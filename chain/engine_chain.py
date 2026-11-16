"""Engine for the chain experiment: a learned relation, passed two steps through an imagined middle event.

Two wave fields of the same physics (vendored upstream WaveFieldNode, 96x96):
  WORLD       driven only by the stimuli (signed two-frame pulses at A = site 0, B = site 4, C = site 7)
  PREDICTION  driven only by the units' branch outputs: the body's expectation, written with POSITIVE sign

Why two fields: in one shared field (experiment 1 of this repo, StateShapedPingRecall damping) the body
writes ANTI-waves, so a predicted event that arrives leaves silence. A population listening there hears
surprise, not expectation, and cannot relay a prediction onward. Here each branch learns from the
difference PREDICTION - WORLD at its own tip (the same DampingReturnNode rule: flatten what it hears), so
the prediction field converges toward the world, and downstream units can listen to the expectation itself.

Units (vendored FadingHistorySpikeNode, fed a half-wave-rectified input so they are sign selective):
  A-ON / A-OFF   hear the WORLD at aperture 1 (next to A): positive / negative half
  B-ON / B-OFF   hear the PREDICTION at aperture 4 (B's place): positive / negative half
Branches are local by anatomy: A-units may write only to sites 3-5 (around B); B-units only to sites 6-7
(around C). The only route from A to a prediction of C runs through the body's own predicted B.
"""
from __future__ import annotations
import pathlib, sys
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import engine as E

SITES = {"A": 0, "B": 4, "C": 7}
A_READ, B_READ = 1, 4
A_REGION, B_REGION = (3, 4, 5), (6, 7)
REFRACTORY = 120      # each unit fires at most once per episode; otherwise units re-fire on their own ringing
N = E.N_SITES


def passive_signed(events, steps):
    """events: [(site, onset, signed_scale)]; the world field's sensor waves."""
    return E.passive(events, steps)


class Unit:
    def __init__(self, decay, th, listens, half, region):
        self.decay, self.th, self.listens, self.half, self.region = decay, th, listens, half, region


def run(units, W, events, steps, learn=False, rule=None, cut=(), reverse_b=False):
    """events: world stimuli. cut: names of populations whose outputs are silenced ('A', 'B').
    reverse_b: B-ON hears the negative half and B-OFF the positive half (message reversed).
    Returns prediction-field sensor waves, world sensor waves, weights, spikes."""
    rule = rule or {}
    world = passive_signed(events, steps)
    pred = E.make("WaveFieldNode", E.WAVE)
    us = [E.make("FadingHistorySpikeNode", {"decay": u.decay, "arm_threshold": u.th[0], "release_threshold": u.th[1],
                                            "pulse_amplitude": E.PING_AMP, "refractory": REFRACTORY, "enabled": 1}) for u in units]
    gs = [E.make("DampingReturnNode", dict(rule, weights=list(w), learn_enabled=int(learn))) for w in W]
    allowed = [set(u.region) for u in units]
    out_wave, spikes = [], [[] for _ in units]
    for tick in range(steps):
        prev_pred = [pred.get_output("read_%d" % s) for s in range(N)]
        prev_world = world[tick - 1] if tick > 0 else np.zeros(N)
        prev_pulse = [u.get_output("pulse") for u in us]
        prev_out = [[g.get_output("out_%d" % s) for s in range(N)] for g in gs]
        pred.pre_step()
        for n in us + gs:
            n.pre_step()
        for u, spec in zip(us, units):
            src = prev_world[A_READ] if spec.listens == "world" else prev_pred[B_READ]
            half = spec.half
            if reverse_b and spec.listens == "prediction":
                half = -half
            u.set_input("signal_in", max(0.0, half * float(src)))
        for k, (g, p, o, spec) in enumerate(zip(gs, prev_pulse, prev_out, units)):
            g.set_input("pre_spike", p)
            pop = "A" if spec.listens == "world" else "B"
            for s in range(N):
                ok = s in allowed[k]
                g.set_input("site_%d" % s, float(prev_pred[s] - prev_world[s]) if ok else 0.0)
                if ok and o[s] and pop not in cut:
                    pred.set_input("write_%d" % s, o[s])
        pred.step()
        for n in us + gs:
            n.step()
        for k, u in enumerate(us):
            if u.pulse:
                spikes[k].append(tick)
        out_wave.append(pred.read_values.copy())
    weights = [[(w if s in allowed[k] else 0.0) for s, w in enumerate(g.weights)] for k, g in enumerate(gs)]
    return {"prediction": np.asarray(out_wave, dtype=float), "world": world, "weights": weights, "spikes": spikes}
