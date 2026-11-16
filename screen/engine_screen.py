"""Screening-off test: does a branch learn to explain what is LEFT, or to explain the world on its own?

One wave world (vendored WaveFieldNode, same physics as chain/): signed pulses A at site 0, B at site 4,
C at site 7. One prediction field driven only by the units' branch outputs.

Units (vendored FadingHistorySpikeNode, half-wave rectified input, so sign selective; latched: once a
trace has armed and begun to fall, its input is closed until it fires, so no later event resets a clock):
  A-ON / A-OFF   hear A's own wave at aperture 0 (A's site)
  B-ON / B-OFF   hear B's own wave at aperture 4 (B's site); here B is REAL, not imagined
Each population has its own receptor: it hears only its own stimulus's wave. In the shared world field
A's wave at aperture 4 overlaps B's arrival, and no arm threshold separated right-sign from wrong-sign
B-units (development check, disclosed in PROTOCOL_SCREEN.md). Only C's tip is shared.
Every branch, A's and B's, may write only at sites 6-7 (C's place). So C's tip gets two candidate inputs:
a direct axon from A, and one from B. The world is a Markov chain A -> B -> C, so given B, A carries no
further information about C. Exact answer: E[sC | sA, sB] = (2q-1) rho2 sB; the direct A weight is ZERO.

Both rules use the same DampingReturnNode (same rate, window, clip). They differ ONLY in what a branch
hears at its tip during its listening window:
  residual   the shared prediction minus C's wave: P - C.  Each branch explains what the others leave.
  similarity its OWN contribution minus C's wave: P_k - C. Each branch explains C by itself; its fixed
             point is the univariate (delay-aware correlation) weight E[C after my spike] / self_response.
P_k is computed exactly from a measured kernel (the field is linear); checked in run_screen.py --check.
The target is C's own wave (A's and B's waves passing through sites 6-7 are not part of what is predicted).
"""
from __future__ import annotations
import pathlib, sys
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import engine as E

SITES = {"A": 0, "B": 4, "C": 7}
READ = {"A": 0, "B": 4}
REGION = (6, 7)
REFRACTORY = 300
N = E.N_SITES
K_LEN = 12          # lags kept in the kernel; the listening window uses lags 4-6


class Unit:
    def __init__(self, decay, th, pop, half):
        self.decay, self.th, self.pop, self.half = decay, th, pop, half


_KERNEL = None
def kernel():
    """K[s_write][j][s_read]: prediction-field read at s_read, j steps after a unit write at s_write."""
    global _KERNEL
    if _KERNEL is None:
        K = np.zeros((N, K_LEN, N))
        for sw in REGION:
            f = E.make("WaveFieldNode", E.WAVE)
            for j in range(K_LEN):
                f.pre_step()
                if j == 0:
                    f.set_input("write_%d" % sw, 1.0)
                f.step(); K[sw, j] = f.read_values
        _KERNEL = K
    return _KERNEL


def run(units, W, events, steps, learn=False, rule=None, mode="residual", latch=True, record=False):
    rule = rule or {}
    world = E.passive(events, steps)
    target = E.passive([ev for ev in events if ev[0] == SITES["C"]], steps)
    sensor = {pop: E.passive([ev for ev in events if ev[0] == SITES[pop]], steps)[:, READ[pop]] for pop in ("A", "B")}
    K = kernel()
    pred = E.make("WaveFieldNode", E.WAVE)
    us = [E.make("FadingHistorySpikeNode", {"decay": u.decay, "arm_threshold": u.th[0], "release_threshold": u.th[1],
                                            "pulse_amplitude": E.PING_AMP, "refractory": REFRACTORY, "enabled": 1}) for u in units]
    gs = [E.make("DampingReturnNode", dict(rule, weights=list(w), learn_enabled=int(learn))) for w in W]
    closed = [False] * len(units); last = [0.0] * len(units)
    fire_tick = [None] * len(units); fire_w = [None] * len(units)
    out_wave, spikes, heard = [], [[] for _ in units], []
    for tick in range(steps):
        prev_pred = np.array([pred.get_output("read_%d" % s) for s in range(N)])
        prev_world = world[tick - 1] if tick > 0 else np.zeros(N)
        prev_target = target[tick - 1] if tick > 0 else np.zeros(N)
        prev_pulse = [u.get_output("pulse") for u in us]
        prev_out = [[g.get_output("out_%d" % s) for s in range(N)] for g in gs]
        pred.pre_step()
        for n in us + gs:
            n.pre_step()
        for k, (u, spec) in enumerate(zip(us, units)):
            x = max(0.0, spec.half * float(sensor[spec.pop][tick - 1])) if tick > 0 else 0.0
            u.set_input("signal_in", 0.0 if (latch and closed[k]) else x)
        for k, (g, p, o) in enumerate(zip(gs, prev_pulse, prev_out)):
            g.set_input("pre_spike", p)
            if mode == "residual":
                tip = prev_pred
            else:                                   # similarity: this branch's own contribution only
                tip = np.zeros(N)
                if fire_tick[k] is not None:
                    j = tick - fire_tick[k] - 3
                    if 0 <= j < K_LEN:
                        tip = E.PING_AMP * sum(fire_w[k][sw] * K[sw, j] for sw in REGION)
            for s in range(N):
                ok = s in REGION
                g.set_input("site_%d" % s, float(tip[s] - prev_target[s]) if ok else 0.0)
                if ok and o[s]:
                    pred.set_input("write_%d" % s, o[s])
            if record and k == 0:
                heard.append((float(tip[6]), float(prev_pred[6])))
        pred.step()
        for n in us + gs:
            n.step()
        for k, u in enumerate(us):
            if u.pulse:
                spikes[k].append(tick); closed[k] = False
                fire_tick[k] = tick; fire_w[k] = list(gs[k].weights)
            elif u.armed and u.trace < last[k]:
                closed[k] = True
            last[k] = u.trace
        out_wave.append(pred.read_values.copy())
    weights = [[(w if s in REGION else 0.0) for s, w in enumerate(g.weights)] for g in gs]
    res = {"prediction": np.asarray(out_wave, dtype=float), "world": world, "target": target, "weights": weights, "spikes": spikes}
    if record:
        res["heard"] = heard
    return res
