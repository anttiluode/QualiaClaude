"""Relay follow-up: regenerative imagined B (see relay/PROTOCOL_REGEN.md). Readout only: uses the trained
bodies stored in results_relay.json; nothing is retrained.

  python relay/run_regen.py --check   one development body: B-unit clocks under a regenerated B vs a seen B
  python relay/run_regen.py           all 32 trained bodies (16 residual, 16 similarity)
"""
import argparse, hashlib, json, pathlib, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import engine_relay as L
import engine_regen as G
import run_relay as R


def readout(r):
    W, gap, r1, r2 = r["weights"], r["gap"], r["rho1"], r["rho2"]
    g2 = gap + R.GAP2_EXTRA
    b0, c0 = R.PROBE_ONSET + gap, R.PROBE_ONSET + gap + g2
    seen = L.run(R.U(), W, R.events(1, r1, 0, R.PROBE_ONSET, gap, g2), R.STEPS)["spikes"]
    bk = [k for k, u in enumerate(R.U()) if u.pop == "B" and u.half == r1]
    scale = max(0.0, r["step_one"])              # |beta_B| for the probe sign; 0 if the body imagines the wrong sign
    out = {"ping_scale": scale}
    for name, ps in (("regen", 1.0), ("regen_amp", scale)):
        cc = {}
        for sa in (1, -1):
            q = G.run(R.U(), W, R.events(sa, 0, 0, R.PROBE_ONSET, gap, g2), R.STEPS, gain=r["gain"], ping_scale=ps)
            cc[sa] = R.proj(q["prediction"], "C", c0, 40)
            if sa == 1:
                on = q["regen_onset"]
                out[name + "_onset_error"] = None if on is None else on - b0
                out[name + "_sign_right"] = bool(q["regen_sign"] == r1)
                out[name + "_clock_lag_vs_seen"] = [q["spikes"][k][0] - seen[k][0] for k in bk if q["spikes"][k] and seen[k]]
                out[name + "_clock_shape_lag"] = ([(q["spikes"][k][0] - on) - (seen[k][0] - b0) for k in bk if q["spikes"][k] and seen[k]]
                                                  if on is not None else [])
        out[name + "_C"] = float((cc[1] - cc[-1]) / 2 * r1 * r2)
    return {"seed": r["seed"], "rule": r["rule"], "rho1": r1, "rho2": r2, "normalized_C": r["closed_normalized"]["C_from_A"],
            "normalized_lag": r["closed_normalized"].get("B_clock_lag_vs_seen"), **out}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--check", action="store_true"); a = ap.parse_args()
    if a.check:
        r = json.loads((HERE / "dev_results_relay.json").read_text())["results"][0]
        res = readout(r)
        print({k: v for k, v in res.items()})
        return
    rows = json.loads((HERE / "results_relay.json").read_text())["results"]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=2) as pool:
        out = list(pool.map(readout, rows))
    receipt = {"label": "relay follow-up: regenerative imagined B (readout of the trained relay bodies)", "cross": G.CROSS,
               "results": out, "elapsed_seconds": time.time() - t0,
               "protocol_sha256": hashlib.sha256((HERE / "PROTOCOL_REGEN.md").read_bytes()).hexdigest(),
               "runner_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
               "engine_sha256": hashlib.sha256((HERE / "engine_regen.py").read_bytes()).hexdigest(),
               "bodies_sha256": hashlib.sha256((HERE / "results_relay.json").read_bytes()).hexdigest()}
    (HERE / "results_regen.json").write_text(json.dumps(receipt, indent=1))
    print("done %.0fs" % (time.time() - t0))


if __name__ == "__main__":
    main()
