"""Engine for the Gemini follow-up: chain/engine_chain.py with two optional changes (it is NOT modified,
so the first chain receipt stays verifiable).

  pred_damping   velocity damping per substep of the PREDICTION field (world field unchanged at 0.006).
                 Higher = predicted waves stay closer to where they were written and ring less.
  subtract_A     the branches learn to match the world MINUS A's own passive wave, so they predict what
                 comes after A, not A's echo. (The world field itself, and what A-units hear, are unchanged.)
With both at their defaults it reproduces engine_chain.run exactly (checked in run_fix.py --check).
"""
from __future__ import annotations
import pathlib, sys
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import engine as E
import engine_chain as C

N = E.N_SITES


def run(units, W, events, steps, learn=False, rule=None, cut=(), reverse_b=False, pred_damping=None, subtract_A=False):
    rule = rule or {}
    world = C.passive_signed(events, steps)
    target = world
    if subtract_A:
        a_events = [ev for ev in events if ev[0] == C.SITES["A"]]
        target = world - C.passive_signed(a_events, steps)
    wave = dict(E.WAVE)
    if pred_damping is not None:
        wave["damping"] = float(pred_damping)
    pred = E.make("WaveFieldNode", wave)
    us = [E.make("FadingHistorySpikeNode", {"decay": u.decay, "arm_threshold": u.th[0], "release_threshold": u.th[1],
                                            "pulse_amplitude": E.PING_AMP, "refractory": C.REFRACTORY, "enabled": 1}) for u in units]
    gs = [E.make("DampingReturnNode", dict(rule, weights=list(w), learn_enabled=int(learn))) for w in W]
    allowed = [set(u.region) for u in units]
    out_wave, spikes = [], [[] for _ in units]
    for tick in range(steps):
        prev_pred = [pred.get_output("read_%d" % s) for s in range(N)]
        prev_world = world[tick - 1] if tick > 0 else np.zeros(N)
        prev_target = target[tick - 1] if tick > 0 else np.zeros(N)
        prev_pulse = [u.get_output("pulse") for u in us]
        prev_out = [[g.get_output("out_%d" % s) for s in range(N)] for g in gs]
        pred.pre_step()
        for n in us + gs:
            n.pre_step()
        for u, spec in zip(us, units):
            src = prev_world[C.A_READ] if spec.listens == "world" else prev_pred[C.B_READ]
            half = -spec.half if (reverse_b and spec.listens == "prediction") else spec.half
            u.set_input("signal_in", max(0.0, half * float(src)))
        for k, (g, p, o, spec) in enumerate(zip(gs, prev_pulse, prev_out, units)):
            g.set_input("pre_spike", p)
            pop = "A" if spec.listens == "world" else "B"
            for s in range(N):
                ok = s in allowed[k]
                g.set_input("site_%d" % s, float(prev_pred[s] - prev_target[s]) if ok else 0.0)
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
