"""Summarise the screening-off test against screen/PROTOCOL_SCREEN.md.
python screen/analyze_screen.py         the batch -> summary_screen.json
python screen/analyze_screen.py --dev   development bodies (printed only)

All three statistics are fractions of the exact (Bayes) value, sign-aligned to the body's relation:
  A_given_B    A's influence on the C prediction when B is present      Bayes: 0
  B_influence  B's influence on the C prediction                         Bayes: 1 (= 0.70)
  A_alone      A's influence on the C prediction when B is absent       Bayes with A only: 1 (= 0.49)
And one scale-free ratio (raw influences, not fractions):
  A_share      A_given_B / B_influence                                   Bayes: 0; one-predictor-at-a-time
               (univariate) fit: about 0.49 / 0.70 = 0.7, less if A's timing jitter blurs its axon
"""
import json, pathlib, sys
from math import comb
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
med = lambda xs: float(np.median(xs)) if len(xs) else float("nan")
AB, BI, AA = (lambda r: r["A_given_B"] / 0.49), (lambda r: r["B_influence"] / 0.70), (lambda r: r["A_alone"] / 0.49)
SH = lambda r: r["A_given_B"] / r["B_influence"] if r["B_influence"] > 0 else float("nan")
TYPES = [(a, b) for a in (1, -1) for b in (1, -1)]


def summary(rows):
    return {"n": len(rows),
            "A_given_B_median": med([AB(r) for r in rows]), "A_given_B_positive": int(sum(AB(r) > 0 for r in rows)),
            "B_influence_median": med([BI(r) for r in rows]), "B_influence_right_sign": int(sum(BI(r) > 0 for r in rows)),
            "A_alone_median": med([AA(r) for r in rows]),
            "A_share_median": med([SH(r) for r in rows]),
            "direct_A_weight_signed_median": med([r["direct_A_weight_signed"] for r in rows]),
            "A_given_B_by_type": {"%+d%+d" % t: med([AB(r) for r in rows if (r["rho1"], r["rho2"]) == t]) for t in TYPES}}


def paired(res, sim):
    by = {r["seed"]: r for r in sim}
    n = len(res)
    smaller = int(sum(abs(SH(r)) < abs(SH(by[r["seed"]])) for r in res))
    return {"residual_A_share_smaller_in_abs": smaller, "of": n,
            "sign_test_p_one_sided": sum(comb(n, k) for k in range(smaller, n + 1)) / 2 ** n}


def rule(S):
    r, s, p = S["residual"], S["similarity"], S["paired"]
    out = {"1_similarity_does_not_screen_off": s["A_given_B_positive"] >= 14,
           "2_residual_share_smaller_14_of_16": p["residual_A_share_smaller_in_abs"] >= 14,
           "3_residual_share_median_at_most_quarter_of_similarity": abs(r["A_share_median"]) <= 0.25 * abs(s["A_share_median"]),
           "4_both_learn_B_to_C": r["B_influence_right_sign"] >= 14 and s["B_influence_right_sign"] >= 14}
    out["confirmed"] = all(out.values())
    return out


name = "dev_results_screen.json" if "--dev" in sys.argv else "results_screen.json"
rows = json.loads((HERE / name).read_text())["results"]
S = {m: summary([r for r in rows if r["rule"] == m]) for m in ("residual", "similarity")}
S["paired"] = paired([r for r in rows if r["rule"] == "residual"], [r for r in rows if r["rule"] == "similarity"])
S["rule"] = rule(S)
if "--dev" not in sys.argv:
    (HERE / "summary_screen.json").write_text(json.dumps(S, indent=1) + "\n")
print(json.dumps(S, indent=1))
