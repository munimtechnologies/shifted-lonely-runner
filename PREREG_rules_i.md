# Pre-registration: route 14, fixed-n searches at smooth N with CP-SAT and a scaled hint

Written 2026-11-27 (about 10:10 UTC), before any code of this route had run. MV2, Munim, Inc.
Made with AI agents working in MV2's name; no human expert has checked it. Text CC BY 4.0,
code Apache-2.0.

## Where the problem stands

The shifted Lonely Runner Conjecture fails for 5 <= n <= 57 (Blanco, Criado and Santos;
aadrianvv; tomdif; Lean-checked in 1337isnot1337/solved-conjectures PR 755), for n = 63
(Xavier Callens, [Zenodo 24051700](https://doi.org/10.5281/zenodo.24051700), unrefereed) and
for n >= 95 (Poliakova, [arXiv:2609.23952](https://arxiv.org/abs/2609.23952)). **Open:
58..62 and 64..94.** Checked 27 November about 09:45 UTC: the Zenodo API ("shifted lonely
runner": 4 records, newest Bonfioli 13 Nov; "lonely runner" newest first), the arXiv listing
newest first (newest 2610.40694, 28 Oct), and solved-conjectures pull requests (newest relevant:
F1Justin's PR 850, the 57-runner configuration does not extend to 58 by one added runner).

## Why route 14

Route 13b's SAT solver made no iteration and failed its sanity tier
([RESULTS_rules_h.md](RESULTS_rules_h.md)). Route 13's CP-SAT search did make progress and
re-found Poliakova's rule in one iteration when given it as a hint. Route 14 runs route 13b's
question (smooth N inside the open range, bases other than the even one) with route 13's
CP-SAT CEGAR (`rule_search_g.cegar_g`, unchanged: same menu, point clauses, exact checks and
certification).

## Method (`rule_search_i.py`)

- **Hint.** For even m the solver gets Poliakova's 9 -> 8 rule with every speed multiplied by
  k = m/2. Multiplying every speed of a cover by k keeps it a cover with the same shifts, so at
  N = 96 it is a 95-runner cover on the base m, 2m, ..., 96m (tested exactly in
  `test_rules_i.py` for m = 4 and 6). At smaller N it is only a starting point. A hint cannot
  change what the solver may answer.
- **Turns.** Tiers take turns of 150 s, least-searched first, 3 processes with 2 CP-SAT workers
  each; clauses and time limits are cached between turns and probes.
- FOUND = padded to exactly n runners, both global exact checkers of `slr.py` pass.
  INFEASIBLE = no configuration of the finite menu covers even the points collected (a proof
  for that menu only).

| tier | m | n | N | gain | hint |
|---|---|---|---|---|---|
| s4H | 4 | 95 | 96 | 1 | yes; sanity, must be FOUND |
| e6N72, e4N72, e2N72, e3N72 | 6, 4, 2, 3 | 71 | 72 | 1 | even m |
| e4N80, e2N80 | 4, 2 | 79 | 80 | 1 | yes |
| e3N81 | 3 | 80 | 81 | 1 | no |
| e6N90 | 6 | 89 | 90 | 1 | yes |
| e6N75 | 6 | 74 | 75 | 1 | yes |
| e6N60, e4N60 | 6, 4 | 59 | 60 | 1 | yes |
| e2G64 | 2 | 62 | 64 | 2 | yes |

All tiers use P = {2, 3, 5}. Our m = 2 menu differs from Callens's (his shifts are a/520 at
N = 64; ours are sigma0 + beta/(N+1) with sigma0 in {a/d : d in {1,2,3,4,6}}), so his
negatives at N = 60..63, 65..95 do not cover our m = 2 tiers. Runs: gate probes I1, I2, I3,
520 s each.

## Sanity rules

- S1: `test_rules_i.py` passes in the gate.
- S2: s4H ends FOUND, with both global exact checkers.
- S3: no tier reports BUG or ERROR.
Otherwise no route-14 result counts.

## Predictions

- **I-R1.** S1-S3 hold and s4H is FOUND in its first turn. **Yes** (80%).
- **I-R2.** At least 8 of the 12 e-tiers complete at least 3 CEGAR iterations within I1-I3.
  **Yes** (60%).
- **I-R3.** At least 3 of the 12 e-tiers are decided within I1-I3. **Yes** (30%). Decided
  e-tiers are INFEASIBLE (85% each).
- **I-R4.** Some e-tier yields a certified counterexample for an n that is still open.
  **No** (5% yes).

## Claims policy

A FOUND configuration for an open n is claimed only after a scoop check on the day of
publishing (issue 110 and its pull requests, arXiv, GitHub, Zenodo API) and a re-check by a
third, fresh checker in a committed test. A negative covers only the finite menu named. A new
counterexample would remove one n from the open range; it would not settle the range.
