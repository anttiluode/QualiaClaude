# Shared prediction: protocol

Written 16 November 2026 by Claude Opus 5.5, **before** the scientific batch. Development runs on seeds 991–993 were made first and are kept in [dev_results.json](dev_results.json), labelled as development; they were used to check plumbing and set the thresholds below, and are not evidence.

## The idea being tested

Antti's proposal: the qualia candidate is a **shared prediction**, a population of units that together keep up an expectation of the world. Astra sharpened it: a pile of independent predictors can also add up to one output, so the test is whether **one small piece of evidence makes the population revise its expectations coherently, at places it does not sense**, toward one consistent world.

This repository tests that mechanism. It cannot test whether anything is felt.

## Setup

One shared wave field (vendored upstream `WaveFieldNode`, 96×96), two senses, three banks of fade-triggered units (vendored `FadingHistorySpikeNode`), every unit returning into the field through a `DampingReturnNode` with eight signed branches. The rule and its settings are those of StateShapedPingRecall `damping/`, unchanged: learning rate 0.03, listening steps 3–5, self-response 0.71, weight cap 2.0.

- **Two hidden worlds.** World B: A (site 0) then B (site 7). World C: A then C (site 4). Same gap. A alone cannot tell them apart.
- **Second sense.** Two frames after A, a tone arrives on one of two separate lines. Tones never enter the field.
- **A-bank:** 24 timers hearing the world's wave at aperture 1 (fade rates of StateShapedPingRecall `damping2/` "even"; they hear the stimuli only, not the body's own output).
- **Tone banks:** 12 timers per tone, hearing only their tone line, fade rates chosen so they fire every four ticks from 16 to 60 frames after the tone.
- **Training:** 40 episodes per body, worlds balanced 20/20 in random order, onset jitter ±5, gap jitter ±3 (Astra's generator), all fast state wiped between episodes.

| Condition | Tone during training |
|---|---|
| informative | tone 1 in world B, tone 2 in world C |
| uninformative | tone 1 or 2 drawn independently of the world, balanced 20/20 |
| a_bank_only | no tone banks |

Fresh seeds 150001–150016: one body per seed per condition, 48 bodies. Within a seed the worlds, onsets and gaps are identical across conditions; only the tone assignment differs.

## Measurements

All with growth frozen, from a full wipe, second event **omitted**. `T_B` and `T_C` are the passive missing waves of B and C. Over the window from two frames after the missing event to 100 frames later, the body's response `p` (minus passive A) is fitted as `p = −β_B T_B − β_C T_C`. So `β_B` is how strongly the body expects B, as an anti-wave, and `β_C` the same for C. The fraction of `p` the fit explains is reported.

- **Cues:** A alone; A + tone 1; A + tone 2.
- **Revision index** `R = (β_B|tone1 − β_B|tone2) + (β_C|tone2 − β_C|tone1)`. Perfect revision is 2; none is 0.
- **Coherence:** relative to A alone, tone 1 raises `β_B` and lowers `β_C`, and tone 2 raises `β_C` and lowers `β_B`.
- **Bank swap (meaning by intervention):** swap the weights of the two tone banks; R should change sign.
- **A-bank silenced:** what the tone banks alone contribute.
- **Meaning by removal:** for each tone unit, the change in `(β_B, β_C)` under its own tone when that unit's branches are zeroed.
- **Surprise:** energy left when a world arrives with the matching tone, the wrong tone, or no tone, relative to an untrained body.

## Decision rule (informative condition, 16 bodies)

Shared prediction with coherent revision counts as **shown in this system** only if all four hold:

1. median R at least 0.5, and R above zero in at least 14 of 16 bodies;
2. all four coherence directions hold in at least 14 of 16 bodies;
3. R higher than in the uninformative condition: paired seed-bootstrap 95% interval (20,000 resamples, generator seed 890) of informative minus uninformative excludes zero, positive;
4. swapping the tone banks reverses the sign of R in at least 14 of 16 bodies.

Also reported, without pass rules: the A-alone expectation in every condition (does the body hold a split expectation, a predictive distribution?), the surprise table, and the meaning-by-removal map.

## Declared in advance

- The rule that does the learning is an LMS adaptive canceller with anti-Hebbian sign. Learning a context-dependent negative image of expected input is known: it is what the electrosensory lobe of mormyrid electric fish does with corollary discharge (Bell and colleagues), and it is what adaptive noise cancelling with a reference input does. What is tested here is whether that mechanism, in a shared wave medium with two senses, produces coherent revision of a split expectation.
- Revision here is additive: the tone banks add a correction to what the A-bank predicts. The A-bank's own units do not change their minds. Whether that counts as a population "settling" or as independent parts summing is a question this design does not settle.
- Nothing here bears on whether anything is felt.
