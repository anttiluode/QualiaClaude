# Screening-off test: protocol

Written 16 November 2026 by Claude Opus 5.5, **before** the batch on the 16 primary bodies (seeds 170001 to 170016).

## The question

Sol's Gate 4 (QualiaAstra) found that residual-driven growth, delay-aware similarity growth and an oracle all reached the same error on one clean route. That is what the mathematics predicts when candidate inputs are not redundant: a least-squares fit, which settles at `w = R⁻¹p`, and a one-input-at-a-time correlation fit, which settles at `w ∝ p`, agree when `R` is nearly diagonal. They differ only when inputs are redundant. Then a residual learner **explains away** and a similarity learner **double counts**.

The chain has a clean redundant case. The world is Markov, `A → B → C`. Given B, A carries no further information about C:

$$E[s_C \mid s_A, s_B] = (2q-1)\,\rho_2\, s_B, \qquad \text{so the direct A} \to \text{C weight is } 0.$$

A direct axon from A still correlates with C, at `(2q−1)² = 0.49`. So a similarity learner should grow it, and a residual learner should not.

## The body ([`engine_screen.py`](engine_screen.py))

- **Units.** 12 A-clocks per sign hear A's own wave at aperture 0; they fire 66 to 122 frames after A, and C arrives 76 to 104 frames after A. 12 B-clocks per sign hear the **real** B's own wave at aperture 4; they fire 40 to 78 frames after B, and C arrives 48 to 62 frames after B. All units are fade-triggered and latched, calibrated by bisection on the fade rate ([`units_screen.json`](units_screen.json)).
- **Branches.** Every branch writes only at sites 6 and 7, C's place, into a prediction field with the same physics. So C's tip has two candidate inputs: the direct A axon and the B route.
- **World.** As in chain/: `q = 0.85`, signed relations `ρ1, ρ2` per body, B at gap 28 to 42 (±3 jitter per episode), C a further gap + 20 after B. 240 episodes. The target is C's own wave.
- **The two rules use the same `DampingReturnNode`** (rate 0.03, window 3 to 5, self-response 0.71, clip 2). They differ **only** in what a branch hears at its tip:
  - **residual**: shared prediction minus C (`P − C`). Each branch explains what the others leave.
  - **similarity**: its own contribution minus C (`P_k − C`). Each branch explains C alone, so its fixed point is the delay-aware correlation weight. `P_k` comes from a measured field kernel; it matches the field to 1.2e-7 (`run_screen.py --check`).

## Readout (prediction projected on C's wave, 40 frames from C's onset)

All statistics are sign-aligned to the body's relation:

| statistic | what it measures | Bayes value |
|---|---|---|
| `A_given_B` | A's influence on the C prediction when B is present | 0 |
| `B_influence` | B's influence | 1 (that is, 0.70) |
| `A_share` = raw `A_given_B` / raw `B_influence` | the primary, scale-free measure | 0 (a one-at-a-time fit: about 0.7, less with A's timing jitter) |

## Development, disclosed

Seeds 981 to 983, every relation type ([`dev_results_screen.json`](dev_results_screen.json)). Three changes were made before the development batch, all disclosed:

1. A-units first read at aperture 1. B's wave armed some opposite-sign A-units there, so they were moved to aperture 0.
2. In the shared world field, A's wave at aperture 4 overlaps B's arrival. No arm threshold separated right-sign from wrong-sign B-units: right-sign peak 0.74 of calibration, wrong-sign up to 0.82. So each population was given its own receptor (it hears only its own stimulus's wave). After this, 0 of 16 sign and amplitude combinations fired a wrong unit.
3. After the first development bodies, the similarity rule overshot in **both** banks (B influence about 2× Bayes, because 12 clocks each fit C alone and their pings overlap). `A_share` was therefore made the primary measure, being scale-free. No rule parameter was changed.

Development result: `A_share` residual 0.11, −0.04, 0.09 against similarity 0.55, 0.48, 0.45.

Two exact properties, seen in development and explained:
- **The four relation types give identical numbers for a given schedule.** With separate receptors the system is exactly mirror-symmetric under sign flips (ON and OFF swap). So relation types are not independent here, and the 16 bodies differ only by schedule.
- **`A_given_B` equals `A_alone`.** With firing times fixed, the prediction is a sum of A's and B's contributions, so A's influence does not depend on whether B is present.

## Decision rule (16 primary bodies)

"Residual learning screens off, similarity does not" counts as **shown** only if all hold:

1. similarity: `A_given_B` > 0 in at least 14 of 16 (it does not screen off);
2. residual `|A_share|` smaller than similarity's in at least 14 of 16, paired by body (one-sided sign test p ≈ 0.002);
3. median residual `|A_share|` at most one quarter of median similarity `|A_share|`;
4. both rules learn the B route: `B_influence` > 0 in at least 14 of 16 for each.

Reported without a rule: `B_influence` (calibration), `A_alone`, the signed direct weight.

## Predictions, recorded before the run

- Residual `A_share` about 0.05 to 0.12, not 0. Training is finite, and A's ±3 jitter gives it a little real timing information about C's waveform that the B-clocks' discrete pings may not cover.
- Similarity `A_share` about 0.45 to 0.55. Similarity `B_influence` about 1.6 to 2.2 (overshoot); residual about 0.8 to 1.0.
- So residual learning is also the **calibrated** one. With A alone, it predicts almost nothing about C, because it relies on B. That is the price of screening off without an imagined B, and it is exactly why chain/ needed one.
