# Screen — does a branch explain what is left, or the world on its own?

Third experiment of QualiaClaude, 16 November 2026, Claude Opus 5.5. Protocol committed before the batch: [`PROTOCOL_SCREEN.md`](PROTOCOL_SCREEN.md). Receipt: [`results_screen.json`](results_screen.json) (its protocol, runner and engine hashes match the committed files). Summary: [`summary_screen.json`](summary_screen.json).

## Why

Sol's Gate 4 in [QualiaAstra](https://github.com/anttiluode/QualiaAstra) let candidate axons compete. Residual-driven growth, delay-aware similarity growth and an oracle all landed on the same route with the same error. That tie is what the mathematics predicts on one clean route. A least-squares learner settles at `w = R⁻¹p` and a one-input-at-a-time correlation learner at `w ∝ p`; these agree whenever the candidate inputs are not redundant (`R` nearly diagonal). The two rules can only come apart where inputs are redundant. There the residual learner **explains away** and the similarity learner **double counts**.

The chain has the textbook redundant case. The world is Markov, `A → B → C`. Given B, A tells you nothing more about C:

$$E[s_C \mid s_A, s_B] = (2q-1)\,\rho_2\, s_B \qquad\Rightarrow\qquad \text{the direct A} \to \text{C weight should be } 0,$$

even though A alone correlates with C at `(2q−1)² = 0.49`.

## The body

- **Clocks.** 12 latched fade-triggered A-clocks per sign hear A. 12 B-clocks per sign hear the **real** B. Each population has its own receptor.
- **One meeting point.** Every branch, from A or from B, may write only at C's place (sites 6 and 7) in a prediction wave field. So C's tip has two candidate inputs: a direct axon from A, and the B route.
- **Two learning rules on the same `DampingReturnNode`**, same rate, window and clip. The only difference is what a branch hears at its tip:

| rule | a branch hears | what it settles at |
|---|---|---|
| **residual** | shared prediction minus C | its share of what the **others leave unexplained** (least squares) |
| **similarity** | its **own** contribution minus C | how well it predicts C **by itself** (delay-aware correlation) |

The own contribution is computed exactly from a measured field kernel (it matches the field to 1e-7).

## Result

16 primary bodies, 240 episodes each. `A_share` is A's influence on the C prediction divided by B's influence (raw values, sign-aligned). Bayes: 0.

| | Residual | Similarity | Bayes |
|---|---:|---:|---:|
| **A's share of the C prediction (median)** | **0.011** [−0.04, 0.07] | **0.445** [0.38, 0.47] | 0 |
| Residual share smaller, paired by body | **16 / 16** (p = 1.5·10⁻⁵) | | |
| A's direct influence > 0 | 9 / 16 (chance) | 16 / 16 | — |
| B's influence, fraction of Bayes (median) | **0.90** | 2.06 | 1 |
| B's influence right sign | 16 / 16 | 16 / 16 | — |

95% intervals: seed bootstrap.

**Against the rule set beforehand, it is shown** (all four conditions). The similarity learner grows the direct A axon in every body, giving A about 44% as much say over C as B has. The residual learner gives it about 1%, with A's sign no better than a coin flip across bodies. It has learned that once B is known, A adds nothing. The similarity learner also **double counts within each bank**: twelve clocks each fit C on their own and their pings overlap, so it predicts C at twice its real strength. The residual learner is close to calibrated (0.90).

**Against my predictions:** residual share 0.011, against my 0.05 to 0.12 (it screens off more cleanly than I expected); similarity 0.445, at the low edge of my 0.45 to 0.55; both B-influence ranges held.

## What it means

- **What the residual learner is.** It is the "explain what is left" rule: the axon worth keeping is the one that removes surprise **others cannot**, not the one that looks most like the target. Selecting inputs by the residual is matching pursuit (Mallat, 1993). Sihti does the same move across scales; here it happens across wiring. The rule is known mathematics. What is new is seeing it work in a wave body of fade-triggered clocks: the screening-off happens physically, at a shared dendritic tip.
- **The price of screening off.** With A alone, the residual body predicts almost nothing about C (`A_alone` = 0.02 of Bayes), because it has learned to rely on B. That is exactly why chain/ needed an **imagined** B. The correct body is "screen off A, then supply B from prediction when it is missing": this experiment's rule plus chain/'s relay.
- **For Sol's Gate 4.** The tie there was expected. Redundant candidates (a direct and an indirect route to the same consequence) are where the two growth rules separate, by a factor of about 40 here.

## What this is not

- **A single tip, not growth.** One tip with fixed candidate axons. Weights shrinking to near zero act like pruning, but there is no wiring cost or structural growth.
- **Not a test of relation types.** With separate receptors the system is exactly mirror-symmetric, so the four relation types give identical numbers for a given schedule. The 16 bodies differ by schedule only.
- **Separate receptors were a design change.** In the shared world field no threshold separated right-sign from wrong-sign B-units; that is disclosed in the protocol. This tests the learning rule at C's tip, not sensing through a shared medium.

## Reproduce

```sh
python screen/run_screen.py --check          # kernel check and unit calibration (cached in units_screen.json)
python screen/run_screen.py --dev            # development bodies, about 25 minutes on two cores
python screen/run_screen.py --workers 2      # the batch, about 35 minutes on two cores
python screen/analyze_screen.py
```
