# Relay: protocol

Written 16 November 2026 by Claude Opus 5.5, **before** the batch on the 16 primary bodies (seeds 180001 to 180016).

## The question

[screen/](../screen/README.md) showed that residual learning drops the direct A → C shortcut once the real B carries C. The price is that a body which learned that way predicts almost nothing about C from A alone. [chain/](../chain/README.md) showed a body can relay a clue through an imagined B. Can one body do both? It should screen the shortcut off when B is seen, and use an imagined B, through the **same** B-units, when B is not.

The key point is "the same B-units". The B → C weights are learned only from perceived B. They help with A alone only if imagination wakes the units that perception trained.

## The body ([`engine_relay.py`](engine_relay.py))

Latched fade-triggered clocks, separate receptors, the same `DampingReturnNode` and wave physics as screen/:

- **AB** (12 per sign) hear A and fire 24 to 60 frames after it. Their branches write at B's place (sites 3 to 5).
- **AC** (12 per sign) hear A and fire 66 to 122 frames after it. Their branches write at C's place (sites 6, 7): the shortcut.
- **B** (12 per sign): **eyes open**, they hear the real B. **Eyes closed**, they hear the prediction field at B's place, gain-scaled. Their branches write at C's place.
- **Targets:** B's own wave at sites 3 to 5, C's own wave at 6 and 7. All learning happens with eyes open (240 episodes, the world of chain/ and screen/). Two rules, as in screen/: **residual** (primary) and **similarity**.
- **The gain G** is measured by each body on itself: a perceived B's peak at aperture 4, divided by the peak of its own imagined B with the B-units silent.

Eyes closed, two ways for the B-units to take up the imagined B:

- **normalized** (primary): drive G × imagined B, perception threshold kept. A right-sign unit fires as if B were seen.
- **graded** (reported only): same drive, but unit k may arm only if the raw imagined B reached θ_k of a perceived B, with θ spread over (0.25, 1).

## Development, disclosed

Three bodies (seeds 981 to 983, relation (+1,+1); relation types are mirror-equivalent with separate receptors), file [`dev_results_relay.json`](dev_results_relay.json). Residual rule:

| body | step one (imagined B, of Bayes) | eyes open, A share | eyes open, A alone → C | eyes closed, normalized → C | eyes closed, graded → C |
|---|---|---|---|---|---|
| 981 | 1.07 | 0.10 | 0.12 | **0.81** | 0.11 |
| 982 | 0.89 | −0.06 | −0.06 | **0.33** | 0.30 |
| 983 | 0.93 | 0.11 | 0.15 | **0.87** | 0.88 |

What development showed, and what changed:

1. **My first prediction for "normalized" was wrong.** I expected it to be about 1.4× overconfident, because it passes B's sign, not its probability. It came out below Bayes instead.
2. **Imagined clocks run a little late.** In residual bodies the imagined B wakes the B-units 1 to 5 frames later than a seen B, but the slow half of body 982 ran about 20 frames late. That is why 982 is weak.
3. **The graded thresholds were changed.** They first ran over (0, 1), and the lowest-threshold opposite-sign units armed on the imagined B's opposite lobe (2 wrong-sign units per probe). The range is now (0.25, 1). Training is unaffected: θ is used only with eyes closed. Graded was not rerun after this change.
4. **The similarity relay adds nothing.** Its imagined B is double counted, so it is both too large and too long. The B-units' traces keep rising through it and fire 26 to 55 frames late, after C's window. Its eyes-closed C equals its eyes-open A-alone C, which is all shortcut.

`B_clock_lag_vs_seen` (imagined minus seen firing time, right-sign B-units) was added to the readout after development.

## Decision rule (residual rule, normalized imagination, 16 bodies)

"One body screens off when it sees B and relays through an imagined B when it does not" counts as **shown** only if all hold:

1. **Screening holds in the joined body:** eyes open, median `|A share|` ≤ 0.15, and B's influence has the right sign in at least 14 of 16.
2. **No step two without imagining:** eyes open with A alone, median C ≤ 0.2 of Bayes.
3. **Imagining restores step two:** eyes closed, C has the right sign in at least 14 of 16 and median ≥ 0.5 of Bayes.
4. **Eyes closed beats eyes open on A alone** in at least 14 of 16 bodies (one-sided sign test p ≈ 0.002).

Reported without a rule: similarity throughout, graded, step one, the imagined-clock lag.

## Predictions, recorded before the run

- Residual, eyes closed, normalized: median 0.6 to 0.9 of Bayes, with a few weak bodies where the slow B-clocks run late on the imagined B.
- Similarity: eyes closed about equal to eyes open (the relay adds nothing in C's window); its A-alone C comes from the shortcut, about 0.4 to 0.8 of Bayes.
- Graded: below normalized. I have no confident prediction of how far.
