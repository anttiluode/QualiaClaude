"""Summarise innovation results against innovation/PROTOCOL_INNOV.md.  --dev prints development bodies."""
import json, pathlib, sys
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
med = lambda xs: float(np.median(xs)) if len(xs) else float("nan")


def boot(x, seed=890):
    rng = np.random.default_rng(seed); x = np.asarray(x)
    b = [np.median(rng.choice(x, len(x))) for _ in range(20000)]
    return [float(v) for v in np.percentile(b, [2.5, 97.5])]


def innov(rows):
    cl = [r["closed_frac"] for r in rows]
    return {"n": len(rows), "closed_frac_median": med(cl), "closed_frac_95": boot(cl) if len(cl) > 2 else None,
            "closed_right_sign": int(sum(c > 0 for c in cl)), "closed_C_median": med([r["closed_C"] for r in rows]),
            "consistent_C_frac_median": med([r["consistent_C_frac"] for r in rows]),
            "contradict_C_frac_median": med([r["contradict_C_frac"] for r in rows]),
            "contradict_follows_B": int(sum(r["contradict_C_frac"] > 0 for r in rows)),
            "B_spikes_consistent_median": med([np.mean([v["right"] for v in r["consistent_B_spikes"].values()]) for r in rows]),
            "B_spikes_contradict_median": med([np.mean([v["right"] for v in r["contradict_B_spikes"].values()]) for r in rows]),
            "wrong_sign_B_spikes_median": med([np.mean([v["wrong"] for k in ("consistent_B_spikes", "contradict_B_spikes") for v in r[k].values()]) for r in rows]),
            "residue_peak_consistent_median": med([r["consistent_residue_peak"] for r in rows]),
            "residue_peak_contradict_median": med([r["contradict_residue_peak"] for r in rows])}


if "--dev" in sys.argv:
    rows = json.loads((HERE / "dev_results_innov.json").read_text())["results"]
    for arm in (0.8, 0.4):
        print("arm", arm, json.dumps(innov([r for r in rows if r["b_arm"] == arm]), indent=1))
    sys.exit()

rows = json.loads((HERE / "results_innov.json").read_text())["results"]
i85 = [r for r in rows if r["body"] == "innovation" and r["q1"] == 0.85]
i70 = [r for r in rows if r["body"] == "innovation" and r["q1"] == 0.70]
g70 = [r for r in rows if r["body"] == "relay_regen"]
S = {"innovation_q85": innov(i85), "innovation_q70": innov(i70),
     "relay_regen_q70": {"n": len(g70), "closed_frac_median": med([r["closed_frac"] for r in g70]),
                         "closed_frac_95": boot([r["closed_frac"] for r in g70]),
                         "closed_right_sign": int(sum(r["closed_frac"] > 0 for r in g70)), "closed_C_median": med([r["closed_C"] for r in g70])}}
ratio = S["innovation_q70"]["closed_C_median"] / S["innovation_q85"]["closed_C_median"]
S["innovation_C_ratio_q70_over_q85"] = ratio
by70 = {r["seed"]: r for r in g70}
closer = int(sum(abs(np.log(max(r["closed_frac"], 1e-6))) < abs(np.log(max(by70[r["seed"]]["closed_frac"], 1e-6))) for r in i70))
S["innovation_closer_to_bayes_than_regen_q70"] = closer
S["rule"] = {"1_calibrated_eyes_closed_q85": 0.75 <= S["innovation_q85"]["closed_frac_median"] <= 1.25 and S["innovation_q85"]["closed_right_sign"] >= 14,
             "2_tracks_reliability": 0.4 <= ratio <= 0.8 and S["innovation_q70"]["closed_right_sign"] >= 14,
             "3_closer_than_regen_q70_12_of_16": closer >= 12,
             "4_contradiction_flips_C_14_of_16": S["innovation_q85"]["contradict_follows_B"] >= 14}
S["rule"]["confirmed"] = all(S["rule"].values())
(HERE / "summary_innov.json").write_text(json.dumps(S, indent=1) + "\n")
print(json.dumps(S, indent=1))
