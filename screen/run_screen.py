"""Screening-off test (see screen/PROTOCOL_SCREEN.md). Same bodies, two learning rules: residual vs similarity.

  python screen/run_screen.py --check      kernel check: computed own contribution == field, one unit
  python screen/run_screen.py --dev        development bodies (seeds 981-983, every relation type)
  python screen/run_screen.py              the pre-registered batch: 16 bodies x 2 rules
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import engine as E
import engine_screen as S

RULE = {"learning_rate": 0.03, "listen_from": 3, "listen_to": 5, "self_response": 0.71, "max_weight": 2.0, "sign": 1.0}
Q = 0.85
EPISODES, STEPS, PROBE_ONSET, GAP2_EXTRA = 240, 240, 23, 20
RELATIONS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
SEEDS = list(range(170001, 170017))
DEV_SEEDS = [981, 982, 983]
RULES = ("residual", "similarity")
A_FIRE = np.linspace(66, 122, 12)     # latched firing times after A (C arrives 76-104 after A)
B_FIRE = np.linspace(40, 78, 12)      # latched firing times after B (C arrives 48-62 after B)
ARM, REL = 0.80, 0.20


def latched_fire_time(decay, pop):
    """First firing tick, relative to the stimulus onset, of one latched unit hearing its own stimulus alone."""
    onset = 20
    w = E.passive([(S.SITES[pop], onset, 1.0)], 300)[:, S.READ[pop]]
    p = E.peak_trace(decay, np.maximum(w, 0))
    u = S.Unit(decay, (ARM * p, REL * p), pop, 1)
    sp = S.run([u], [[0.0] * 8], [(S.SITES[pop], onset, 1.0)], 300)["spikes"][0]
    return (sp[0] - onset) if sp else None, (ARM * p, REL * p)


def calibrate(target, pop):
    lo, hi = 0.70, 0.995
    for _ in range(26):
        mid = (lo + hi) / 2
        t, _ = latched_fire_time(mid, pop)
        if t is None or t > target:
            hi = mid
        else:
            lo = mid
    t, th = latched_fire_time(lo, pop)
    return lo, th, t


_U = None
CAL_FILE = HERE / "units_screen.json"
def U():
    """Units, calibrated once (bisection on the fade rate) and cached in units_screen.json."""
    global _U
    if _U is None:
        if CAL_FILE.exists():
            cal = {p: [(d, tuple(th), t) for d, th, t in rows] for p, rows in json.loads(CAL_FILE.read_text()).items()}
        else:
            cal = {"A": [calibrate(t, "A") for t in A_FIRE], "B": [calibrate(t, "B") for t in B_FIRE]}
            CAL_FILE.write_text(json.dumps({p: [[d, list(th), t] for d, th, t in rows] for p, rows in cal.items()}, indent=1))
        _U = [S.Unit(d, th, pop, half) for pop in ("A", "B") for half in (1, -1) for d, th, _ in cal[pop]]
        U.cal = cal
    return _U


def schedule(seed):
    rng = np.random.default_rng(seed)
    gap = int(rng.integers(28, 43)); amp = float(rng.uniform(.9, 1.12))
    sa = np.array([1] * (EPISODES // 2) + [-1] * (EPISODES // 2)); rng.shuffle(sa)
    eps = []
    for a in sa:
        k1, k2 = rng.random() < Q, rng.random() < Q
        onset = 20 + int(rng.integers(-5, 6)); g = gap + int(rng.integers(-3, 4))
        eps.append((int(a), bool(k1), bool(k2), onset, g, gap + GAP2_EXTRA))
    return gap, amp, eps


def events(sa, sb, sc, onset, g, g2, amp=1.0):
    ev = [(S.SITES["A"], onset, amp * sa)]
    if sb:
        ev.append((S.SITES["B"], onset + g, amp * sb))
    if sc:
        ev.append((S.SITES["C"], onset + g + g2, amp * sc))
    return ev


def train(seed, rel, mode):
    gap, amp, eps = schedule(seed)
    W = [[0.0] * 8 for _ in U()]
    for sa, k1, k2, onset, g, g2 in eps:
        sb = rel[0] * sa * (1 if k1 else -1); sc = rel[1] * sb * (1 if k2 else -1)
        W = S.run(U(), W, events(sa, sb, sc, onset, g, g2, amp), STEPS, learn=True, rule=RULE, mode=mode)["weights"]
    return gap, W


def beta_c(W, gap, sa, sb):
    """Prediction in C's window (40 frames from C's onset), projected on C's own wave."""
    c0 = PROBE_ONSET + gap + gap + GAP2_EXTRA
    r = S.run(U(), W, events(sa, sb, 0, PROBE_ONSET, gap, gap + GAP2_EXTRA), STEPS)
    tc = E.passive([(S.SITES["C"], c0, 1.0)], STEPS)[c0:c0 + 40].ravel()
    fired = {pop: int(sum(1 for k, u in enumerate(U()) if u.pop == pop and r["spikes"][k])) for pop in ("A", "B")}
    return float(r["prediction"][c0:c0 + 40].ravel() @ tc / (tc @ tc)), fired


def read(W, gap, rel):
    r1, r2 = rel
    b = {}; fired = {}
    for sa in (1, -1):
        for sb in (1, -1, 0):
            b[(sa, sb)], fired["%+d%+d" % (sa, sb)] = beta_c(W, gap, sa, sb)
    screen = np.mean([(b[(1, sb)] - b[(-1, sb)]) / 2 for sb in (1, -1)])
    b_infl = np.mean([(b[(sa, 1)] - b[(sa, -1)]) / 2 for sa in (1, -1)])
    alone = (b[(1, 0)] - b[(-1, 0)]) / 2
    return {"beta": {"%+d%+d" % k: v for k, v in b.items()}, "units_fired": fired,
            "A_given_B": float(screen * r1 * r2), "B_influence": float(b_infl * r2), "A_alone": float(alone * r1 * r2)}


def direct_weight(W):
    """Signed direct A -> C weight: (A-ON minus A-OFF) summed over clocks and both C sites, divided by 2."""
    on = sum(sum(W[k]) for k, u in enumerate(U()) if u.pop == "A" and u.half == 1)
    off = sum(sum(W[k]) for k, u in enumerate(U()) if u.pop == "A" and u.half == -1)
    return (on - off) / 2


def job(arg):
    seed, rel, mode = arg
    gap, W = train(seed, rel, mode)
    rd = read(W, gap, rel)
    return {"seed": seed, "rule": mode, "rho1": rel[0], "rho2": rel[1], "gap": gap, "weights": W,
            "direct_A_weight_signed": float(direct_weight(W) * rel[0] * rel[1]), **rd}


def check():
    """With one unit holding nonzero weights, the computed own contribution must equal the field it hears."""
    W = [[0.0] * 8 for _ in U()]
    k = next(i for i, u in enumerate(U()) if u.pop == "B" and u.half == 1)
    W[k][6], W[k][7] = 0.7, -0.4
    ev = events(1, 1, 0, 20, 34, 54)
    r = S.run(U()[k:k + 1], W[k:k + 1], ev, STEPS, mode="similarity", record=True)
    own = np.array([h[0] for h in r["heard"]]); field = np.array([h[1] for h in r["heard"]])
    t = r["spikes"][0][0]
    print("fire tick", t, "own vs field at lags 3-8:", [(round(own[t + L], 6), round(field[t + L], 6)) for L in range(3, 9)])
    d = max(abs(own[t + L] - field[t + L]) for L in range(3, 3 + S.K_LEN))
    print("max difference:", d); assert d < 1e-6
    for pop, rows in U.cal.items():
        print(pop, "decays", [round(x[0], 4) for x in rows], "fire", [x[2] for x in rows])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--check", action="store_true"); ap.add_argument("--dev", action="store_true")
    a = ap.parse_args()
    if a.check:
        return check()
    t0 = time.time()
    if a.dev:
        jobs = [(s, rel, m) for s in DEV_SEEDS for rel in RELATIONS for m in RULES]
        out, label = HERE / "dev_results_screen.json", "screening-off: development bodies (not evidence)"
    else:
        jobs = [(s, RELATIONS[i % 4], m) for m in RULES for i, s in enumerate(SEEDS)]
        out, label = HERE / "results_screen.json", "screening-off: pre-registered batch"
    U()
    receipt = {"label": label, "rule": RULE, "q": Q, "episodes": EPISODES, "a_fire": list(A_FIRE), "b_fire": list(B_FIRE),
               "calibration": {p: [[float(d), list(map(float, th)), t] for d, th, t in rows] for p, rows in U.cal.items()},
               "results": [], "runner_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
               "engine_sha256": hashlib.sha256((HERE / "engine_screen.py").read_bytes()).hexdigest()}
    if not a.dev:
        receipt["protocol_sha256"] = hashlib.sha256((HERE / "PROTOCOL_SCREEN.md").read_bytes()).hexdigest()
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for n, rec in enumerate(pool.map(job, jobs), 1):
            receipt["results"].append(rec); receipt["elapsed_seconds"] = time.time() - t0
            out.write_text(json.dumps(receipt, indent=1))
            print("%d/%d %.0fs" % (n, len(jobs), time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
