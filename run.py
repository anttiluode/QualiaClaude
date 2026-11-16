"""Shared prediction: can one piece of evidence on a second sense revise a population's expectation
coherently, at places it never senses? See PROTOCOL.md for the design and the decision rule.

Two hidden worlds:  world B = A then B (site 7);  world C = A then C (site 4); same gap.
A alone cannot tell them apart. Two frames after A, a tone arrives on a separate line.
Conditions (the body is trained on 40 episodes, worlds balanced 20/20, all fast state wiped between):
  informative     tone 1 in world B, tone 2 in world C
  uninformative   tone 1 or tone 2 drawn independently of the world (balanced 20/20)
  a_bank_only     no tone banks at all
Test (growth frozen, full wipe), second event omitted: A alone; A + tone 1; A + tone 2.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import engine as E

RULE = {"learning_rate": 0.03, "listen_from": 3, "listen_to": 5, "self_response": 0.71, "max_weight": 2.0, "sign": 1.0}
TONE_DECAYS = [0.8745, 0.9045, 0.923, 0.9355, 0.9445, 0.951, 0.9565, 0.961, 0.9645, 0.9675, 0.97, 0.972]
EPISODES, STEPS, PROBE_ONSET, TONE_LAG = 40, 300, 23, 2
SEEDS = list(range(150001, 150017))      # fresh; development used 991-993
DEV_SEEDS = [991, 992, 993]
CONDITIONS = ("informative", "uninformative", "a_bank_only")


def make_body(with_tones=True):
    calA = E.passive([(E.SITES["A"], 20, 1.0)], 200)[:, E.A_READ]
    calT = E.tone_line(0, 200)
    units = [(d, E.thresholds(d, calA), ("wave", E.A_READ)) for d in E.A_DECAYS]
    if with_tones:
        for k in (1, 2):
            units += [(d, E.thresholds(d, calT), ("tone", k)) for d in TONE_DECAYS]
    return E.Body(units)


BODY = {True: None, False: None}
def body(with_tones):
    if BODY[with_tones] is None:
        BODY[with_tones] = make_body(with_tones)
    return BODY[with_tones]


def banks(n_units):
    a = list(range(len(E.A_DECAYS)))
    if n_units == len(a):
        return a, [], []
    t1 = list(range(len(a), len(a) + len(TONE_DECAYS)))
    return a, t1, list(range(t1[-1] + 1, t1[-1] + 1 + len(TONE_DECAYS)))


def schedule(seed, condition):
    rng = np.random.default_rng(seed)
    gap = int(rng.integers(28, 43)); amp = float(rng.uniform(.9, 1.12))
    worlds = np.array(["B"] * (EPISODES // 2) + ["C"] * (EPISODES // 2)); rng.shuffle(worlds)
    tones = np.array([1] * (EPISODES // 2) + [2] * (EPISODES // 2)); rng.shuffle(tones)
    eps = []
    for w, t in zip(worlds, tones):
        onset = 20 + int(rng.integers(-5, 6)); g = gap + int(rng.integers(-3, 4))
        tone = {"informative": 1 if w == "B" else 2, "uninformative": int(t), "a_bank_only": None}[condition]
        eps.append((str(w), onset, g, tone))
    return gap, amp, eps


def stim(world, onset, gap, amp=1.0, omit_second=False):
    s = [(E.SITES["A"], onset, amp)]
    if not omit_second:
        s.append((E.SITES[world], onset + gap, amp))
    return s


def tones_for(tone, onset):
    return {k: (onset + TONE_LAG if tone == k else None) for k in (1, 2)}


def train(seed, condition):
    gap, amp, eps = schedule(seed, condition)
    bd = body(condition != "a_bank_only")
    W = [[0.0] * 8 for _ in bd.units]; clip = 0
    for world, onset, g, tone in eps:
        r = E.run(bd, W, stim(world, onset, g, amp), tones_for(tone, onset), STEPS, learn=True, rule=RULE)
        W, clip = r["weights"], clip + r["clipped"]
    return gap, W, clip


def targets(gap):
    base = E.passive(stim("B", PROBE_ONSET, gap, omit_second=True), STEPS)
    TB = E.passive(stim("B", PROBE_ONSET, gap), STEPS) - base
    TC = E.passive(stim("C", PROBE_ONSET, gap), STEPS) - base
    a, b = PROBE_ONSET + gap + 2, PROBE_ONSET + gap + 100
    return base, TB, TC, (a, b)


def beta(p, TB, TC, win):
    """Least-squares fit p = -bB*TB - bC*TC over the window; also the fraction of p it explains."""
    a, b = win
    X = np.stack([-TB[a:b].ravel(), -TC[a:b].ravel()], axis=1)
    y = p[a:b].ravel()
    coef = np.linalg.lstsq(X, y, rcond=None)[0]
    explained = 1 - float(((X @ coef - y) ** 2).sum()) / max(float((y ** 2).sum()), 1e-18)
    return {"bB": float(coef[0]), "bC": float(coef[1]), "explained": explained}


def read_body(W, gap, with_tones=True):
    """The body's prediction under each cue, with the second event omitted."""
    bd = body(with_tones)
    base, TB, TC, win = targets(gap)
    out = {}
    for name, tone in (("none", None), ("tone1", 1), ("tone2", 2)):
        if tone is not None and not with_tones:
            continue
        r = E.run(bd, W, stim("B", PROBE_ONSET, gap, omit_second=True), tones_for(tone, PROBE_ONSET), STEPS)
        out[name] = beta(r["wave"] - base, TB, TC, win)
        out[name]["clipped"] = r["clipped"]
    if with_tones:
        out["revision_index"] = (out["tone1"]["bB"] - out["tone2"]["bB"]) + (out["tone2"]["bC"] - out["tone1"]["bC"])
    return out


def surprise(W, gap, world, tone, with_tones=True):
    """Energy left in the window when the world arrives with this tone, relative to an untrained body."""
    base, TB, TC, (a, b) = targets(gap)
    T = TB if world == "B" else TC
    r = E.run(body(with_tones), W, stim(world, PROBE_ONSET, gap), tones_for(tone, PROBE_ONSET), STEPS)
    return float(((r["wave"] - base)[a:b] ** 2).sum()) / float((T[a:b] ** 2).sum())


def job(arg):
    seed, condition = arg
    with_tones = condition != "a_bank_only"
    gap, W, clip = train(seed, condition)
    rec = {"seed": seed, "condition": condition, "gap": gap, "training_clipped_frames": clip, "weights": W}
    rec["read"] = read_body(W, gap, with_tones)
    if with_tones:
        a, t1, t2 = banks(len(W))
        Ws = [list(w) for w in W]
        for i, j in zip(t1, t2):
            Ws[i], Ws[j] = W[j], W[i]
        rec["read_banks_swapped"] = read_body(Ws, gap, True)
        Wa0 = [([0.0] * 8 if i in a else list(w)) for i, w in enumerate(W)]
        rec["read_a_bank_silenced"] = read_body(Wa0, gap, True)
        # meaning by removal: each tone unit's own contribution under its own tone
        meaning = []
        for bank, tone in ((t1, "tone1"), (t2, "tone2")):
            full = rec["read"][tone]
            for i in bank:
                Wr = [([0.0] * 8 if k == i else list(w)) for k, w in enumerate(W)]
                rr = read_body(Wr, gap, True)[tone]
                meaning.append({"unit": i, "tone": tone, "decay": TONE_DECAYS[(i - bank[0])],
                                "d_bB": full["bB"] - rr["bB"], "d_bC": full["bC"] - rr["bC"]})
        rec["meaning_by_removal"] = meaning
        rec["surprise"] = {"B_with_tone1": surprise(W, gap, "B", 1), "B_with_tone2": surprise(W, gap, "B", 2),
                           "C_with_tone2": surprise(W, gap, "C", 2), "C_with_tone1": surprise(W, gap, "C", 1),
                           "B_no_tone": surprise(W, gap, "B", None), "C_no_tone": surprise(W, gap, "C", None)}
    else:
        rec["surprise"] = {"B_no_tone": surprise(W, gap, "B", None, False), "C_no_tone": surprise(W, gap, "C", None, False)}
    return rec


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=2); ap.add_argument("--dev", action="store_true")
    a = ap.parse_args(); t0 = time.time()
    seeds = DEV_SEEDS if a.dev else SEEDS
    jobs = [(s, c) for c in CONDITIONS for s in seeds]
    receipt = {"label": "development run (not evidence)" if a.dev else "QualiaClaude shared-prediction batch",
               "rule": RULE, "a_decays": E.A_DECAYS, "tone_decays": TONE_DECAYS, "episodes": EPISODES, "seeds": seeds,
               "results": [],
               "protocol_sha256": hashlib.sha256((ROOT / "PROTOCOL.md").read_bytes()).hexdigest() if (ROOT / "PROTOCOL.md").exists() else None,
               "runner_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
               "engine_sha256": hashlib.sha256((ROOT / "engine.py").read_bytes()).hexdigest()}
    out = ROOT / ("dev_results.json" if a.dev else "results.json")
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for n, rec in enumerate(pool.map(job, jobs), 1):
            receipt["results"].append(rec); receipt["elapsed_seconds"] = time.time() - t0
            out.write_text(json.dumps(receipt, indent=1))
            print("%d/%d  %.0fs" % (n, len(jobs), time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
