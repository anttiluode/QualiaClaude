"""Summarise the clock follow-up against chain/PROTOCOL_LATCH.md, with chain/results_chain.json as baseline.
python chain/analyze_latch.py         the pre-registered batch -> summary_latch.json
python chain/analyze_latch.py --dev   the development bodies (printed only)"""
import json, pathlib, sys
from math import comb
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
med = lambda xs: float(np.median(xs)) if len(xs) else float("nan")
s1 = lambda r, c="intact": r[c]["dB_staged"] * r["rho1"] / 0.70
s2 = lambda r, c="intact": r[c]["dC_staged"] * r["rho1"] * r["rho2"] / 0.49
TYPES = [(a, b) for a in (1, -1) for b in (1, -1)]
key = lambda t: "%+d%+d" % t


def moved(r):
    if "clock_shift_last_episode" not in r:
        return None                      # not recorded for chain/ bodies; see clock_diag.json for those
    return sum(abs(s) >= 10 for s in r["clock_shift_last_episode"])


def summary(rows, base=None):
    out = {"n": len(rows),
           "step_one_median": med([s1(r) for r in rows]), "step_one_right_sign": int(sum(s1(r) > 0 for r in rows)),
           "step_two_median": med([s2(r) for r in rows]), "step_two_right_sign": int(sum(s2(r) > 0 for r in rows)),
           "by_relation_step_two": {key(t): med([s2(r) for r in rows if (r["rho1"], r["rho2"]) == t]) for t in TYPES},
           "by_relation_right_sign": {key(t): int(sum(s2(r) > 0 for r in rows if (r["rho1"], r["rho2"]) == t)) for t in TYPES},
           "rho1_plus_step_two_median": med([s2(r) for r in rows if r["rho1"] == 1]),
           "rho1_minus_step_two_median": med([s2(r) for r in rows if r["rho1"] == -1]),
           "A_units_moved_10plus_last_episode_rho1_plus": [moved(r) for r in rows if r["rho1"] == 1],
           "cut_B_removes_step_two_pct": 1 - med([abs(r["cut_B"]["dC_staged"]) for r in rows]) / max(med([abs(r["intact"]["dC_staged"]) for r in rows]), 1e-12),
           "reverse_B_flips": int(sum(np.sign(r["reverse_B"]["dC_staged"]) == -np.sign(r["intact"]["dC_staged"]) for r in rows))}
    if base is not None:
        plus = [r for r in rows if r["rho1"] == 1]
        up = int(sum(s2(r) > s2(base[r["seed"]]) for r in plus)); n = len(plus)
        out["rho1_plus_step_two_higher_than_chain"] = up
        out["rho1_plus_sign_test_p_one_sided"] = sum(comb(n, k) for k in range(up, n + 1)) / 2 ** n
        out["rule"] = {
            "1_clock_fixed": all(m is not None and m <= 1 for m in out["A_units_moved_10plus_last_episode_rho1_plus"]),
            "2_step_one_kept": out["step_one_median"] >= 0.5 and out["step_one_right_sign"] >= 14,
            "3_failing_type_3_of_4": out["by_relation_right_sign"]["+1-1"] >= 3,
            "4_rho1_plus_higher_7_of_8": up >= 7,
            "5_step_two_sign_15_of_16": out["step_two_right_sign"] >= 15}
        out["rule"]["confirmed"] = all(out["rule"].values())
    return out


if "--dev" in sys.argv:
    rows = json.loads((HERE / "dev_results_latch.json").read_text())["results"]
    extra = HERE / "dev_results_latch_latch_matched.json"
    if extra.exists():
        rows += json.loads(extra.read_text())["results"]
    for c in ("none", "latch", "residue", "latch_matched"):
        print(c, json.dumps(summary([r for r in rows if r["condition"] == c]), indent=1))
else:
    base = {r["seed"]: r for r in json.loads((HERE / "results_chain.json").read_text())["results"] if r["q"] == 0.85}
    rows = json.loads((HERE / "results_latch.json").read_text())["results"]
    S = {"chain_baseline": summary(list(base.values()))}
    for c in ("latch", "residue"):
        S[c] = summary([r for r in rows if r["condition"] == c], base)
    (HERE / "summary_latch.json").write_text(json.dumps(S, indent=1) + "\n")
    print(json.dumps(S, indent=1))
