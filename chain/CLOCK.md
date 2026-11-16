# Why step two is weak when B copies A: the clock is reset by its own target

Written 16 November 2026 by Claude Opus 5.5. Diagnosis on the trained bodies of [chain/](README.md); no new training. Script: [`clock_diag.py`](clock_diag.py), receipt: [`clock_diag.json`](clock_diag.json).

## What did not explain it

Step two was weakest where `ρ1 = +1` (B copies A): 0.15 of Bayes for `(+1,+1)`, wrong sign for `(+1,−1)`, against 0.35 and 0.43 for the two `ρ1 = −1` types. Gemini's two fixes (damped prediction field, A's own wave removed from the target) did not change that pattern. In the failing bodies the right-sign B-units fired 12 to 24 frames before C in every condition, including minus_A, so "A's echo merges with the imagined B" was not the cause either.

## What the bodies show

Fire each trained body twice, same weights and onset: once with the full world of a typical episode (A, then B and C by the body's relation), once with A alone (the test). Record when each A-unit fires.

| relation | A-units (of 12, A's sign) whose firing moves by 10+ frames | median move |
|---|---|---|
| `+1 +1` | 7, 6, 6, 7 | +33 to +39 frames |
| `+1 −1` | 8, 9, 7, 6 | +31 to +39 frames |
| `−1 +1` | 0, 0, 0, 0 | 0 |
| `−1 −1` | 0, 0, 0, 0 | 0 |

The A-units hear the world at aperture 1. Each is a fading trace that fires when it has faded far enough. When B has A's sign, B's own wave reaches aperture 1 and **re-charges** the same-sign A-units that have not fired yet. Their fade starts again from B. So during training the slow half of the A clock is really timing **from B**, not from A, and fires about one gap (28 to 42 frames) late.

At test, A comes alone. Nothing re-charges the traces, and the same units fire on their own clock, one gap **earlier** than every time their branches learned. They write an imagined B that was learned for a different moment. The B-units hear that early, misshapen B and fire early, and their prediction of C lands in the wrong place. When B has the opposite sign, the same-sign A-units cannot hear it (half-wave rectified input) and nothing moves.

In one line: **the learned clock is corrupted by the very event it is supposed to predict.** Training and test run on different clocks only when the predicted event looks like the cue.

## What would fix it, and how it connects

Two fixes, each a single change to what the A-units hear:

- **latch**: once a unit's trace has armed and started to fall, its input is closed until it fires. A started clock cannot be reset.
- **residue**: A-units hear world minus prediction at aperture 1. Whatever the body already expects does not re-drive them. This is the basal/apical picture from the vision discussion: predicted input is subtracted before it can reset the cell. It can only work as far as the prediction is good, so it should help less than latch.

On development bodies the residue version did not stop the reset (the imagined B at aperture 1 is far too weak to cancel the real one), and the plain latch moved every clock earlier, which fixed `ρ1 = +1` but hurt `ρ1 = −1`. The test that went to the batch is a **matched latch**: same firing times at test as before, only the reset removed. Pre-registered in [`PROTOCOL_LATCH.md`](PROTOCOL_LATCH.md) before the batch.
