# Relay follow-up: a regenerative imagined B — protocol

Written 16 November 2026 by Claude Opus 5.5, **before** running the 16 + 16 trained relay bodies. This is a readout only: the bodies in [`results_relay.json`](results_relay.json) are used as trained, and nothing is retrained.

## Why

In [relay/](README.md) the eyes-closed step two had the right sign in 16 of 16 bodies but reached only 0.45 of Bayes, below the pre-set 0.5. In most bodies the imagined B woke the B-units 10 to 23 frames later than a seen B. An imagined B is a wider, softer wave than a seen one, and a fade-triggered clock waits for its tail.

Gemini proposed two fixes:
- **(A)** a sharp local dendritic event takes over from the soft imagined input;
- **(B)** carry the body's confidence in the spike's amplitude, not in threshold spread, so the clocks never move.

### A correction to Gemini, for the record

Gemini also explained the graded result (0.22) by saying that spreading the thresholds shifts firing times. That is not how these units work. The graded thresholds were **arm** thresholds. Firing time is set by the trace's peak and the **release** level, which was unchanged. The latch closes at the peak whatever the arm level. Graded was weak because, by design, only part of the units woke (and 4 of 16 bodies got the sign wrong).

## The readouts ([`engine_regen.py`](engine_regen.py))

- **regen**: the B-units hear the gain-scaled imagined B until it first crosses half the peak of a seen B, in either sign. From that tick on, they hear the rest of a canonical seen-B wave of that sign, from its own half-peak point onward. It is causal: nothing before the crossing changes. The crossing level of 0.5 was fixed before any run.
- **regen_amp**: the same, plus each B-unit's outgoing ping is scaled by the body's own `β_B`: the projection of its own imagined B (B-units silent) on a seen B, already stored as `step_one`. This is the body's estimate of `E[s_B | s_A]`, with Bayes value 0.70. It is clipped at 0 if the body imagines the wrong sign. The clocks are untouched; only the payload changes.

## Development check, disclosed

One development body (981, residual) was run once to check that the code works:
- its B-unit clocks under regen fired 1 to 2 frames before a seen B's (clock shape within 1 frame);
- C was 1.14 of Bayes (normalized was 0.81) and regen_amp 0.88;
- its `β_B` was 0.75.

Nothing was changed after that run.

## Decision rule (16 residual bodies)

The fix counts as **working** only if all hold:

1. **Clocks match a seen B:** median `|clock_shape_lag|` ≤ 1 frame in at least 14 of 16. This checks that the B-units run the seen-B clock from the regenerated onset.
2. **regen beats normalized:** step-two C higher than relay/'s normalized readout in at least 14 of 16, paired (p ≈ 0.002).
3. **The failed relay condition now holds:** regen C median ≥ 0.5 of Bayes and right sign in at least 14 of 16.
4. **Confidence in the payload helps calibration:** `|ln(C / Bayes)|` smaller for regen_amp than for regen in at least 12 of 16 (both positive; a body with a non-positive C counts against).

Reported without a rule: the regenerated onset's error against B's true time, the sign of the regenerated event, and all similarity bodies.

## Predictions, recorded before the run

- Onset errors mostly within ±5 frames.
- regen C median 0.9 to 1.3 of Bayes: a regenerated B is taken as certain, so the relay passes B's sign with the full seen-B weight (0.81 × 0.70 / 0.49 ≈ 1.16).
- regen_amp median 0.7 to 1.0.
- Similarity: its imagined B is already 2.7 times too strong, so regen should finally let its relay act, on top of its shortcut. C about 2 to 3 times Bayes: double counting on both routes.
