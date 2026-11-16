"""Summarise the relay batch against relay/PROTOCOL_RELAY.md.  --dev: development bodies, printed only.
All C statistics are fractions of exact Bayes, sign-aligned to the body's relation."""
import json, pathlib, sys
from math import comb
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
med = lambda xs: float(np.median(xs)) if len(xs) else float("nan")


def stats(rows):
    share = [r["open"]["A_given_B"] / r["open"]["B_influence"] if r["open"]["B_influence"] > 0 else float("nan") for r in rows]
    opn = [r["open"]["C_from_A_alone"] / 0.49 for r in rows]
    cn = [r["closed_normalized"]["C_from_A"] / 0.49 for r in rows]
    cg = [r["closed_graded"]["C_from_A"] / 0.49 for r in rows]
    up = int(sum(c > o for c, o in zip(cn, opn))); n = len(rows)
    lag = [med(r["closed_normalized"]["B_clock_lag_vs_seen"]) for r in rows if r["closed_normalized"].get("B_clock_lag_vs_seen")]
    return {"n": n,
            "open_A_share_median": med(share), "open_B_influence_median": med([r["open"]["B_influence"] / 0.70 for r in rows]),
            "open_B_influence_right_sign": int(sum(r["open"]["B_influence"] > 0 for r in rows)),
            "step_one_median": med([r["step_one"] / 0.70 for r in rows]),
            "open_A_alone_C_median": med(opn),
            "closed_normalized_C_median": med(cn), "closed_normalized_C_right_sign": int(sum(c > 0 for c in cn)),
            "closed_graded_C_median": med(cg), "closed_graded_C_right_sign": int(sum(c > 0 for c in cg)),
            "closed_above_open": up, "closed_above_open_p_one_sided": sum(comb(n, k) for k in range(up, n + 1)) / 2 ** n,
            "imagined_B_clock_lag_median_per_body": lag,
            "per_body": [{"seed": r["seed"], "closed_normalized": c, "closed_graded": g, "open_A_alone": o}
                         for r, c, g, o in zip(rows, cn, cg, opn)]}


name = "dev_results_relay.json" if "--dev" in sys.argv else "results_relay.json"
rows = json.loads((HERE / name).read_text())["results"]
S = {m: stats([r for r in rows if r["rule"] == m]) for m in ("residual", "similarity")}
r = S["residual"]
S["rule"] = {"1_screen_holds": abs(r["open_A_share_median"]) <= 0.15 and r["open_B_influence_right_sign"] >= 14,
             "2_no_step_two_without_imagining": r["open_A_alone_C_median"] <= 0.2,
             "3_imagining_restores_step_two": r["closed_normalized_C_right_sign"] >= 14 and r["closed_normalized_C_median"] >= 0.5,
             "4_closed_above_open_14_of_16": r["closed_above_open"] >= 14}
S["rule"]["confirmed"] = all(S["rule"].values())
if "--dev" not in sys.argv:
    (HERE / "summary_relay.json").write_text(json.dumps(S, indent=1) + "\n")
print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk != "per_body"} if isinstance(v, dict) else v) for k, v in S.items()}, indent=1))
