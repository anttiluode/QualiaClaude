"""Diagnosis of the weak step two, on the trained chain/ bodies (no new training). See chain/CLOCK.md.

For each primary body: fire the trained body once with the full world of a typical episode (A = +1, B and C
by the body's relation, kept) and once with A alone, same weights, same onset. Report each unit's change of
first firing time (full minus A alone). A change in a WORLD-listening unit means something after A moved its
clock; a change in a B-unit means the imagined B it hears arrived at a different time.
"""
import json, pathlib, sys
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import engine_chain as C
import run_chain as R

U = R.U()
rows = []
for r in [x for x in json.loads((HERE / "results_chain.json").read_text())["results"] if x["q"] == 0.85]:
    W, gap = r["weights"], r["gap"]
    sa = 1; sb = r["rho1"] * sa; sc = r["rho2"] * sb
    full = C.run(U, W, R.events(sa, sb, sc, R.PROBE_ONSET, gap, gap + R.GAP2_EXTRA), R.STEPS)["spikes"]
    alone = C.run(U, W, R.events(sa, 0, 0, R.PROBE_ONSET, gap, gap + R.GAP2_EXTRA, a_only=True), R.STEPS)["spikes"]
    def shift(pop, half):
        return [int(full[k][0] - alone[k][0]) for k, u in enumerate(U)
                if u.listens == pop and u.half == half and full[k] and alone[k]]
    rows.append({"seed": r["seed"], "rho1": r["rho1"], "rho2": r["rho2"], "gap": gap,
                 "A_units_shift": shift("world", sa), "B_units_shift": shift("prediction", sa * r["rho1"])})
by = {}
for a in (1, -1):
    for b in (1, -1):
        rr = [x for x in rows if (x["rho1"], x["rho2"]) == (a, b)]
        by["%+d%+d" % (a, b)] = {"A_units_moved_by_10_or_more": [sum(abs(s) >= 10 for s in x["A_units_shift"]) for x in rr],
                                 "median_shift_of_moved_A_units": [float(np.median([s for s in x["A_units_shift"] if abs(s) >= 10] or [0])) for x in rr]}
out = {"rows": rows, "by_relation": by}
(HERE / "clock_diag.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(by, indent=1))
