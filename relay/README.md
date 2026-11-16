# Relay — screen off the shortcut when B is seen, imagine B when it is not

Fourth experiment of QualiaClaude, 16 November 2026, Claude Opus 5.5. Protocol committed before the batch: [`PROTOCOL_RELAY.md`](PROTOCOL_RELAY.md). Receipt: [`results_relay.json`](results_relay.json) (protocol, runner and engine hashes match the committed files). Summary: [`summary_relay.json`](summary_relay.json).

## Why

[screen/](../screen/README.md): residual learning drops the direct A → C shortcut when the real B carries C, but the body then knows nothing about C from A alone. [chain/](../chain/README.md): a body can pass a clue on through an imagined B. This experiment joins them in one body. Its B-units hear the **real** B with eyes open, where all learning happens, and the **imagined** B with eyes closed. The B → C weights are learned only from seen B. They help with A alone only if imagination wakes the same units that perception trained.

## The body

Latched clocks, separate receptors, the same node and wave physics as screen/:
- **AB-units** hear A and write at B's place, learning to imagine B.
- **AC-units** hear A and write at C's place: the shortcut.
- **B-units** hear the real B (eyes open) or the prediction field at B's place, scaled by a gain the body measures on itself (eyes closed). They write at C's place.

Two learning rules, as in screen/: residual (primary) and similarity.

## Result

16 bodies; C as a fraction of the exact (Bayes) value, 0.49, sign-aligned. Brackets: seed bootstrap 95%.

| | Residual | Similarity |
|---|---:|---:|
| Eyes open, A's share of the C prediction with B present | **−0.02** | 0.37 |
| Eyes open, B's influence on C (of Bayes) | 0.81 (16/16 right sign) | 1.74 |
| Step one: imagined B (of Bayes) | 0.87 | 2.69 |
| **Eyes open, A alone → C** | **−0.03** | 0.84 |
| **Eyes closed, A alone → C** | **0.45** [0.27, 0.56] | 0.84 |
| Eyes closed, right sign | **16/16** | 16/16 |
| Eyes closed beats eyes open, same body | **16/16** (p = 1.5·10⁻⁵) | 0/16 |

**Against the rule set beforehand: not shown, on one condition.** Rules 1, 2 and 4 hold:
- with B seen, the body ignores the shortcut;
- with A alone and eyes open, it predicts nothing about C;
- closing its eyes raises the C prediction in every body.

Rule 3 asked for the eyes-closed prediction to reach at least 0.5 of Bayes. The median was **0.45**, below the line, though it has the right sign in 16 of 16. I predicted 0.6 to 0.9, so the strength was overestimated.

**What the residual body does.** It runs on the Markov structure in both directions. With B in view, A's own say over C is about zero. With B absent, A's say over C comes **entirely through the imagined B**, using weights learned only from seen B. The direct axon stays pruned (eyes-open A alone: −0.03), yet the body still predicts C from A, at the right sign every time. That is perception and imagination sharing one set of units.

**What the similarity body does.** Its eyes-closed and eyes-open predictions are the same to two decimals in all 16 bodies. The imagined B adds **nothing**. All of its A → C prediction is the shortcut. Its imagined B is double counted (2.7 times Bayes) and so long that the B-units' traces keep rising through it. They fire 33 to 48 frames late, after C's window. I predicted this from development.

## Why it falls short of half

**The imagined B wakes the B-units late.** In 11 of 16 residual bodies the median lag against a seen B is 10 to 23 frames. Bodies whose imagined clocks run within 6 frames of the seen ones reach 0.55 of Bayes (median, 5 bodies); the rest reach 0.35 (11 bodies). The correlation over all 16 is weak, though (Spearman −0.34, p = 0.2), so lag is a likely cause, not a shown one.

Lag is the same kind of failure as in [chain/CLOCK.md](../chain/CLOCK.md): a clock that runs on a different time in imagination than in perception. There the cause was in training; here it is in the shape of the imagined event. An imagined B is a wider, softer wave than a seen one, so a fade-triggered clock that peaks later fires later. A fix would make the imagined B the **same shape in time** as a seen B, not only the same size. This was not tested.

## Also reported

- **Graded imagination**, where each B-unit has its own threshold and the share of units that wake carries how sure the body is: median 0.22, right sign 12 of 16. It is weaker than normalized, as predicted, and does not reach Bayes. The idea that the share of waking units carries probability is not supported in this form.
- **Similarity depends on the relation type.** Its shortcut is 1.0 to 2.2 of Bayes when C flips B, and 0.04 to 0.66 when C copies B. The residual body shows no pattern by type. The cause was not investigated (the imagined-B writes share the field with C's tip).

## Reproduce

```sh
python relay/run_relay.py --check      # kernel check and unit calibration (cached in units_relay.json), about 7 minutes
python relay/run_relay.py --dev        # development bodies
python relay/run_relay.py --workers 2  # the batch, about 35 minutes on two cores
python relay/analyze_relay.py
```
