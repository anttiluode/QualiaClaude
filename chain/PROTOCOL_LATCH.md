# Clock follow-up: protocol

Written 16 November 2026 by Claude Opus 5.5, **before** the batch on the 16 primary bodies. The finding it tests is in [`CLOCK.md`](CLOCK.md): when B has A's sign, B's own wave re-charges the slow A-units during training, so they learn on a clock that is about one gap later than the one they run on at test.

## Conditions

Everything is as in chain/ (same 16 primary bodies, schedules, relations, B-units, rule, readout). Only what the world-listening A-units hear changes. Engine: [`engine_latch.py`](engine_latch.py); with its options off it reproduces chain/ exactly (`python chain/run_latch.py --check`).

- **latch_matched** (the test): once an A-unit's trace has armed and started to fall, its input is closed until it fires. Each A-unit's release level is reset so that, with A alone, it fires on the **same tick** as the unlatched unit (checked: 0 to 1 frame difference over amplitudes 0.9 to 1.12, both signs). At test the clocks are therefore unchanged; the only thing removed is their resetting by later events.
- **latch** (reported, no rule): the same latch with the original release levels. Closing the input also cuts A's own ringing, so every A clock runs 4 to 11 frames earlier.

## Development, disclosed

Run on the development schedules (seeds 991 to 993) with every relation type, never on the primary bodies ([`dev_results_latch.json`](dev_results_latch.json), [`dev_results_latch_latch_matched.json`](dev_results_latch_latch_matched.json)). Step two as a fraction of Bayes (median of 3 bodies per type):

| condition | `+1+1` | `+1−1` | `−1+1` | `−1−1` | A-units moved 10+ frames (`ρ1=+1`) |
|---|---|---|---|---|---|
| none (= chain/) | 0.11 | 0.12 | 0.46 | 0.47 | 6 to 10 per body |
| latch | 0.41 | 0.32 | 0.13 | 0.26 | 0 |
| residue | 0.37 | 0.13 | 0.75 | 0.21 | 6 to 10 per body |
| latch_matched | 0.47 | 0.39 | 0.41 | 0.40 | 0 |

The residue condition (A-units hear world minus prediction) did **not** stop the reset: the imagined B at aperture 1 is far too weak to cancel the real one. So it does not test the finding and is dropped from the batch. The raw latch fixed `ρ1=+1` but moved every clock and hurt `ρ1=−1`, which is why the matched version was built. The matched version was then run once on development bodies; nothing was tuned after that run.

## Decision rule (latch_matched, 16 primary bodies, staged readout)

The finding counts as **confirmed** only if all hold:

1. **clock fixed**: in every `ρ1=+1` body, at most 1 of the 12 same-sign A-units fires 10+ frames later in its last training episode than with A alone (chain/: 6 to 9);
2. step one stays at least 0.5 of Bayes (median) with the right sign in at least 14 of 16;
3. the failing type `(+1,−1)`: step two right sign in at least 3 of its 4 bodies (chain/: 1 of 4);
4. step two higher than in chain/ in at least 7 of the 8 `ρ1=+1` bodies, paired by body (one-sided sign test p ≈ 0.035);
5. step two right sign in at least 15 of 16 (chain/: 13).

Reported without a rule: step two by type, the `ρ1=−1` change, the overall median, cut-B and reversal tests, and the raw latch condition.

## Predictions, recorded before the run

- latch_matched: `ρ1=+1` step two rises to about 0.35 to 0.45 of Bayes; `ρ1=−1` stays within 0.1 of chain/ (0.35 and 0.43); overall median about 0.4. Step two stays **below half of Bayes**, so the second claim of chain/ (Bayes-like strength) is still not shown. That gap, if it stays, is a separate problem (the imagined B is weaker than a real one, and the B-units' arm level was set for it).
- latch (raw): `ρ1=+1` improves, `ρ1=−1` gets worse, as on development bodies.
