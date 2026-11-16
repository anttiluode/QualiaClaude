"""Chain experiment: does a wave body learn two relations and pass a clue two steps, the way exact Bayes would?
See chain/PROTOCOL_CHAIN.md for the decision rule.

World per episode: sA = +-1 (balanced). sB = rho1*sA with probability q, else -rho1*sA.
sC = rho2*sB with probability q, else -rho2*sB. Signed pulses: A at site 0, B at site 4 (gap g = 28..42), C at site 7 (a further g + 20 frames: a
fade-triggered unit cannot fire until its input has stopped ringing, about 32 frames).
Each body has its own (rho1, rho2); it is never told them.
Exact Bayes, given A's sign:  E[sB] = (2q-1)*rho1*sA,   E[sC] = (2q-1)^2*rho1*rho2*sA.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import engine as E
import engine_chain as C

RULE = {"learning_rate": 0.03, "listen_from": 3, "listen_to": 5, "self_response": 0.71, "max_weight": 2.0, "sign": 1.0}
A_DECAYS = E.A_DECAYS[::2]                  # 12 fade rates; fire 27-72 frames after A
B_DECAYS = [0.82, 0.8305, 0.8409, 0.8514, 0.8618, 0.8723, 0.8827, 0.8932, 0.9036, 0.9141, 0.9245, 0.935]   # spread over the band that fires 35-70 frames after an imagined B
A_ARM, B_ARM = (0.80, 0.20), (0.15, 0.0375)  # B-units hear an imagined, weaker B
GAP2_EXTRA = 20
EPISODES, STEPS, PROBE_ONSET = 80, 340, 23
RELATIONS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
SEEDS = list(range(160001, 160017))         # primary, q = 0.85; relation = RELATIONS[i % 4]
CONTROL_SEEDS = list(range(160101, 160109))  # q = 0.5: no relation to learn
DEV_SEEDS = [991, 992, 993]
Q = 0.85


def units():
    wa = E.passive([(C.SITES["A"], 20, 1.0)], 300)[:, C.A_READ]
    wb = E.passive([(C.SITES["B"], 20, 1.0)], 300)[:, C.B_READ]
    out = []
    for listens, w, (arm, rel), region, decays in (("world", wa, A_ARM, C.A_REGION, A_DECAYS),
                                                   ("prediction", wb, B_ARM, C.B_REGION, B_DECAYS)):
        for half in (1, -1):
            for d in decays:
                p = E.peak_trace(d, np.maximum(w, 0))          # calibrated on the positive half of a +pulse
                out.append(C.Unit(d, (arm * p, rel * p), listens, half, region))
    return out


UNITS = None
def U():
    global UNITS
    if UNITS is None:
        UNITS = units()
    return UNITS


def schedule(seed, q):
    rng = np.random.default_rng(seed)
    gap = int(rng.integers(28, 43)); amp = float(rng.uniform(.9, 1.12))
    sa = np.array([1] * (EPISODES // 2) + [-1] * (EPISODES // 2)); rng.shuffle(sa)
    eps = []
    for a in sa:
        keep1, keep2 = rng.random() < q, rng.random() < q
        onset = 20 + int(rng.integers(-5, 6)); g = gap + int(rng.integers(-3, 4))
        _ = int(rng.integers(-3, 4))           # drawn and discarded: C keeps B's jitter relative to A (+-3), not double
        g2 = gap + GAP2_EXTRA
        eps.append((int(a), bool(keep1), bool(keep2), onset, g, g2))
    return gap, amp, eps


def events(sa, sb, sc, onset, g, g2, amp=1.0, a_only=False):
    ev = [(C.SITES["A"], onset, amp * sa)]
    if not a_only:
        ev += [(C.SITES["B"], onset + g, amp * sb), (C.SITES["C"], onset + g + g2, amp * sc)]
    return ev


def train(seed, q, rel):
    r1, r2 = rel
    gap, amp, eps = schedule(seed, q)
    W = [[0.0] * 8 for _ in U()]
    for sa, k1, k2, onset, g, g2 in eps:
        sb = r1 * sa * (1 if k1 else -1); sc = r2 * sb * (1 if k2 else -1)
        W = C.run(U(), W, events(sa, sb, sc, onset, g, g2, amp), STEPS, learn=True, rule=RULE)["weights"]
    return gap, W


def templates(gap):
    g2 = gap + GAP2_EXTRA
    T = {k: E.passive([(C.SITES[k], PROBE_ONSET + off, 1.0)], STEPS) for k, off in (("A", 0), ("B", gap), ("C", gap + g2))}
    return T, (PROBE_ONSET + 2, PROBE_ONSET + gap + g2 + 100)


def fit(P, T, win):
    a, b = win
    X = np.stack([T[k][a:b].ravel() for k in ("A", "B", "C")], axis=1)
    y = P[a:b].ravel()
    coef = np.linalg.lstsq(X, y, rcond=None)[0]
    expl = 1 - float(((X @ coef - y) ** 2).sum()) / max(float((y ** 2).sum()), 1e-18)
    return {"bA": float(coef[0]), "bB": float(coef[1]), "bC": float(coef[2]), "explained": expl}


def fit_staged(P, T, gap):
    """B from B's own window (B onset .. C onset), against A and B templates; then C from a 40-frame window
    starting at C's onset, on what A and B do not explain. Avoids B and C templates trading off."""
    b0, c0 = PROBE_ONSET + gap, PROBE_ONSET + gap + gap + GAP2_EXTRA
    X = np.stack([T[k][b0:c0].ravel() for k in ("A", "B")], axis=1)
    cA, cB = np.linalg.lstsq(X, P[b0:c0].ravel(), rcond=None)[0]
    rest = P[c0:c0 + 40] - cA * T["A"][c0:c0 + 40] - cB * T["B"][c0:c0 + 40]
    tc = T["C"][c0:c0 + 40].ravel()
    cC = float(rest.ravel() @ tc / (tc @ tc))
    return {"sB": float(cB), "sC": cC}


def read(W, gap, **kw):
    T, win = templates(gap)
    out = {}
    for sa in (1, -1):
        r = C.run(U(), W, events(sa, 0, 0, PROBE_ONSET, gap, gap + GAP2_EXTRA, a_only=True), STEPS, **kw)
        out["A%+d" % sa] = fit(r["prediction"], T, win)
        out["A%+d" % sa].update(fit_staged(r["prediction"], T, gap))
        out["A%+d" % sa]["b_units_fired"] = int(sum(len(s) > 0 for s, u in zip(r["spikes"], U()) if u.listens == "prediction"))
    out["dB"] = (out["A+1"]["bB"] - out["A-1"]["bB"]) / 2
    out["dC"] = (out["A+1"]["bC"] - out["A-1"]["bC"]) / 2
    out["dB_staged"] = (out["A+1"]["sB"] - out["A-1"]["sB"]) / 2
    out["dC_staged"] = (out["A+1"]["sC"] - out["A-1"]["sC"]) / 2
    return out


def job(arg):
    seed, q = arg
    idx = (SEEDS + CONTROL_SEEDS + DEV_SEEDS).index(seed)
    rel = RELATIONS[idx % 4]
    gap, W = train(seed, q, rel)
    bayes = {"dB": (2 * q - 1) * rel[0], "dC": (2 * q - 1) ** 2 * rel[0] * rel[1]}
    return {"seed": seed, "q": q, "rho1": rel[0], "rho2": rel[1], "gap": gap, "bayes": bayes, "weights": W,
            "intact": read(W, gap), "cut_B": read(W, gap, cut=("B",)), "cut_A": read(W, gap, cut=("A",)),
            "reverse_B": read(W, gap, reverse_b=True)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=2); ap.add_argument("--dev", action="store_true")
    a = ap.parse_args(); t0 = time.time()
    jobs = [(s, Q) for s in DEV_SEEDS] if a.dev else [(s, Q) for s in SEEDS] + [(s, 0.5) for s in CONTROL_SEEDS]
    receipt = {"label": "development run (not evidence)" if a.dev else "chain batch", "q": Q, "rule": RULE,
               "a_decays": A_DECAYS, "b_decays": B_DECAYS, "gap2_extra": GAP2_EXTRA, "a_arm": A_ARM, "b_arm": B_ARM, "episodes": EPISODES, "results": [],
               "protocol_sha256": hashlib.sha256((HERE / "PROTOCOL_CHAIN.md").read_bytes()).hexdigest() if (HERE / "PROTOCOL_CHAIN.md").exists() else None,
               "runner_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
               "engine_sha256": hashlib.sha256((HERE / "engine_chain.py").read_bytes()).hexdigest()}
    out = HERE / ("dev_results_chain.json" if a.dev else "results_chain.json")
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for n, rec in enumerate(pool.map(job, jobs), 1):
            receipt["results"].append(rec); receipt["elapsed_seconds"] = time.time() - t0
            out.write_text(json.dumps(receipt, indent=1))
            print("%d/%d %.0fs" % (n, len(jobs), time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
