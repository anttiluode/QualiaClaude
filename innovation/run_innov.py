"""Innovation experiment (see innovation/PROTOCOL_INNOV.md).

  python innovation/run_innov.py --dev      development bodies (seeds 981-983), B-unit arm 0.8 and 0.4
  python innovation/run_innov.py            the batch: innovation at q1 = 0.85 and 0.70, relay+regen at q1 = 0.70
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "relay")); sys.path.insert(0, str(HERE))
import engine as E
import engine_relay as L
import engine_regen as G
import engine_innov as I
import run_relay as R                       # units (same calibration file), events, projection, rule

Q2 = 0.85
B_ARM = 0.8                                  # chosen on development bodies (0.8 vs 0.4), see protocol
SEEDS = {0.85: list(range(190001, 190017)), 0.70: list(range(190101, 190117))}
DEV_SEEDS = [981, 982, 983]


def schedule(seed, q1):
    rng = np.random.default_rng(seed)
    gap = int(rng.integers(28, 43)); amp = float(rng.uniform(.9, 1.12))
    sa = np.array([1] * (R.EPISODES // 2) + [-1] * (R.EPISODES // 2)); rng.shuffle(sa)
    eps = []
    for a in sa:
        k1, k2 = rng.random() < q1, rng.random() < Q2
        onset = 20 + int(rng.integers(-5, 6)); g = gap + int(rng.integers(-3, 4))
        eps.append((int(a), bool(k1), bool(k2), onset, g, gap + R.GAP2_EXTRA))
    return gap, amp, eps


def train(seed, q1, rel, body, b_arm):
    gap, amp, eps = schedule(seed, q1)
    W = [[0.0] * 8 for _ in R.U()]
    for sa, k1, k2, onset, g, g2 in eps:
        sb = rel[0] * sa * (1 if k1 else -1); sc = rel[1] * sb * (1 if k2 else -1)
        ev = R.events(sa, sb, sc, onset, g, g2, amp)
        if body == "innovation":
            W = I.run(R.U(), W, ev, R.STEPS, learn=True, rule=R.RULE, b_arm=b_arm)["weights"]
        else:
            W = L.run(R.U(), W, ev, R.STEPS, learn=True, rule=R.RULE, mode="residual")["weights"]
    return gap, W


def b_spikes(r, half):
    return int(sum(1 for k, u in enumerate(R.U()) if u.pop == "B" and u.half == half and r["spikes"][k]))


def read_innov(W, gap, rel, q1, b_arm):
    r1, r2 = rel
    g2 = gap + R.GAP2_EXTRA; c0 = R.PROBE_ONSET + gap + g2; b0 = R.PROBE_ONSET + gap
    bayes_closed = (2 * q1 - 1) * (2 * Q2 - 1)
    out = {"bayes_closed": bayes_closed}
    cc = {}
    for sa in (1, -1):
        cc[sa] = R.proj(I.run(R.U(), W, R.events(sa, 0, 0, R.PROBE_ONSET, gap, g2), R.STEPS, eyes="closed", b_arm=b_arm)["prediction"], "C", c0, 40)
    out["closed_C"] = float((cc[1] - cc[-1]) / 2 * r1 * r2)
    out["closed_frac"] = out["closed_C"] / bayes_closed
    for name, flip in (("consistent", 1), ("contradict", -1)):
        c = {}; sp = {}; rp = {}
        for sa in (1, -1):
            sb = flip * r1 * sa
            q = I.run(R.U(), W, R.events(sa, sb, 0, R.PROBE_ONSET, gap, g2), R.STEPS, b_arm=b_arm)
            c[sa] = R.proj(q["prediction"], "C", c0, 40)
            sp[sa] = {"right": b_spikes(q, sb), "wrong": b_spikes(q, -sb)}
            rp[sa] = float(np.max(np.abs(q["residue"][b0:b0 + 30])))
        # C aligned with what the real B says about C (r2 * sB), as a fraction of 2q2-1
        out[name + "_C_frac"] = float((c[1] - c[-1]) / 2 * flip * r1 * r2 / (2 * Q2 - 1))
        out[name + "_B_spikes"] = sp; out[name + "_residue_peak"] = float(np.mean(list(rp.values())))
    return out


def read_regen(W, gap, rel, q1):
    """relay/ body at the same reliability, read eyes closed with the regenerated imagined B (relay/PROTOCOL_REGEN.md)."""
    r1, r2 = rel
    g2 = gap + R.GAP2_EXTRA; b0 = R.PROBE_ONSET + gap; c0 = b0 + g2
    pk = []
    for sa in (1, -1):
        r = L.run(R.U(), W, R.events(sa, 0, 0, R.PROBE_ONSET, gap, g2), R.STEPS, cut=("B",))
        pk.append(float(np.max(np.abs(r["prediction"][b0 - 5:b0 + 30, L.READ["B"]]))))
    real_peak = float(np.max(np.abs(E.passive([(L.SITES["B"], b0, 1.0)], R.STEPS)[:, L.READ["B"]])))
    gain = real_peak / max(np.mean(pk), 1e-9)
    cc = {}
    for sa in (1, -1):
        cc[sa] = R.proj(G.run(R.U(), W, R.events(sa, 0, 0, R.PROBE_ONSET, gap, g2), R.STEPS, gain=gain)["prediction"], "C", c0, 40)
    bayes_closed = (2 * q1 - 1) * (2 * Q2 - 1)
    C = float((cc[1] - cc[-1]) / 2 * r1 * r2)
    return {"bayes_closed": bayes_closed, "gain": gain, "closed_C": C, "closed_frac": C / bayes_closed}


def job(arg):
    seed, q1, rel, body, b_arm = arg
    gap, W = train(seed, q1, rel, body, b_arm)
    rd = read_innov(W, gap, rel, q1, b_arm) if body == "innovation" else read_regen(W, gap, rel, q1)
    return {"seed": seed, "q1": q1, "body": body, "b_arm": b_arm, "rho1": rel[0], "rho2": rel[1], "gap": gap, "weights": W, **rd}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=2); ap.add_argument("--dev", action="store_true")
    a = ap.parse_args(); t0 = time.time(); R.U()
    if a.dev:
        jobs = [(s, 0.85, (1, 1), "innovation", arm) for s in DEV_SEEDS for arm in (0.8, 0.4)]
        out, label = HERE / "dev_results_innov.json", "innovation: development bodies (not evidence)"
    else:
        jobs = ([(s, q, R.RELATIONS[i % 4], "innovation", B_ARM) for q in (0.85, 0.70) for i, s in enumerate(SEEDS[q])]
                + [(s, 0.70, R.RELATIONS[i % 4], "relay_regen", None) for i, s in enumerate(SEEDS[0.70])])
        out, label = HERE / "results_innov.json", "innovation: pre-registered batch"
    receipt = {"label": label, "q2": Q2, "b_arm": B_ARM, "results": [],
               "runner_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
               "engine_sha256": hashlib.sha256((HERE / "engine_innov.py").read_bytes()).hexdigest()}
    if not a.dev:
        receipt["protocol_sha256"] = hashlib.sha256((HERE / "PROTOCOL_INNOV.md").read_bytes()).hexdigest()
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for n, rec in enumerate(pool.map(job, jobs), 1):
            receipt["results"].append(rec); receipt["elapsed_seconds"] = time.time() - t0
            out.write_text(json.dumps(receipt, indent=1))
            print("%d/%d %.0fs" % (n, len(jobs), time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
