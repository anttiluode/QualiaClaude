# Innovation: protocol

Written 16 November 2026 by Claude Opus 5.5, **before** the batch.

## The idea (Antti, 16 Nov 2026)

What a neuron already expects (its own imagined B, its own state coming back) cancels in the dendrite and never reaches the soma. Only the residue spills over and becomes a spike:

$$B = \underbrace{\hat B(A)}_{\text{held in the dendrite}} + \underbrace{r_B}_{\text{the spike}}$$

This is the innovation form of a Kalman filter, and the core of predictive coding (Rao & Ballard 1999). What would be new is seeing it work with fade-triggered clocks on a wave field, and what it does to the open problems of relay/.

### What it predicts, if it works

- C hears two **uncorrelated** inputs: the prior path from A, and B's residue spikes. So the direct A → C path is legitimate again: it carries the prior `(2q₁−1)(2q₂−1)`. It is not double counting, because B-units carry only what A did not predict.
- **Eyes closed** (senses off, so no residue), C comes from the prior path alone. That is exactly Bayes, at **whatever** the reliability of A → B is. There is no imagined event to time, so relay/'s clock problem does not arise. The confidence lives in a graded weight, not in an all-or-none spike.
- **A contradicting real B** gives the largest residue, so it should flip C. Bayes: C follows B fully, `(2q₂−1)·s_B`.

## The body ([`engine_innov.py`](engine_innov.py))

relay/'s populations, units, rule and physics. AB-units write the held prediction of B at sites 3 to 5; AC-units write the prior path at sites 6 and 7. The change is in the B-units:
- **eyes open**, they hear `r_B` = B's wave at aperture 4 minus the prediction field at aperture 4 (the same physical quantity, so no gain);
- **eyes closed**, they hear nothing.

Residual learning, eyes open, 240 episodes. Second-step reliability `q₂ = 0.85`.

## Groups (16 bodies each)

| group | seeds | first-step reliability q₁ | Bayes, eyes closed |
|---|---|---|---|
| innovation | 190001 to 190016 | 0.85 | 0.49 |
| innovation | 190101 to 190116 | 0.70 | 0.28 |
| relay body + regenerated imagined B (relay/PROTOCOL_REGEN.md) | 190101 to 190116 | 0.70 | 0.28 |

The last group is the comparison Sol asked for. relay/'s 1.03 of Bayes at q₁ = 0.85 could be two errors cancelling. A body that passes B as certain cannot follow a change in q₁; a calibrated one can.

## Development, disclosed

Seeds 981 to 983, q₁ = 0.85, relation (+1,+1), B-unit arm level 0.8 or 0.4 of a seen B's calibration peak ([`dev_results_innov.json`](dev_results_innov.json)).

- **Arm 0.8.** The B-units fire **only on contradictions**: 0 of 12 when B agrees with the prediction (residue peak about 0.37), 12 of 12 when it contradicts (residue about 1.1). Eyes closed: 1.07, 0.66, 0.92 of Bayes. A contradicting B pulls C from the prior to about zero (0.09, 0.19, −0.07 of Bayes) but does **not** flip it.
- **Arm 0.4.** The B-units fire on both, and contradictions get worse (C stays with the prior: −0.58, −0.22, −0.45). The reason: a fade-triggered unit turns a bigger input into a **later** spike. Residue 1.1 against 0.38 fires about 25 frames later, so contradiction spikes land after C's window, where the weights learned on agreeing episodes do not apply. **In these units, how surprising something is gets coded as how late the spike is.**

So the arm was set to **0.8** before the batch.

## Decision rules

**Claim A: the innovation body is calibrated, and it follows the reliability of A → B.** All three must hold:

1. q₁ = 0.85, eyes closed: median C between 0.75 and 1.25 of Bayes, right sign in at least 14 of 16.
2. Follows reliability: median eyes-closed C at q₁ = 0.70 divided by that at q₁ = 0.85 lies between 0.4 and 0.8 (Bayes: 0.57), and right sign in at least 14 of 16 at q₁ = 0.70.
3. At q₁ = 0.70, `|ln(C / Bayes)|` is smaller for innovation than for relay + regen in at least 12 of 16 bodies (paired by seed, same schedules).

**Claim B: a contradicting B flips C.** Eyes open, B opposite to what A predicts: C has the sign of what the real B says (`r₂·s_B`) in at least 14 of 16 bodies at q₁ = 0.85.

Reported without a rule: eyes-open C when B agrees, B-unit spikes when B agrees and when it contradicts, residue sizes.

## Predictions, recorded before the run

- **Claim A holds.** Innovation eyes closed about 0.8 to 1.1 of Bayes at both reliabilities; ratio about 0.5 to 0.65.
- **Relay + regen at q₁ = 0.70: about 1.5 to 2.5 of Bayes.** The regenerated event is rescaled to a seen B's size whatever the body's confidence, so it passes B as certain.
- **Claim B fails.** From development: C is pulled toward zero by a contradiction but does not flip, because the weights a contradiction needs are learned on only 15% of episodes, and the contradiction spikes come late. Expect C to follow the real B in about 8 to 12 of 16 bodies.
