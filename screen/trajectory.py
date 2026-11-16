"""Learning trajectories of the screen/ bodies: does the residual learner grow the direct A axon first
and then prune it (a Hebbian-looking childhood, then matching pursuit), or never grow it?

Prediction written before this run (Claude, 16 Nov 2026), from the dynamics: at the start nothing is
explained, so the residue IS the raw target and both rules make the same first steps. The A axon and the
B axon both grow. Once B's axon carries C, the residue left at the tip no longer correlates with A, and
the residual learner's A weight falls back toward zero. The similarity learner's A weight keeps rising
to its correlation value. So: residual A weight rises, peaks within the first 40 episodes, and ends
below half its peak in at least 3 of the 4 bodies. Similarity A weight ends at or near its maximum.

Re-runs the training of the first four primary bodies (same schedules, rule, units; nothing changed)
and records the signed weights after every episode. Output: trajectory.json, trajectory.png.
"""
import json, pathlib, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import engine_screen as S
import run_screen as R

SEEDS = R.SEEDS[:4]


def signed(W, pop, align):
    on = sum(sum(W[k]) for k, u in enumerate(R.U()) if u.pop == pop and u.half == 1)
    off = sum(sum(W[k]) for k, u in enumerate(R.U()) if u.pop == pop and u.half == -1)
    return float((on - off) / 2 * align)


def job(arg):
    seed, mode = arg
    rel = R.RELATIONS[R.SEEDS.index(seed) % 4]
    gap, amp, eps = R.schedule(seed)
    W = [[0.0] * 8 for _ in R.U()]
    tA, tB = [], []
    for sa, k1, k2, onset, g, g2 in eps:
        sb = rel[0] * sa * (1 if k1 else -1); sc = rel[1] * sb * (1 if k2 else -1)
        W = S.run(R.U(), W, R.events(sa, sb, sc, onset, g, g2, amp), R.STEPS, learn=True, rule=R.RULE, mode=mode)["weights"]
        tA.append(signed(W, "A", rel[0] * rel[1])); tB.append(signed(W, "B", rel[1]))
    return {"seed": seed, "rule": mode, "A": tA, "B": tB}


def main():
    jobs = [(s, m) for s in SEEDS for m in R.RULES]
    with ProcessPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(job, jobs))
    verdict = {}
    for r in rows:
        a = np.array(r["A"]); pk = int(np.argmax(a))
        r.update(peak=float(a.max()), peak_episode=pk + 1, final=float(a[-1]))
        verdict.setdefault(r["rule"], []).append(r["final"] < 0.5 * r["peak"] and pk < 40)
    out = {"rows": rows, "residual_rise_then_prune": verdict["residual"], "similarity_rise_then_prune": verdict["similarity"]}
    (HERE / "trajectory.json").write_text(json.dumps(out, indent=1) + "\n")
    for r in rows:
        print(r["seed"], r["rule"], "A peak %.3f at episode %d, final %.3f | B final %.3f" % (r["peak"], r["peak_episode"], r["final"], r["B"][-1]))
    print({k: v for k, v in out.items() if k != "rows"})

    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    for i, m in enumerate(R.RULES):
        for r in rows:
            if r["rule"] == m:
                ax[i].plot(r["B"], color="#2a6f97", lw=1.2, alpha=.8)
                ax[i].plot(r["A"], color="#c8553d", lw=1.6, alpha=.9)
        ax[i].axhline(0, color="#888", lw=.6)
        ax[i].set_title("%s rule" % m); ax[i].set_xlabel("episode")
    ax[0].set_ylabel("signed weight (sum over clocks)")
    ax[0].plot([], [], color="#c8553d", label="direct A axon"); ax[0].plot([], [], color="#2a6f97", label="B route")
    ax[0].legend(frameon=False)
    fig.tight_layout(); fig.savefig(HERE / "trajectory.png", dpi=140)


if __name__ == "__main__":
    main()
