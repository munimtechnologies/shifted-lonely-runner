# Results: route 4 (PREREG_br.md), graded 2026-11-25

By MV2 of Munim, Inc. Made with AI agents working in MV2's name; no human expert has
checked it. Text CC BY 4.0.

## Grades

| prediction | predicted | outcome | evidence |
|---|---|---|---|
| B0a Dirichlet tightness, n = 1..13 | pass | **pass** | `test_slr_br.py` passed in the publish gate; commit [8f16f0c](https://github.com/munimtechnologies/shifted-lonely-runner/commit/8f16f0cab86ff1f4c30a1e2f6e5272c4ec71fc92) |
| B0b float/exact agreement, best-response optimality | pass | **pass** | same commit |
| B1 n = 8 certified | yes (85%) | **yes** | same commit |
| B2 n = 18 certified | yes (45%) | **yes** | `test_slr_br_gap.py` was committed ([d672b79](https://github.com/munimtechnologies/shifted-lonely-runner/commit/d672b79deb527a0ce5b33d0a1710fc3b41ebe6f1)), which the gate allows only if all three cases pass |
| B3 n = 19 certified | yes (40%) | **yes** | same commit |
| B4 n = 20 certified | yes (35%) | **yes** | same commit |

All six predictions came true. Each certificate is speeds 1..n with shifts whose closed arcs of
radius 1/(n+1) - 1/10^11 cover the circle, checked in exact rational arithmetic. The gate
keeps no output for a passing test, so the shifts themselves are not stored yet; they are
regenerated exactly by `python -m unittest -v test_slr_br_gap` (the search is deterministic
for seed 1; the whole gate step for this commit, all three cases included, took about 96
seconds on MV2's machine, judging by the publish log's timestamps).

## Not new: prior result found after the run

These three counterexamples are **not new**. On 2026-11-25, after the gate run, a wider search
found that counterexamples for every **18 <= n <= 54** had already been published on
2026-11-22 by aadrianvv (working with Claude) in
[1337isnot1337/solved-conjectures, results/shifted-lonely-runner-counterexamples](https://github.com/1337isnot1337/solved-conjectures/tree/main/results/shifted-lonely-runner-counterexamples)
(unrefereed; speeds 1..n for n <= 40, other speed sets for 41..54; two exact checks in their
`verify.py`; history in
[issue #110](https://github.com/1337isnot1337/solved-conjectures/issues/110), opened
2026-11-20). MV2's earlier prior-work searches (2026-11-24 and 2026-11-25: the arXiv
listing, web searches, and the code of Blanco, Criado and Santos) missed it because it is
only in a GitHub repository. Route 4 is an independent re-finding of n = 18, 19, 20 by a
different method (best-response dynamics rather than annealing), nothing more.

## What this changes

The open range is now **55 <= n <= 94**. Route 5 (`PREREG_sbr.md`, `slr_sbr.py`) targets it,
starting from the published n = 54 certificate, and also re-checks all 37 published
certificates with MV2's own exact checkers (`test_external_certs.py`).
