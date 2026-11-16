"""Summarise results_regen.json against PROTOCOL_REGEN.md -> summary_regen.json. C as a fraction of Bayes (0.49)."""
import json, pathlib
from math import comb
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
d = json.loads((HERE / "results_regen.json").read_text())


def summ(rows, rule):
    f = lambda x: x / 0.49
    n = len(rows)
    shape = [float(np.median(np.abs(r["regen_clock_shape_lag"]))) if r["regen_clock_shape_lag"] else 99.0 for r in rows]
    rg = [f(r["regen_C"]) for r in rows]; ra = [f(r["regen_amp_C"]) for r in rows]; nm = [f(r["normalized_C"]) for r in rows]
    up = int(sum(a > b for a, b in zip(rg, nm)))
    better = int(sum((a > 0 and b > 0 and abs(np.log(b)) < abs(np.log(a))) or (a <= 0 < b) for a, b in zip(rg, ra)))
    S = {"n": n, "clock_shape_ok": int(sum(s <= 1 for s in shape)), "onset_error": [r["regen_onset_error"] for r in rows],
         "regen_sign_right": int(sum(r["regen_sign_right"] for r in rows)),
         "normalized_C_median": float(np.median(nm)), "regen_C_median": float(np.median(rg)), "regen_C_right_sign": int(sum(x > 0 for x in rg)),
         "regen_amp_C_median": float(np.median(ra)), "regen_amp_C_right_sign": int(sum(x > 0 for x in ra)),
         "regen_above_normalized": up, "p_one_sided": sum(comb(n, k) for k in range(up, n + 1)) / 2 ** n,
         "amp_better_calibrated": better, "ping_scale_median": float(np.median([r["ping_scale"] for r in rows])),
         "per_body": [{"seed": r["seed"], "normalized": a, "regen": b, "regen_amp": c} for r, a, b, c in zip(rows, nm, rg, ra)]}
    rng = np.random.default_rng(890)
    for key, x in (("regen", rg), ("regen_amp", ra)):
        bs = [np.median(rng.choice(np.array(x), n)) for _ in range(20000)]
        S[key + "_C_median_95"] = [float(v) for v in np.percentile(bs, [2.5, 97.5])]
    if rule:
        S["rule"] = {"1_clocks_match": S["clock_shape_ok"] >= 14, "2_regen_beats_normalized": up >= 14,
                     "3_median_half_and_sign": S["regen_C_median"] >= 0.5 and S["regen_C_right_sign"] >= 14,
                     "4_amp_better_12": better >= 12}
        S["rule"] = {k: bool(v) for k, v in S["rule"].items()}
        S["rule"]["confirmed"] = all(S["rule"].values())
    return S


out = {"residual": summ([r for r in d["results"] if r["rule"] == "residual"], True),
       "similarity": summ([r for r in d["results"] if r["rule"] == "similarity"], False)}
(HERE / "summary_regen.json").write_text(json.dumps(out, indent=1) + "\n")
for k, v in out.items():
    print(k, json.dumps({kk: vv for kk, vv in v.items() if kk != "per_body"}, indent=1))
