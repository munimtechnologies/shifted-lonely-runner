# Pre-registration: route 16, continuous local search around the two structured covers

Written 2026-11-27 (about 15:40 UTC), before any code of this route had run. MV2, Munim, Inc.
Made with AI agents working in MV2's name; no human expert has checked it. Text CC BY 4.0,
code Apache-2.0.

## Where the problem stands

The shifted Lonely Runner Conjecture fails for 5 <= n <= 57 (Blanco, Criado and Santos;
aadrianvv; tomdif; Callens for 18..38; Lean-checked in 1337isnot1337/solved-conjectures PR 755),
for n = 63 (Xavier Callens, [Zenodo 24051700](https://doi.org/10.5281/zenodo.24051700),
unrefereed) and for n >= 95 (Poliakova, [arXiv:2609.23952](https://arxiv.org/abs/2609.23952)).
**Open: 58..62 and 64..94.** Re-checked 27 November about 15:30 UTC: the Zenodo API
("shifted lonely runner": the same 4 records, newest Bonfioli 13 Nov; "lonely runner" newest
first: Zhang 26 Nov, our own lonely-runner-16 archive 27 Nov, nothing on shifted covers), the
arXiv listing newest first (newest 2610.40694, 28 Oct), and solved-conjectures pull requests
(newest F1Justin's PR 1017, open, 27 Nov: the fixed 57 runners plus any seven extra runners
leave an uncovered time at radius 1/59).

## Why a new route

Route 15 (PREREG_rules_j.md) asked, exactly and over a finite menu of shifts, whether the
neighbours of Callens's 63-runner cover and Poliakova's 95-runner cover still cover after one
or two deletions (n = 62, 61, 94, 93) or one addition (n = 64). Both sanity tiers re-found
covers, but CP-SAT decided none of the five targets in two gate probes (RESULTS_rules_j.md).
Route 16 asks the same neighbour question with a heuristic that can move every shift
continuously and swap speeds. It can only find covers; it cannot rule them out.

## Method (`descent_k.py`)

- Shifts are real numbers. Each sweep re-tunes every runner in random order to its exact best
  response (`slr._best_shift`: the shift that covers the largest measure of what the other
  runners leave open), at radius R (1 - 10^-7), R = 1/(n+1).
- When two sweeps in a row stop improving: with probability 1/2 try a speed swap (6 random
  runners times 48 random unused speeds up to twice the source's largest speed, each with its
  best shift; accepted only if the uncovered measure falls), otherwise kick 2-12% of the
  shifts of the best configuration to random values.
- A float cover is accepted only if exact checker A passes on the shifts rounded to 1/2^48;
  then the shifts are rounded to the smallest denominator in a fixed list that still covers,
  padded to exactly n distinct speeds, and both exact checkers of `slr.py` must pass
  (`descent_j.certify_j`).

| tier | start | n | radius |
|---|---|---|---|
| cC63 | Callens's 63 speeds, every shift random (calibration: a cover exists) | 63 | 1/64 |
| kC62 | Callens's cover minus the runner whose deletion leaves the least uncovered measure | 62 | 1/63 |
| kC61 | Callens's cover minus two runners, deleted greedily the same way | 61 | 1/62 |
| kC64 | Callens's cover plus the best single added runner (speed <= 256) | 64 | 1/65 |
| kP94 | Poliakova's cover minus the best single deletion | 94 | 1/95 |

Each tier runs in its own process for the whole probe (gate probes K1, K2, K3, 520 s each) and
resumes from its cached best configuration. Each report also prints route 15's cached state
(line `R15`), which grades route 15.

## Sanity rules

- S1: `test_descent_k.py` passes in the gate (it includes an easy cover that must be found and
  checked, a case where no cover exists that must not be reported, and an exact certificate
  of Poliakova's cover).
- S2: no tier reports ERROR or BUG.
Otherwise no route-16 result counts.

## Predictions

- **K-R1.** S1 and S2 hold. **Yes** (85%).
- **K-R2.** The calibration tier cC63 re-finds a cover at radius 1/64 within K1-K3. **No**
  (30% yes). If it does not, a failure in the target tiers says little about whether covers
  exist.
- **K-R3.** In kC62 the best uncovered measure after K3 is at most one tenth of its start value
  m0. **Yes** (55%).
- **K-R4.** Some target tier yields a certified counterexample for an open n. **No** (3% yes).

## Claims policy

A FOUND configuration for an open n is claimed only after a scoop check on the day of
publishing (Zenodo API, solved-conjectures pull requests, arXiv, GitHub, web) and a re-check by
a fresh third checker in a committed test. A tier that ends without a cover proves nothing;
only its best uncovered measure is reported. Credit: the n = 63 cover is Callens's (CC BY 4.0,
transcribed from `cert_n063.json` of his AutoevolveAI repository); the 95-runner cover is
Poliakova's; best-response search with speed swaps and kicks follows aadrianvv's methods
(routes 4-8 of this repository); bounding extensions of a fixed cover is F1Justin's idea
(PR 850, PR 1017).
