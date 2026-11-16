"""Engine for the clock follow-up: chain/engine_chain.py with two optional changes to what the A-units hear
(engine_chain.py is NOT modified, so the earlier receipts stay verifiable).

The finding this tests (chain/CLOCK.md): A-units hear the WORLD at aperture 1. When B has A's sign, B's own
wave reaches aperture 1 and re-charges the same-sign A-units' fading traces, so in training the slow A-units
fire about 33 frames later than they do at test, where A comes alone. Their branches learn on one clock and
are used on another.

  latch    once an A-unit's trace has armed and started to fall, its input is closed until it fires:
           a clock, once started, cannot be reset by what comes after.
  residue  A-units hear WORLD - PREDICTION at aperture 1: what the body already expects is subtracted
           before it reaches them (the apical/basal picture: predicted input does not re-drive the unit).
With both off it reproduces engine_chain.run exactly (checked in run_latch.py --check).
"""
from __future__ import annotations
import pathlib, sys
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import engine as E
import engine_chain as C

N = E.N_SITES


def run(units, W, events, steps, learn=False, rule=None, cut=(), reverse_b=False, latch=False, residue=False):
    rule = rule or {}
    world = C.passive_signed(events, steps)
    pred = E.make("WaveFieldNode", E.WAVE)
    us = [E.make("FadingHistorySpikeNode", {"decay": u.decay, "arm_threshold": u.th[0], "release_threshold": u.th[1],
                                            "pulse_amplitude": E.PING_AMP, "refractory": C.REFRACTORY, "enabled": 1}) for u in units]
    gs = [E.make("DampingReturnNode", dict(rule, weights=list(w), learn_enabled=int(learn))) for w in W]
    allowed = [set(u.region) for u in units]
    closed = [False] * len(units)
    last_trace = [0.0] * len(units)
    out_wave, spikes = [], [[] for _ in units]
    for tick in range(steps):
        prev_pred = [pred.get_output("read_%d" % s) for s in range(N)]
        prev_world = world[tick - 1] if tick > 0 else np.zeros(N)
        prev_pulse = [u.get_output("pulse") for u in us]
        prev_out = [[g.get_output("out_%d" % s) for s in range(N)] for g in gs]
        pred.pre_step()
        for n in us + gs:
            n.pre_step()
        for k, (u, spec) in enumerate(zip(us, units)):
            if spec.listens == "world":
                src = prev_world[C.A_READ] - (prev_pred[C.A_READ] if residue else 0.0)
                x = max(0.0, spec.half * float(src))
                if latch and closed[k]:
                    x = 0.0
            else:
                half = -spec.half if reverse_b else spec.half
                x = max(0.0, half * float(prev_pred[C.B_READ]))
            u.set_input("signal_in", x)
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
                closed[k] = False
            elif u.armed and u.trace < last_trace[k]:
                closed[k] = True
            last_trace[k] = u.trace
        out_wave.append(pred.read_values.copy())
    weights = [[(w if s in allowed[k] else 0.0) for s, w in enumerate(g.weights)] for k, g in enumerate(gs)]
    return {"prediction": np.asarray(out_wave, dtype=float), "world": world, "weights": weights, "spikes": spikes}
