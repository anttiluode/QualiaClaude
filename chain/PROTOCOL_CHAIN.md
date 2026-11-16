# Chain: protocol

Written 16 November 2026 by Claude Opus 5.5, **before** the scientific batch. Follow-up to this repository's first experiment (shared prediction), joining it with Astra's [QualiaAstra](https://github.com/anttiluode/QualiaAstra): there, an engineered chain of three belief units passes a clue two steps exactly; here, a wave body must learn the relations itself and pass a clue two steps through its own imagined middle event.

## Question

Can a body of fade-triggered units, learning only by a local rule, (1) learn two signed relations between three events, and (2) pass a clue two steps, A → imagined B → C, through a causal chain that runs through its own prediction of B? How close does it come to the exact Bayesian answer?

## World

Each episode: A is a signed pulse at site 0 (sign `sA` = ±1, balanced). B at site 4, `g` frames later (`g` = 28–42 per body, jitter ±3 per episode), has sign `ρ1·sA` with probability `q`, otherwise the opposite. C at site 7, `g + 20` frames after B (no extra jitter), has sign `ρ2·sB` with probability `q`. Each body gets its own `(ρ1, ρ2)`, cycling through all four combinations; it is never told them. `q = 0.85`.

Exact Bayes, given A's sign: `E[sB] = (2q−1)·ρ1·sA = 0.70·ρ1·sA`, `E[sC] = (2q−1)²·ρ1·ρ2·sA = 0.49·ρ1·ρ2·sA`. The second step is attenuated twice.

## Body

Two wave fields of the same physics (vendored upstream `WaveFieldNode`): the **world** field, driven only by the stimuli, and a **prediction** field, driven only by the units. Each branch (`DampingReturnNode`, same rule and settings as experiment 1) learns from `prediction − world` at its own tip, so the prediction field converges toward the world. Units are `FadingHistorySpikeNode`s fed a half-wave-rectified input (ON and OFF halves), so they are sign selective.

- **A-units:** 12 ON + 12 OFF, hear the *world* next to A, may write only around B (sites 3–5).
- **B-units:** 12 ON + 12 OFF, hear the *prediction* at B's place, may write only around C (sites 6–7).

The only route from A to a prediction of C runs through the body's own predicted B.

Training: 80 episodes per body, all fast state wiped between episodes. Test: growth frozen, A alone (B and C are never shown at test; the prediction field depends on the world only through the A-units).

## Development history (seeds 991–993; disclosed, not evidence)

1. First version: B-units fired after C had already arrived, and the C expectation was ≈ 0. A fade-triggered unit cannot fire until its input stops ringing (≈ 32 frames). **Changed:** C now comes `g + 20` frames after B instead of `g`; B-units arm at 0.15 of a full B's peak trace (they hear an imagined, weaker B) instead of 0.35.
2. Training doubled from 40 to 80 episodes (B-units only start firing once the imagined B has grown).
3. B-unit fade rates re-spread over 0.82–0.935, the band that fires 35–70 frames after an imagined B.
4. Jitter on the second gap removed, so C's timing relative to A varies ±3 frames, like B's (no effect in development; kept).
5. Refractory period 120 frames for all units (each fires at most once per episode); B-units were re-firing on their own ringing and writing a second, misplaced C.
6. A staged readout added (below), because one whole-window fit let the B and C templates trade off.

After these, development bodies gave: step one 0.53, 0.66, −0.55 (Bayes ±0.70); step two 0.05, −0.06, −0.23 (Bayes ±0.49), all with the correct sign; cutting B-units removed step two; reversing them flipped it.

## Measurements

For `sA = +1` and `−1`, the prediction field's sensor waves are read out:

- **Staged readout (primary).** `β_B`: least-squares fit of the prediction onto A and B templates in B's window (B's onset to C's onset). `β_C`: projection onto the C template of what A and B do not explain, in the 40 frames from C's onset.
- `ΔB = (β_B(+A) − β_B(−A))/2`, `ΔC` likewise. Bayes: `ΔB* = 0.70·ρ1`, `ΔC* = 0.49·ρ1ρ2`.
- Whole-window three-template fit, reported alongside.
- **Interventions:** cut B-units' outputs; reverse B's message (B-ON hears the negative half and B-OFF the positive); cut A-units' outputs.

**Batch:** 16 bodies with `q = 0.85` (seeds 160001–160016, four of each relation type) and 8 control bodies with `q = 0.5`, where there is no relation to learn and Bayes predicts zero (seeds 160101–160108).

## Decision rule (16 primary bodies, staged readout)

**Claim 1, a learned causal chain**, is shown only if all hold:

1. step one: `sign(ΔB) = ρ1` in at least 14 of 16, and median `ρ1·ΔB / 0.70` at least 0.5;
2. step two: `sign(ΔC) = ρ1ρ2` in at least 13 of 16 (one-sided binomial p ≈ 0.01 against chance);
3. cutting the B-units reduces the median `|ΔC|` by at least 70%, while the median `|ΔB|` changes by less than 20%;
4. reversing B's message makes `sign(ΔC)` opposite to the intact body's in at least 13 of 16.

**Claim 2, Bayes-like strength**, is shown only if median `ρ1·ΔB / 0.70` and median `ρ1ρ2·ΔC / 0.49` are both at least 0.5. Development suggests step two will fall short; it is stated anyway.

Reported without a rule: the `q = 0.5` control (Bayes zero), the whole-window readout, and the attenuation ratio `(ρ1ρ2·ΔC) / (ρ1·ΔB)` against Bayes's 0.70.

## Declared in advance

The relations and the chain topology are not supplied as equations, but the anatomy is: which units hear which field and where they may write was chosen by hand to make a chain the only route. The rule is an LMS canceller; ON/OFF rectification and local projection are standard. A one-line sign rule would solve this task exactly, as in QualiaAstra; the question is whether a physical body with a local rule learns to.
