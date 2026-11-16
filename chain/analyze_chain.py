"""Summarise chain/results_chain.json against PROTOCOL_CHAIN.md. Written before the batch results existed."""
import json, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
D = json.loads((HERE / "results_chain.json").read_text())
prim = [r for r in D["results"] if r["q"] == 0.85]
ctrl = [r for r in D["results"] if r["q"] == 0.5]
med = lambda xs: float(np.median(xs))


def norm(r, cond, step):
    """Signed strength relative to Bayes: 1 = exact Bayes, 0 = nothing, negative = wrong sign."""
    if step == "B":
        return r[cond]["dB_staged"] * r["rho1"] / 0.70
    return r[cond]["dC_staged"] * r["rho1"] * r["rho2"] / 0.49


S = {"bodies": {"primary": len(prim), "control_q05": len(ctrl)}}
for cond in ("intact", "cut_B", "reverse_B", "cut_A"):
    S[cond] = {"step_one_fraction_of_bayes_median": med([norm(r, cond, "B") for r in prim]),
               "step_two_fraction_of_bayes_median": med([norm(r, cond, "C") for r in prim]),
               "step_one_correct_sign": int(sum(norm(r, cond, "B") > 0 for r in prim)),
               "step_two_correct_sign": int(sum(norm(r, cond, "C") > 0 for r in prim)),
               "median_abs_dB": med([abs(r[cond]["dB_staged"]) for r in prim]),
               "median_abs_dC": med([abs(r[cond]["dC_staged"]) for r in prim])}
i, cb = S["intact"], S["cut_B"]
flip = int(sum(np.sign(r["reverse_B"]["dC_staged"]) == -np.sign(r["intact"]["dC_staged"]) and r["intact"]["dC_staged"] != 0 for r in prim))
S["reverse_B_flips_step_two"] = flip
S["cut_B_reduction_of_median_abs_dC"] = 1 - cb["median_abs_dC"] / i["median_abs_dC"] if i["median_abs_dC"] > 0 else None
S["cut_B_change_of_median_abs_dB"] = abs(cb["median_abs_dB"] - i["median_abs_dB"]) / i["median_abs_dB"] if i["median_abs_dB"] > 0 else None
S["attenuation_ratio_median"] = med([(r["intact"]["dC_staged"] * r["rho1"] * r["rho2"]) / (r["intact"]["dB_staged"] * r["rho1"])
                                     for r in prim if r["intact"]["dB_staged"] * r["rho1"] > 0])
S["whole_window_intact"] = {"step_one_fraction_of_bayes_median": med([r["intact"]["dB"] * r["rho1"] / .7 for r in prim]),
                            "step_two_fraction_of_bayes_median": med([r["intact"]["dC"] * r["rho1"] * r["rho2"] / .49 for r in prim]),
                            "step_two_correct_sign": int(sum(r["intact"]["dC"] * r["rho1"] * r["rho2"] > 0 for r in prim))}
S["control_q05"] = {"median_abs_dB": med([abs(r["intact"]["dB_staged"]) for r in ctrl]),
                    "median_abs_dC": med([abs(r["intact"]["dC_staged"]) for r in ctrl])}
S["by_relation"] = {"%+d%+d" % (a, b): {"step_one": med([norm(r, "intact", "B") for r in prim if (r["rho1"], r["rho2"]) == (a, b)]),
                                        "step_two": med([norm(r, "intact", "C") for r in prim if (r["rho1"], r["rho2"]) == (a, b)])}
                    for a in (1, -1) for b in (1, -1)}
S["claim_1"] = {"1_step_one_sign_14_and_half_bayes": i["step_one_correct_sign"] >= 14 and i["step_one_fraction_of_bayes_median"] >= 0.5,
                "2_step_two_sign_13": i["step_two_correct_sign"] >= 13,
                "3_cut_B_removes_70pct_of_step_two_keeps_step_one": (S["cut_B_reduction_of_median_abs_dC"] or 0) >= 0.7 and (S["cut_B_change_of_median_abs_dB"] or 1) < 0.2,
                "4_reverse_B_flips_step_two_in_13": flip >= 13}
S["claim_1"]["shown"] = all(S["claim_1"].values())
S["claim_2_bayes_like"] = {"step_one_at_least_half": i["step_one_fraction_of_bayes_median"] >= 0.5,
                           "step_two_at_least_half": i["step_two_fraction_of_bayes_median"] >= 0.5}
S["claim_2_bayes_like"]["shown"] = all(S["claim_2_bayes_like"].values())
(HERE / "summary_chain.json").write_text(json.dumps(S, indent=1) + "\n")
print(json.dumps(S, indent=1))

fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
cols = {"intact": "#2a6f9b", "cut_B": "#999999", "reverse_B": "#c8562f"}
for k, cond in enumerate(("intact", "cut_B", "reverse_B")):
    ax[0].scatter(np.full(len(prim), k) + np.linspace(-.15, .15, len(prim)), [norm(r, cond, "B") for r in prim], color=cols[cond], s=22)
    ax[1].scatter(np.full(len(prim), k) + np.linspace(-.15, .15, len(prim)), [norm(r, cond, "C") for r in prim], color=cols[cond], s=22)
for a, title in zip(ax, ("Step one: A → expected B", "Step two: imagined B → expected C")):
    a.axhline(1, color="#2a6f9b", ls="--", lw=.8); a.axhline(0, color="#999", lw=.8)
    a.text(2.35, 1.0, "exact Bayes", va="center", fontsize=8, color="#2a6f9b")
    a.set_xticks([0, 1, 2]); a.set_xticklabels(["intact", "B-units cut", "B message reversed"])
    a.set_ylabel("strength, fraction of exact Bayes (sign-corrected)"); a.set_title(title)
    a.spines[["top", "right"]].set_visible(False); a.set_xlim(-.5, 2.9)
fig.tight_layout(); fig.savefig(HERE / "chain.png", dpi=150)
