"""Summarise results_fix.json against PROTOCOL_FIX.md, with chain/results_chain.json as baseline. Written before results."""
import json, pathlib
from math import comb
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
base = {r["seed"]: r for r in json.loads((HERE / "results_chain.json").read_text())["results"] if r["q"] == 0.85}
fix = json.loads((HERE / "results_fix.json").read_text())["results"]
med = lambda xs: float(np.median(xs))
s1 = lambda r, c="intact": r[c]["dB_staged"] * r["rho1"] / 0.70
s2 = lambda r, c="intact": r[c]["dC_staged"] * r["rho1"] * r["rho2"] / 0.49


def summary(rows, paired_to=None):
    out = {"step_one_median": med([s1(r) for r in rows]), "step_one_right_sign": int(sum(s1(r) > 0 for r in rows)),
           "step_two_median": med([s2(r) for r in rows]), "step_two_right_sign": int(sum(s2(r) > 0 for r in rows)),
           "failing_type_right_sign": int(sum(s2(r) > 0 for r in rows if (r["rho1"], r["rho2"]) == (1, -1))),
           "cut_B_leak_median_signed_to_A": med([r["cut_B"]["dC_staged"] for r in rows]),
           "cut_B_removes_step_two_pct": 1 - med([abs(r["cut_B"]["dC_staged"]) for r in rows]) / max(med([abs(r["intact"]["dC_staged"]) for r in rows]), 1e-12),
           "reverse_B_flips": int(sum(np.sign(r["reverse_B"]["dC_staged"]) == -np.sign(r["intact"]["dC_staged"]) for r in rows)),
           "by_relation_step_two": {"%+d%+d" % (a, b): med([s2(r) for r in rows if (r["rho1"], r["rho2"]) == (a, b)])
                                    for a in (1, -1) for b in (1, -1)}}
    if paired_to is not None:
        up = int(sum(s2(r) > s2(paired_to[r["seed"]]) for r in rows)); n = len(rows)
        out["step_two_higher_than_chain"] = up
        out["sign_test_p_one_sided"] = sum(comb(n, k) for k in range(up, n + 1)) / 2 ** n
        out["rule"] = {"1_step_one_kept": out["step_one_median"] >= 0.5 and out["step_one_right_sign"] >= 14,
                       "2_failing_type_3_of_4": out["failing_type_right_sign"] >= 3,
                       "3_step_two_sign_15_of_16": out["step_two_right_sign"] >= 15,
                       "4_step_two_higher_in_12_of_16": up >= 12}
        out["rule"]["confirmed"] = all(out["rule"].values())
    return out


S = {"chain_baseline": summary(list(base.values()))}
for c in ("damped", "minus_A", "both"):
    S[c] = summary([r for r in fix if r["condition"] == c], base)
(HERE / "summary_fix.json").write_text(json.dumps(S, indent=1) + "\n")
print(json.dumps(S, indent=1))
