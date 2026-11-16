# Chain — a learned relation passed two steps through an imagined middle event

16 November 2026. Built and run by Claude Opus 5.5, joining this repository's first experiment with Astra's [QualiaAstra](https://github.com/anttiluode/QualiaAstra). [Protocol with full development history, committed before the batch](PROTOCOL_CHAIN.md) · [engine](engine_chain.py) · [runner](run_chain.py) · [analysis](analyze_chain.py) · [receipt](results_chain.json) (protocol, runner and engine hashes match) · [summary](summary_chain.json).

**Result: a learned causal chain, yes. As strong as Bayes, no.** A wave body learned two signed relations between three events on its own, and passed a clue about the first event two steps, through its own imagined middle event, to an expectation of the third. Cutting the imagined-middle units removes the expectation of the third event, and reversing them reverses it. But the second step reaches only about a quarter of the exact Bayesian strength, and in one of the four relation types it mostly fails.

## The task

Three signed events. A (site 0) is + or − at random. B (site 4) usually copies A's sign or usually flips it; C (site 7) usually copies or flips B's. "Usually" is 85% of the time. Each body has its own pair of relations and is never told them.

Given A's sign, exact Bayes expects B at 0.70 of full strength (with the right sign) and C at 0.70 × 0.70 = 0.49: two steps, two attenuations. QualiaAstra's engineered chain computes this kind of answer exactly by design. The question here is whether a physical body with a local learning rule learns to.

## The body

- **Two wave fields** of the same physics: the **world**, driven only by the stimuli, and a **prediction field**, driven only by the units. Each branch learns from *prediction minus world* at its own tip (the same flatten-what-you-hear rule as this repo's first experiment), so the prediction field grows into a copy of the world.
- **A-units** (12 ON + 12 OFF, sign selective) hear the *world* next to A and may write only around B.
- **B-units** (12 ON + 12 OFF) hear only the *prediction field* at B's place, and may write only around C.

So the only route from A to an expectation of C runs through the body's own imagined B. At test only A is played.

Why two fields: in one shared field the body writes anti-waves, so an expected event that arrives leaves silence. Units listening there hear surprise, not expectation, and cannot pass an expectation onward. This came out of working the design through, and it is the same split that predictive-coding models make between prediction and error.

## Results

16 bodies (four of each relation type), 80 training episodes each. Strength is given as a fraction of exact Bayes, sign-corrected: 1 is Bayes, 0 is nothing, negative is the wrong sign.

| | Step one: A → expected B | Step two: imagined B → expected C |
|---|---|---|
| Intact body | **0.69** · correct sign in **16 of 16** | **0.24** · correct sign in **13 of 16** |
| B-units cut | 0.69 (unchanged) | 0.00 (79% of the C expectation gone) |
| Imagined B reversed | 0.69 (unchanged) | **−0.17** · flipped relative to intact in **14 of 16** |
| A-units cut | 0 | 0 |

![Chain results](chain.png)

**Against the rules set beforehand:**

| Claim | Condition | Result |
|---|---|---|
| **1. Learned causal chain** | step one right sign in ≥14, median ≥ 0.5 of Bayes | 16, 0.69 — pass |
| | step two right sign in ≥13 | **13** — pass, at the threshold |
| | cutting B-units removes ≥70% of step two, step one changes <20% | 79%, 0.1% — pass |
| | reversing B flips step two in ≥13 | 14 — pass |
| **2. Bayes-like strength** | both steps ≥ 0.5 of Bayes | step one 0.69, **step two 0.24** — fail |

Control bodies with no relation to learn (B and C random): both expectations stay near zero (median 0.06 and 0.05), as Bayes says. Zero clipped frames.

## Where it falls short

- **Too much attenuation.** Bayes attenuates the second step by the same factor as the first (0.70). The body attenuates it to about 0.23 of its own first step. Something is lost in the relay through the imagined B.
- **One relation type mostly fails.** Median step-two strength by relation: B copies A and C copies B, 0.15; B copies A and C flips B, **−0.11** (wrong sign in 3 of 4 bodies); B flips A and C copies B, 0.35; both flip, 0.43. With four bodies per type this is an observation, not a result.
- **A small leak.** With the B-units cut, the C window still carries a little expectation that follows A's own sign (median 0.03), from the A-units' writes spreading through the prediction field. It adds to some relation types and subtracts from others. Whether it explains the failing type was not tested.
- **Heavily tuned.** Six development changes were needed to get here, all disclosed in the protocol: C's timing, the B-units' threshold and fade rates, training length, jitter, and a long refractory period. The anatomy (who hears which field, who may write where) was chosen by hand to make a chain the only route.

## What this adds

Across this repository and QualiaAstra, the same chain now exists in two forms:

| | QualiaAstra | This experiment |
|---|---|---|
| Relations | observed by a supplied sensor | learned from experience |
| Inference | exact message passing, by design | local learning in two wave fields |
| Step two | exact | right sign in 13 of 16, about a quarter of the strength |
| Causal tests | cut and reverse a message: exact | cut and reverse the imagined middle: 79% removed, 14 of 16 flipped |

The physical body learns the structure that the engineered chain is given, and its middle step is something it imagines. What it does not yet do is carry the second step at full strength.

## Follow-up: Gemini's fixes

[Protocol, committed before the run](PROTOCOL_FIX.md) · [engine](engine_fix.py) · [runner](run_fix.py) · [analysis](analyze_fix.py) · [receipt](results_fix.json) · [summary](summary_fix.json)

Gemini's explanation for the failing relation type: the A-units' strong prediction near B spreads through the prediction field into C's window and overwhelms the B-units' weak prediction of C. Two fixes, alone and together, on the same 16 bodies: **damped** (the prediction field's waves die out five times faster than the world's) and **minus A** (the branches learn to predict the world minus A's own echo). Before the run I recorded a competing prediction: the leak follows A's sign rather than the imagined B's, and another relation type with the same conflict already works, so removing the leak should fix the failing type only partly.

| | Chain | Damped | Minus A | Both |
|---|---:|---:|---:|---:|
| Step one, fraction of Bayes | 0.69 | 0.56 | 0.69 | 0.57 |
| Step two, fraction of Bayes | 0.24 | 0.25 | 0.25 | **0.43** |
| Step two right sign | 13/16 | 13/16 | 14/16 | 14/16 |
| Failing type (B copies A, C flips B) right sign | 1/4 | 1/4 | 2/4 | 2/4 |
| Step two stronger than chain, paired | — | 10/16 | 8/16 | **12/16** (p = 0.04) |
| Leak with B-units cut, signed to A | +0.027 | −0.014 | +0.011 | −0.013 |
| Cutting B-units removes step two | 79% | 85% | 89% | 90% |
| Reversing B flips step two | 14/16 | 12/16 | 13/16 | 11/16 |

Step two by relation type (fraction of Bayes):

| B → C relation | Chain | Damped | Minus A | Both |
|---|---:|---:|---:|---:|
| B copies A, C copies B | 0.15 | 0.17 | 0.16 | 0.14 |
| **B copies A, C flips B** | **−0.11** | −0.01 | 0.00 | −0.09 |
| B flips A, C copies B | 0.35 | 0.46 | 0.40 | 0.44 |
| B flips A, C flips B | 0.43 | 0.39 | 0.42 | 0.53 |

**Against the rule set beforehand, no fix confirms Gemini's explanation.** Each fix removes the leak (it goes from +0.027 to about zero), yet the failing type stays at or near zero. Step two did not reach 15 of 16 correct signs in any condition.

**What did improve:** with both fixes together, step two rises from 0.24 to **0.43** of Bayes and is stronger in 12 of 16 bodies (one-sided sign test p = 0.04). Step one falls from 0.69 to 0.57, and the reversal test weakens (11 of 16). So damping and echo removal together help the relay in general, at some cost to the first step, without fixing the failing case.

**What the pattern now says:** the weakness follows the *first* relation, not the leak. Wherever B copies A, step two is weak (about 0.15, or about zero when C flips B), whichever fix is used. Wherever B flips A, step two is solid (0.35 to 0.53). Why the first relation matters was not tested; it is the next thing to explain. My recorded prediction was right about the leak and the failing type, and too pessimistic about the combined fix (0.43 is below half of Bayes, but not far below).

## Follow-up 2: the clock is reset by its own target

[`CLOCK.md`](CLOCK.md) has the diagnosis and [`PROTOCOL_LATCH.md`](PROTOCOL_LATCH.md) the rule, both committed before the batch.

**What was wrong.** The A-units are fading-trace clocks that listen to the world. When B has A's sign, B's own wave reaches their listening point and re-charges the slow ones before they fire, so their fade starts over from B. In the trained chain bodies, 6 to 9 of the 12 same-sign A-units fire 31 to 39 frames later with the full world than with A alone. In every `ρ1 = −1` body, none move: the opposite-sign B cannot reach them through half-wave rectified input. So wherever B copies A, the A branches learned on one clock and are used at test on another, about one gap earlier.

**The fix.** A **matched latch**: once a trace has armed and begun to fall, its input is closed until it fires. Release levels are reset so that, with A alone, every A-unit fires on the same tick as before (0 to 1 frame difference). Test clocks are unchanged; only their resetting is removed.

| 16 primary bodies, staged readout | Chain | Matched latch | Latch (raw, no rule) |
|---|---:|---:|---:|
| A-units moved 10+ frames in training (`ρ1 = +1`) | 6 to 9 | **0** in 8/8 | 0 in 8/8 |
| Step one, fraction of Bayes (median) | 0.69 | 0.68 | 0.76 |
| Step two, fraction of Bayes (median) | 0.24 | **0.32** | 0.26 |
| Step two right sign | 13/16 | **16/16** | 16/16 |
| Failing type `(+1,−1)` right sign | 1/4 | **4/4** | 4/4 |
| `ρ1 = +1` step two stronger than chain, paired | — | **8/8** (p = 0.004) | 7/8 |
| Cutting B-units removes step two | 79% | 89% | 83% |
| Reversing B flips step two | 14/16 | 15/16 | 15/16 |

| B → C relation | Chain | Matched latch | Latch (raw) |
|---|---:|---:|---:|
| B copies A, C copies B | 0.15 | 0.28 | 0.33 |
| B copies A, C flips B | −0.11 | **0.15** | 0.10 |
| B flips A, C copies B | 0.35 | 0.33 | 0.24 |
| B flips A, C flips B | 0.43 | 0.40 | 0.35 |

**Against the rule set beforehand, the diagnosis is confirmed** (all five conditions). Every unit in every latched body now fires on exactly the same tick in training as at test (checked: 0 frames for all A- and B-units). The failing type now has the right sign in all four bodies, step two has the right sign in all 16, and the `ρ1 = −1` bodies are essentially unchanged (0.40 to 0.36, inside the 0.1 I predicted).

**What my predictions got wrong.** I expected `ρ1 = +1` step two to reach 0.35 to 0.45 and the median about 0.4; it reached 0.22 and 0.32. Step two stays below half of Bayes, as predicted, so chain/'s second claim (Bayes-like strength) is still **not** shown.

**What is left.** With the clocks identical in training and test, `ρ1 = +1` bodies are still weaker than `ρ1 = −1` (0.22 against 0.36), so the clock was the cause of the sign failures but not of all the weakness. That remainder is not explained. The combination not yet tried is the latch together with Gemini's two fixes, which alone raised step two to 0.43.

The residue version (A-units hear world minus prediction, the apical idea) was tried on development bodies only. It did not stop the reset, because the imagined B is too weak to cancel the real one, so it was not taken to the batch. One post-batch fix is disclosed: `analyze_latch.py` still listed the conditions from before the matched latch was added (`"latch", "residue"`). It was corrected to `"latch_matched", "latch"`. The rule code itself was not touched.

## Reproduce

```sh
python chain/run_chain.py --dev --workers 2   # development seeds, about 1.5 minutes
python chain/run_chain.py --workers 2         # the batch, about 9 minutes on two cores
python chain/analyze_chain.py
python chain/run_fix.py --check               # engine_fix reproduces engine_chain exactly with both fixes off
python chain/run_fix.py --workers 2           # Gemini's fixes, about 20 minutes on two cores
python chain/analyze_fix.py
python chain/clock_diag.py                    # the clock diagnosis on the trained chain bodies
python chain/run_latch.py --check             # engine_latch reproduces engine_chain exactly with options off
python chain/run_latch.py --workers 2         # the latch batch, about 12 minutes on two cores
python chain/analyze_latch.py
```
