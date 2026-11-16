"""Clock follow-up to the chain: does protecting the A-units' clocks from B's own wave fix step two?
See chain/CLOCK.md (the finding) and chain/PROTOCOL_LATCH.md (the decision rule).

  python chain/run_latch.py --check         engine_latch with options off == engine_chain
  python chain/run_latch.py --dev           development bodies only (seeds 991-993, every relation type)
  python chain/run_latch.py                 the pre-registered batch (16 primary bodies x 2 conditions)
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import engine_chain as C
import engine_latch as L
import run_chain as R

CONDITIONS = {"latch_matched": {"latch": True, "units": "matched"}, "latch": {"latch": True}}
DEV_CONDITIONS = ("none", "latch", "residue", "latch_matched")


def matched_units():
    """Latched A-units with the SAME firing time as the unlatched ones when A (+1, amplitude 1) comes alone:
    each A-unit's release level is set to its latched trace at the tick the unlatched unit fires. So at test
    the clocks are unchanged; only their resetting by later events is removed. B-units are unchanged."""
    import copy
    base = R.U(); W0 = [[0.0] * 8 for _ in base]
    ev = R.events(1, 0, 0, 20, 30, 50, a_only=True)
    t_base = L.run(base, W0, ev, R.STEPS)["spikes"]
    out = [copy.copy(u) for u in base]
    for k, u in enumerate(base):
        if u.listens != "world":
            continue
        tr = trace_latched(u, R.events(u.half, 0, 0, 20, 30, 50, a_only=True))
        t = L.run(base, W0, R.events(u.half, 0, 0, 20, 30, 50, a_only=True), R.STEPS)["spikes"][k][0]
        out[k].th = (u.th[0], float(tr[t]))
    return out


def trace_latched(u, ev):
    """The latched trace of one A-unit (input closed once armed and falling), with release disabled."""
    import engine as E
    world = C.passive_signed(ev, R.STEPS)
    n = E.make("FadingHistorySpikeNode", {"decay": u.decay, "arm_threshold": u.th[0], "release_threshold": -1.0,
                                          "pulse_amplitude": E.PING_AMP, "refractory": C.REFRACTORY, "enabled": 1})
    closed, last, tr = False, 0.0, []
    for tick in range(R.STEPS):
        x = max(0.0, u.half * float(world[tick - 1][C.A_READ])) if tick > 0 else 0.0
        n.pre_step(); n.set_input("signal_in", 0.0 if closed else x); n.step()
        if n.armed and n.trace < last:
            closed = True
        last = n.trace; tr.append(n.trace)
    return tr


MATCHED = None
def units_for(opts):
    global MATCHED
    if opts.get("units") == "matched":
        if MATCHED is None:
            MATCHED = matched_units()
        return MATCHED
    return R.U()


def eng(opts):
    return {k: v for k, v in opts.items() if k != "units"}
SEEDS = R.SEEDS


def train(seed, rel, opts):
    gap, amp, eps = R.schedule(seed, R.Q)
    UU = units_for(opts)
    W = [[0.0] * 8 for _ in UU]
    shifts = []
    for n, (sa, k1, k2, onset, g, g2) in enumerate(eps):
        sb = rel[0] * sa * (1 if k1 else -1); sc = rel[1] * sb * (1 if k2 else -1)
        r = L.run(UU, W, R.events(sa, sb, sc, onset, g, g2, amp), R.STEPS, learn=True, rule=R.RULE, **eng(opts))
        if n == len(eps) - 1:
            last = (sa, onset, g, amp, r["spikes"], W)
        W = r["weights"]
    return gap, W, last


def clock_shift(last, opts):
    """Firing time of each world-listening unit in the last training episode minus its firing time when the
    same A comes alone (same weights, same onset). 0 = the clock was not moved by what came after A."""
    sa, onset, g, amp, spikes, W = last
    UU = units_for(opts)
    alone = L.run(UU, W, R.events(sa, 0, 0, onset, g, g + R.GAP2_EXTRA, amp, a_only=True), R.STEPS, **eng(opts))["spikes"]
    out = []
    for k, u in enumerate(UU):
        if u.listens == "world" and u.half == sa and spikes[k] and alone[k]:
            out.append(int(spikes[k][0] - alone[k][0]))
    return out


def read(W, gap, opts, **kw):
    T, win = R.templates(gap)
    out = {}
    for sa in (1, -1):
        r = L.run(units_for(opts), W, R.events(sa, 0, 0, R.PROBE_ONSET, gap, gap + R.GAP2_EXTRA, a_only=True), R.STEPS, **eng(opts), **kw)
        out["A%+d" % sa] = R.fit(r["prediction"], T, win)
        out["A%+d" % sa].update(R.fit_staged(r["prediction"], T, gap))
    for k, key in (("dB", "bB"), ("dC", "bC"), ("dB_staged", "sB"), ("dC_staged", "sC")):
        out[k] = (out["A+1"][key] - out["A-1"][key]) / 2
    return out


def job(arg):
    seed, rel, name = arg
    opts = dict(CONDITIONS, residue={"residue": True}).get(name, {})
    gap, W, last = train(seed, rel, opts)
    return {"seed": seed, "condition": name, "rho1": rel[0], "rho2": rel[1], "gap": gap, "weights": W,
            "clock_shift_last_episode": clock_shift(last, opts),
            "intact": read(W, gap, opts), "cut_B": read(W, gap, opts, cut=("B",)), "reverse_B": read(W, gap, opts, reverse_b=True)}


def check():
    W = [[0.01 * ((i + s) % 5 - 2) for s in range(8)] for i in range(len(R.U()))]
    ev = R.events(1, 1, -1, 20, 30, 50)
    a = C.run(R.U(), W, ev, 200, learn=True, rule=R.RULE); b = L.run(R.U(), W, ev, 200, learn=True, rule=R.RULE)
    d = max(float(np.abs(a["prediction"] - b["prediction"]).max()), float(np.abs(np.array(a["weights"]) - np.array(b["weights"])).max()))
    print("max difference engine_latch vs engine_chain:", d); assert d == 0.0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--check", action="store_true"); ap.add_argument("--dev", action="store_true")
    ap.add_argument("--only", default=None, help="dev: run only this condition")
    a = ap.parse_args()
    if a.check:
        return check()
    t0 = time.time()
    if a.dev:
        conds = [a.only] if a.only else DEV_CONDITIONS
        jobs = [(s, rel, c) for s in R.DEV_SEEDS for rel in R.RELATIONS for c in conds]
        out = HERE / ("dev_results_latch_%s.json" % a.only if a.only else "dev_results_latch.json")
        label = "clock follow-up: development bodies"
    else:
        jobs = [(s, R.RELATIONS[R.SEEDS.index(s) % 4], c) for c in CONDITIONS for s in SEEDS]
        out, label = HERE / "results_latch.json", "clock follow-up: pre-registered batch"
    receipt = {"label": label, "conditions": CONDITIONS, "results": [],
               "runner_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
               "engine_sha256": hashlib.sha256((HERE / "engine_latch.py").read_bytes()).hexdigest()}
    if not a.dev:
        receipt["protocol_sha256"] = hashlib.sha256((HERE / "PROTOCOL_LATCH.md").read_bytes()).hexdigest()
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for n, rec in enumerate(pool.map(job, jobs), 1):
            receipt["results"].append(rec); receipt["elapsed_seconds"] = time.time() - t0
            out.write_text(json.dumps(receipt, indent=1))
            print("%d/%d %.0fs" % (n, len(jobs), time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
