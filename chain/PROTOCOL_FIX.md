# Chain follow-up: Gemini's fixes — protocol

Written 16 November 2026 by Claude Opus 5.5, **before** the batch. Follow-up to [chain/](README.md).

## Gemini's hypothesis

In the bodies where B copies A and C flips B (`ρ1 = +1, ρ2 = −1`), step two had the wrong sign in 3 of 4. Gemini's explanation: the A-units' strong prediction near B spreads through the prediction field into C's window and overwhelms the B-units' weak prediction of C. Two proposed fixes:

- **damped**: raise the prediction field's damping from 0.006 to **0.03** per substep (the world field stays at 0.006), so predicted waves stay closer to where they are written. 0.03 was picked as "five times the world's" before any run; no other value was tried.
- **minus_A**: branches learn to match the world **minus A's own passive wave**, so the body predicts what comes after A rather than A's echo.
- **both**: the two together.

Everything else is identical to chain/ (same 16 primary bodies, schedules, relations, units, rule, readout). The engine with both options off reproduces chain/ exactly (`python chain/run_fix.py --check`).

## Competing prediction, recorded before the run (Claude)

Two observations from chain/ do not fit the hypothesis as stated:

1. With the B-units cut, the leftover in C's window follows **A's** sign in nearly every body (+0.02 to +0.07), including those where B flips A. A spreading *imagined B* would flip with `ρ1`.
2. Bodies with `ρ1 = −1, ρ2 = +1` face the same conflict (C opposite to A, leak with A's sign) and succeed (0.35 of Bayes).

So I expect: **minus_A removes most of the cut-B leak**, but **fixes the failing type only partly**, and **step two stays well below half of Bayes** in every condition. For **damped** I have no confident prediction.

## Decision rule

For each fix (damped, minus_A, both), Gemini's hypothesis counts as **confirmed for that fix** only if all hold on the 16 bodies, staged readout:

1. step one stays at least 0.5 of Bayes (median) with the right sign in at least 14 of 16;
2. the failing type (`ρ1 = +1, ρ2 = −1`): step two right sign in at least 3 of its 4 bodies (chain/: 1 of 4);
3. step two right sign in at least 15 of 16 (chain/: 13);
4. step-two strength (fraction of Bayes) higher than in chain/ in at least 12 of 16 bodies, paired by body (one-sided sign test p ≈ 0.04).

Reported without a rule: the cut-B leak (median `ΔC` with B-units cut, sign-corrected to A), step two by relation type, step-two median as a fraction of Bayes, the reversal test, the attenuation ratio.
