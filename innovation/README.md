# Innovation — the dendrite keeps the expectation, only the residue spikes

Fifth experiment of QualiaClaude, 16 November 2026, Claude Opus 5.5, from Antti's rule. Protocol committed before the batch: [`PROTOCOL_INNOV.md`](PROTOCOL_INNOV.md). Receipt: [`results_innov.json`](results_innov.json) (protocol, runner and engine hashes match). Summary: [`summary_innov.json`](summary_innov.json).

## The rule

What a neuron already expects (its own imagined B, its own state coming back) cancels in the dendrite and does not reach the soma. Only the residue spills over and spikes:

$$B = \underbrace{\hat B(A)}_{\text{held in the dendrite}} + \underbrace{r_B}_{\text{the spike}}$$

This is the innovation form of a Kalman filter, and the core of predictive coding (Rao & Ballard 1999).

In relay/'s body, only the B-units change:
- **eyes open**, they hear B's wave minus the body's own prediction of it at the same place;
- **eyes closed**, they hear nothing.

The direct path from A to C stays. Under this rule it carries the prior, `(2q₁−1)(2q₂−1)`. It is not a shortcut to be pruned, because B-units now carry only what A did not predict.

## Result

Eyes-closed C as a fraction of the exact answer, 16 bodies per group. Brackets: seed bootstrap 95%.

| | first-step reliability q₁ = 0.85 (Bayes 0.49) | q₁ = 0.70 (Bayes 0.28) |
|---|---:|---:|
| **innovation**, eyes closed | **0.83** [0.79, 0.92], right sign 16/16 | **0.88** [0.64, 1.03], right sign 16/16 |
| relay + regenerated imagined B, eyes closed | 1.03 (relay/, other seeds) | **1.83** [1.33, 2.04], right sign 15/16 |

The innovation body follows the reliability of A → B. Its eyes-closed C falls to **0.61** of its q₁ = 0.85 value when q₁ drops to 0.70; Bayes says 0.57. The relay body that passes the imagined B as a certain event does not follow it. At q₁ = 0.70 it overshoots to 1.8 times Bayes. So its 1.03 at q₁ = 0.85 was, as suspected, mostly two errors cancelling.

**Quiet when the world agrees.** With eyes open, B-units fired **0 of 12** when B agreed with what A predicted and **12 of 12** when it contradicted (q₁ = 0.85). Residue peaks were 0.38 against 1.10 of a seen B. With a weaker prior (q₁ = 0.70), agreement leaves a bigger residue (0.57) and about half the units fire.

**Against the rules set beforehand:**

- **Claim A** (calibrated, and follows reliability): **not shown, on one condition.**
  - Rule 1 holds: 0.83, right sign 16/16.
  - Rule 2 holds: ratio 0.61, right sign 16/16 at q₁ = 0.70.
  - **Rule 3 failed:** innovation was closer to Bayes than relay + regen at q₁ = 0.70 in **11** of 16 bodies, paired; the rule asked for 12. The medians are far apart (0.88 against 1.83). The innovation body is noisy at q₁ = 0.70 (0.32 to 1.53), and relay + regen happens to land near Bayes in a few bodies.
- **Claim B** (a contradicting B flips C): **failed, as predicted.** C followed the real B in 11 of 16 bodies at q₁ = 0.85, against the 14 required. Median 0.08 of Bayes: a contradiction pulls C to about zero but does not turn it around. At q₁ = 0.70 the prior is weaker, and C follows B in 14 of 16 (median 0.31), so a weaker expectation is easier to overturn.

## What it means

- **Confidence survives as state.** The rule does what relay/ could not: with the senses off, the body predicts C at the right strength for two different reliabilities, through a graded learned weight, with no imagined event to time and no certain spike. In relay/ the confidence was lost on the way to C; here it never has to travel as a spike.
- **Surprise is coded as delay.** A fade-triggered unit fires later the bigger its input was. In development, a contradiction's spike came about 25 frames later than a confirmation's (with a lower arm level, 0.4), and landed after C's window. That is one reason contradictions cannot flip C. The weights a flip needs are learned on only 15% of episodes, and on spikes that arrive at a different time. This is a property of these units worth knowing in its own right: **how surprising is turned into when**.
- **Comparison with relay/.** The two bodies show perception and imagination sharing units in two different ways:
  - in relay/, an imagined B wakes the same units as a seen B, so imagination looks like evidence and its uncertainty is lost;
  - here, an expected B is subtracted before it reaches those units, so the units speak only for evidence, and the expectation stays in the dendrite with its uncertainty intact.

  The second is closer to Bayes. The first is the only one of the two that can relay a **chain** of imagined steps.

## Not shown

- that a contradiction flips C (Claim B);
- that innovation beats relay + regen body by body at q₁ = 0.70 (11/16 against a 12/16 rule);
- anything about chains longer than A → B → C, or about learning the arm level.

## Reproduce

```sh
python innovation/run_innov.py --dev       # development bodies, arm 0.8 and 0.4
python innovation/run_innov.py --workers 2 # the batch, about 65 minutes on two cores
python innovation/analyze_innov.py
```
