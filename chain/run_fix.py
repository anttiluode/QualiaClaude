"""Gemini's follow-up to the chain: does damping the prediction field, or removing A's own spillover from
what the branches learn to predict, fix step two? See chain/PROTOCOL_FIX.md."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import engine_chain as C
import engine_fix as F
import run_chain as R

PRED_DAMPING = 0.03                         # 5x the world's 0.006; chosen before any run (see protocol)
CONDITIONS = {"damped": {"pred_damping": PRED_DAMPING}, "minus_A": {"subtract_A": True},
              "both": {"pred_damping": PRED_DAMPING, "subtract_A": True}}
SEEDS = R.SEEDS                             # the same 16 primary bodies (same schedules, same relations)


def train(seed, opts):
    rel = R.RELATIONS[R.SEEDS.index(seed) % 4]
    gap, amp, eps = R.schedule(seed, R.Q)
    W = [[0.0] * 8 for _ in R.U()]
    for sa, k1, k2, onset, g, g2 in eps:
        sb = rel[0] * sa * (1 if k1 else -1); sc = rel[1] * sb * (1 if k2 else -1)
        W = F.run(R.U(), W, R.events(sa, sb, sc, onset, g, g2, amp), R.STEPS, learn=True, rule=R.RULE, **opts)["weights"]
    return rel, gap, W


def read(W, gap, opts, **kw):
    T, win = R.templates(gap)
    out = {}
    for sa in (1, -1):
        r = F.run(R.U(), W, R.events(sa, 0, 0, R.PROBE_ONSET, gap, gap + R.GAP2_EXTRA, a_only=True), R.STEPS,
                  pred_damping=opts.get("pred_damping"), **kw)
        out["A%+d" % sa] = R.fit(r["prediction"], T, win)
        out["A%+d" % sa].update(R.fit_staged(r["prediction"], T, gap))
    for k, key in (("dB", "bB"), ("dC", "bC"), ("dB_staged", "sB"), ("dC_staged", "sC")):
        out[k] = (out["A+1"][key] - out["A-1"][key]) / 2
    return out


def job(arg):
    seed, name = arg
    opts = CONDITIONS[name]
    rel, gap, W = train(seed, opts)
    return {"seed": seed, "condition": name, "rho1": rel[0], "rho2": rel[1], "gap": gap, "weights": W,
            "intact": read(W, gap, opts), "cut_B": read(W, gap, opts, cut=("B",)), "reverse_B": read(W, gap, opts, reverse_b=True)}


def check():
    """With default options engine_fix must reproduce engine_chain exactly."""
    W = [[0.01 * ((i + s) % 5 - 2) for s in range(8)] for i in range(len(R.U()))]
    ev = R.events(1, 1, -1, 20, 30, 50)
    a = C.run(R.U(), W, ev, 200, learn=True, rule=R.RULE); b = F.run(R.U(), W, ev, 200, learn=True, rule=R.RULE)
    d = max(float(np.abs(a["prediction"] - b["prediction"]).max()), float(np.abs(np.array(a["weights"]) - np.array(b["weights"])).max()))
    print("max difference engine_fix vs engine_chain:", d); assert d == 0.0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=2); ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        return check()
    t0 = time.time()
    jobs = [(s, c) for c in CONDITIONS for s in SEEDS]
    receipt = {"label": "chain follow-up: Gemini's fixes", "conditions": CONDITIONS, "seeds": SEEDS, "results": [],
               "protocol_sha256": hashlib.sha256((HERE / "PROTOCOL_FIX.md").read_bytes()).hexdigest(),
               "runner_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
               "engine_sha256": hashlib.sha256((HERE / "engine_fix.py").read_bytes()).hexdigest()}
    out = HERE / "results_fix.json"
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for n, rec in enumerate(pool.map(job, jobs), 1):
            receipt["results"].append(rec); receipt["elapsed_seconds"] = time.time() - t0
            out.write_text(json.dumps(receipt, indent=1))
            print("%d/%d %.0fs" % (n, len(jobs), time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
