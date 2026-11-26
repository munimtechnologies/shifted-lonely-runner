# Pre-registration: route 13, an exact search for one 94-runner counterexample

Written 2026-11-26 (about 16:50 UTC), before any code of this route had run. MV2, Munim, Inc.
Made with AI agents working in MV2's name; no human expert has checked it. Text CC BY 4.0,
code Apache-2.0.

## Question

The shifted Lonely Runner Conjecture is known to fail for 5 <= n <= 57 (Blanco, Criado and
Santos; aadrianvv; tomdif; Lean-checked in 1337isnot1337/solved-conjectures PR 755) and for
n >= 95 (Poliakova, [arXiv:2609.23952](https://arxiv.org/abs/2609.23952)). On 26 November
(about 16:20 UTC: solved-conjectures issue 110 and its pull requests, including the open PR 850;
the arXiv listing newest first) **58..94 is still open**.

Routes 10-12 looked for a uniform local rule, which would cover all n above its threshold at
once. Route 12 showed (RESULTS_rules_f.md) that Poliakova's whole rule cannot be extended to
gain 2 at the same top in our menus. **Route 13 asks a narrower but exact question: is there a
counterexample for n = 94 alone** that modifies the base m, 2m, ..., mN (N = 95, or N = 96 with
gain 2)? Such a counterexample would be the first below Poliakova's 95. It would leave 58..93
open.

At one fixed n the condition is weaker than any uniform rule. It is enough that the OPEN arcs
{t : ||v t + s|| < 1/(n+1)} cover the circle: then gamma(v; s) < 1/(n+1). Here 1/(n+1) is larger
than the base's own radius 1/(N+1), and base runners that are not multiples of a touched speed
help too. aadrianvv reported (issue 110, 21 November) that the base of even speeds with shifts
in a Z/4 menu has no such configuration at n = 94. Bases of multiples of 3, 4 or 6, which put the
added runners at thirds, quarters or sixths, have not been reported.

## Menu and method (`rule_search_g.py`)

- Base: the speeds m j for j = 1..N, shift 0. Every P-smooth base speed may be removed or
  rephased; the others stay.
- Added speeds: P-smooth integers up to 2 m N + 1 that are not multiples of m.
- Shifts: sigma0 + beta/(N+1), with sigma0 in {a/d : d in {1, 2, 3, 4, 6}} and beta in steps of
  1/2 on [-2, 2]. That is 72 shifts. Poliakova's rule is in this menu.
- Runner count: sum(removed) - sum(added) >= N - n. With fewer runners, padding with new speeds
  keeps the cover.
- Decision: CEGAR over time points. For a point t, the clause lists every option whose open
  arc contains t. Candidates come from CP-SAT and are checked exactly. Their uncovered points
  are found three ways: float gaps, exact abutments of arcs, and the exact sweep of `slr.py`.
  Each one adds a clause the candidate violates.
- FOUND: the configuration, padded to exactly n runners, passes both global exact checkers of
  `slr.py` at R = 1/95.
- INFEASIBLE: no configuration of this finite menu exists. It is a proof for that menu only.

| tier | m | n | N | P | role |
|---|---|---|---|---|---|
| g2H | 2 | 95 | 96 | {2,3} | sanity: Poliakova's rule given as a solver hint; must be FOUND |
| g2N | 2 | 94 | 95 | {2,3} | control: halves only (aadrianvv: none in a Z/4 menu) |
| g6N | 6 | 94 | 95 | {2,3,5} | target: halves, thirds, sixths |
| g3N | 3 | 94 | 95 | {2,3,5} | target: thirds |
| g4N | 4 | 94 | 95 | {2,3,5} | target: quarters |
| g6G2 | 6 | 94 | 96 | {2,3,5} | target: gain 2 from N = 96 (compete job only) |

Runs: gate probes G1 (g2H, g2N, g6N), G2 (g6N), G3 (g3N, g4N), about 500 s each with 6 CP-SAT
workers. State is cached, so later probes and runs resume.

## Sanity rules

- S1: `test_rules_g.py` passes. It checks the shift grid by hand values, and that a point's
  clause is satisfied exactly when a random configuration covers that point (random
  configurations on bases of multiples of 2, 4 and 6, against a separate Fraction test). It
  also checks that Poliakova's configuration is a 95-runner cover at radius 1/96 under both
  global checkers, and that it satisfies every seed clause.
- S2: g2H ends FOUND. Otherwise no route-13 result counts.
- S3: no tier reports BUG or ERROR.

## Predictions

- **G-R1.** S1, S2 and S3 hold. **Yes** (75%).
- **G-R2.** The control g2N is decided within the three probes. **Yes** (35%). If decided:
  INFEASIBLE (85%).
- **G-R3.** g6N is decided within the three probes. **Yes** (20%). If decided: INFEASIBLE
  (90%).
- **G-R4.** Some target tier yields a certified 94-runner counterexample. **No** (4% yes).

## Claims policy

A FOUND configuration is claimed only after a scoop check on the day of publishing and a
re-check by a third, fresh checker. A negative covers only the finite menu named. A 94-runner
counterexample would move the open range from 58..94 to 58..93. It would not settle the range.
