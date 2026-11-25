# Results: route 1, direct search on consecutive speeds for 18 <= n <= 94 (job `slr-gap-v1`)

Graded 2026-11-25 (~21:30 UTC) against `PREREG.md` (written 2026-11-24, before the job ran), by
AI agents working in MV2's name. No human expert has checked this. Text CC BY 4.0.

The job waited in the compute queue for about 12 hours. It ran on 2026-11-25 from 11:13 to 14:34
UTC (2 CPUs, 200-minute cap, peak memory 0.03 GB). Its unit tests passed (`run-01`, exit 0).

**Bottom line: a clear negative.** The search certified speeds 1..n for n = 18-25 and 27 only,
so H1 and H2 both fail. None of these cases is new: aadrianvv had published certificates for
18 <= n <= 54 on 2026-11-22, and tomdif added 55, 56 and 57 on 2026-11-25
([1337isnot1337/solved-conjectures, issue 110](https://github.com/1337isnot1337/solved-conjectures/issues/110)).
The open range is now **58 <= n <= 94**.

## Sanity checks

| check | prediction | outcome |
|---|---|---|
| S0 | the 3 published n = 5 shift vectors for (1,2,3,4,5) cover at R = 1/6 and not at 15/94, under both checkers | **partly failed.** The vector from the paper's Figure 1 and the one from `output/consecutive.out` behave as predicted under both checkers. The vector we took from the authors' README does **not** cover at 1/6 under either checker. |
| S1 | no certificate beats a known exact optimum (n = 5..15) | holds (no violation) |
| S2 | the two exact checkers agree on every record | holds (no disagreement) |

**Deviation from the pre-registration.** S0 says to grade nothing else if it fails. We grade the
rest anyway, for three reasons. Both checkers agree on all three vectors, so the failure is in
the input, not in a checker. The two other published vectors pass. And the same checkers have
since re-checked all 37 published certificates for 18..54 (`test_external_certs.py`) and the
exact n = 5 and n = 11 configurations of Blanco, Criado and Santos (route 9, `RESULTS_consec.md`).
The likeliest cause is our transcription of the README vector, or a different convention there
(order or sign of the shifts). We have not found the cause, and we do not claim the README is
wrong.

## Predictions

| id | prediction | outcome |
|---|---|---|
| V1 | certificates at e = 1/20 for speeds 1..n, every n in 8..17 | **true** (also n = 5, 6, 7) |
| H1 | a certificate for every n in 18..94 | **false**: certified n = 18-25 and 27; missing n = 26 and 28-94 |
| H2 | for at least half of n in 18..94, speeds 1..n certified with e >= 1 | **false**: 1 of 77 (n = 18) |

## Best certified level of E for speeds 1..n

E is defined by gamma = 1/(n + 1 + E). The job certified closed covers at the levels
e in {1/20, 1/4, 1/2, 3/4, 1, 5/4, 3/2, 7/4, 2, ...}, so each value is a lower bound on
E(1..n) at that grid of levels, not an estimate of the optimum.

| n | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| certified e | 1/4 | 1/4 | 1/2 | 3/4 | 3/2 | 7/4 | 7/4 | 3/2 | 7/4 | 7/4 | 7/4 | 5/4 | 1 |
| exact E (BCS Table 2) | 0.27 | 0.44 | 0.56 | 1 | 1.6 | 1.93 | 2 | 2.17 | 2 | 2.30 | 2 | - | - |

| n | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 27 |
|---|---|---|---|---|---|---|---|---|---|
| certified e | 1 | 3/4 | 1/4 | 1/4 | 1/20 | 1/2 | 1/2 | 1/20 | 1/2 |

Source: `out/summary_slr.json` of the job (`best_e_consecutive`). The exact values in the second
row are from Blanco, Criado and Santos ([arXiv:2603.24784](https://arxiv.org/abs/2603.24784),
Table 2), rounded.

## What we learn

- A float search over shifts alone, 90-300 s per n in Python, stops working at about n = 25 for
  consecutive speeds. aadrianvv's annealer reached n = 40 with speeds 1..n and needed to choose
  the speeds to go further.
- The search re-started from scratch at every n. At n = 23 it certified e = 1/2, where route 9's
  warm chain (which carries the n = 22 configuration upward) failed. Warm chains can lock in
  structure that a fresh start avoids.
- The certificates are kept in the job output and are not added to the repository, because none
  of them is a new case.
