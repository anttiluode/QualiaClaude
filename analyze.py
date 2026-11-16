"""Summarise results.json against PROTOCOL.md. Written before the batch results existed."""
import json, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parent
D = json.loads((ROOT / "results.json").read_text()); rows = D["results"]
cond = lambda c: sorted([r for r in rows if r["condition"] == c], key=lambda r: r["seed"])
inf, uni, abo = cond("informative"), cond("uninformative"), cond("a_bank_only")
med = lambda xs: float(np.median(xs))


def boot(d):
    d = np.asarray(d, dtype=float)
    b = d[np.random.default_rng(890).integers(0, len(d), (20000, len(d)))].mean(axis=1)
    lo, hi = np.quantile(b, [.025, .975])
    return {"mean": float(d.mean()), "ci95": [float(lo), float(hi)]}


def coherent(r):
    n, t1, t2 = r["read"]["none"], r["read"]["tone1"], r["read"]["tone2"]
    return t1["bB"] > n["bB"] and t1["bC"] < n["bC"] and t2["bC"] > n["bC"] and t2["bB"] < n["bB"]


def expect(rs, cue):
    return {"bB": med([r["read"][cue]["bB"] for r in rs]), "bC": med([r["read"][cue]["bC"] for r in rs]),
            "explained": med([r["read"][cue]["explained"] for r in rs])}


R_inf = [r["read"]["revision_index"] for r in inf]
R_uni = [r["read"]["revision_index"] for r in uni]
assert [r["seed"] for r in inf] == [r["seed"] for r in uni]
S = {
    "bodies": {"informative": len(inf), "uninformative": len(uni), "a_bank_only": len(abo)},
    "expectation": {c: {cue: expect(rs, cue) for cue in (("none", "tone1", "tone2") if c != "a_bank_only" else ("none",))}
                    for c, rs in (("informative", inf), ("uninformative", uni), ("a_bank_only", abo))},
    "revision_index": {"informative_median": med(R_inf), "informative_above_zero": int(sum(x > 0 for x in R_inf)),
                       "uninformative_median": med(R_uni),
                       "informative_minus_uninformative": boot(np.array(R_inf) - np.array(R_uni))},
    "coherent_bodies_informative": int(sum(coherent(r) for r in inf)),
    "coherent_bodies_uninformative": int(sum(coherent(r) for r in uni)),
    "swap_reverses_sign_informative": int(sum(np.sign(r["read_banks_swapped"]["revision_index"]) == -np.sign(r["read"]["revision_index"])
                                              and r["read"]["revision_index"] != 0 for r in inf)),
    "tone_banks_alone_informative": {cue: {"bB": med([r["read_a_bank_silenced"][cue]["bB"] for r in inf]),
                                           "bC": med([r["read_a_bank_silenced"][cue]["bC"] for r in inf])} for cue in ("tone1", "tone2")},
    "surprise_informative": {k: med([r["surprise"][k] for r in inf]) for k in inf[0]["surprise"]},
    "surprise_uninformative": {k: med([r["surprise"][k] for r in uni]) for k in uni[0]["surprise"]},
    "surprise_a_bank_only": {k: med([r["surprise"][k] for r in abo]) for k in abo[0]["surprise"]},
    "clipped_frames": int(sum(r["training_clipped_frames"] for r in rows)
                          + sum(r["read"][c]["clipped"] for r in rows for c in r["read"] if isinstance(r["read"][c], dict))),
}
# meaning by removal: median contribution of each tone unit (by firing delay), per bank, informative bodies
delays = list(range(16, 61, 4))
S["meaning_by_removal_informative"] = {
    tone: [{"fires_after_tone": dl, "d_bB": med([m["d_bB"] for r in inf for m in r["meaning_by_removal"] if m["tone"] == tone and abs(m["decay"] - dec) < 1e-9]),
            "d_bC": med([m["d_bC"] for r in inf for m in r["meaning_by_removal"] if m["tone"] == tone and abs(m["decay"] - dec) < 1e-9])}
           for dl, dec in zip(delays, D["tone_decays"])] for tone in ("tone1", "tone2")}
S["decision_rule"] = {
    "1_median_R_at_least_0.5_and_R_above_zero_in_14": S["revision_index"]["informative_median"] >= 0.5 and S["revision_index"]["informative_above_zero"] >= 14,
    "2_coherent_in_14_of_16": S["coherent_bodies_informative"] >= 14,
    "3_beats_uninformative_ci_excludes_zero": S["revision_index"]["informative_minus_uninformative"]["ci95"][0] > 0,
    "4_swap_reverses_sign_in_14": S["swap_reverses_sign_informative"] >= 14}
S["decision_rule"]["shown"] = all(S["decision_rule"].values())
(ROOT / "summary.json").write_text(json.dumps(S, indent=1) + "\n")
print(json.dumps({k: v for k, v in S.items() if k != "meaning_by_removal_informative"}, indent=1))

# figure
fig, ax = plt.subplots(1, 3, figsize=(15, 4.6))
cols = {"none": "#7a8a99", "tone1": "#2a6f9b", "tone2": "#c8562f"}
for c, rs, k in (("informative", inf, 0), ("uninformative", uni, 1)):
    for cue in ("none", "tone1", "tone2"):
        ax[k].scatter([r["read"][cue]["bB"] for r in rs], [r["read"][cue]["bC"] for r in rs], s=28, color=cols[cue],
                      label={"none": "A alone", "tone1": "A + tone 1", "tone2": "A + tone 2"}[cue])
    ax[k].plot([0, 1], [0, 0], color="#bbb", lw=.8); ax[k].plot([0, 0], [0, 1], color="#bbb", lw=.8)
    ax[k].set_xlabel("expects B (β_B)"); ax[k].set_ylabel("expects C (β_C)")
    ax[k].set_title("%s tone during training" % c.capitalize()); ax[k].legend(frameon=False, fontsize=8)
    ax[k].set_xlim(-.3, 1.1); ax[k].set_ylim(-.3, 1.1)
m = S["meaning_by_removal_informative"]["tone1"]
ax[2].bar(np.array(delays) - 1, [x["d_bB"] for x in m], width=1.8, color="#2a6f9b", label="adds to 'B expected'")
ax[2].bar(np.array(delays) + 1, [x["d_bC"] for x in m], width=1.8, color="#c8562f", label="adds to 'C expected'")
ax[2].axhline(0, color="#999", lw=.8); ax[2].set_xlabel("tone-1 unit: fires this many frames after the tone")
ax[2].set_ylabel("contribution (removal)"); ax[2].set_title("What each tone-1 unit means"); ax[2].legend(frameon=False, fontsize=8)
for a in ax:
    a.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(ROOT / "shared_prediction.png", dpi=150)
