# Pre-registration: route 13b, fixed-n searches with an incremental SAT solver

Written 2026-11-27 (about 01:40 UTC), before any code of this route had run. MV2, Munim, Inc.
Made with AI agents working in MV2's name; no human expert has checked it. Text CC BY 4.0,
code Apache-2.0.

## Where the problem stands

The shifted Lonely Runner Conjecture fails for 5 <= n <= 57 (Blanco, Criado and Santos;
aadrianvv; tomdif; Lean-checked in 1337isnot1337/solved-conjectures PR 755) and for n >= 95
(Poliakova, [arXiv:2609.23952](https://arxiv.org/abs/2609.23952)). **It also fails for n = 63:**
Xavier Callens (SocrateAI Lab) deposited
[an exact counterexample at n = 63](https://doi.org/10.5281/zenodo.24051700) on Zenodo on
8 November 2026. Its certificate is a Poliakova-type move on the base 2, 4, ..., 128, with
shifts a_i/520 and gamma = 66/4225 < 1/64; three exact checkers and a kernel-checked Lean
statement accept it, with no human audit. The record calls it sporadic: the same menu is
infeasible for N = 60..63 and 65..95. A companion record
([10.5281/zenodo.24132291](https://doi.org/10.5281/zenodo.24132291)) reports a negative,
inconclusive search at n = 39..94. Our README had said "58..94 open" since 24 November; we
missed both records, which issue 110 does not mention either. We found them on 27 November
through the Zenodo API. **Open now: 58..62 and 64..94** (checked 27 November about 01:30 UTC:
solved-conjectures issue 110 and its pull requests, the arXiv listing newest first, GitHub
repositories sorted by update, Zenodo records for "shifted lonely runner").

## Question

Callens's n = 63 uses N = 64, a power of 2. This suggests that fixed-n moves exist for very
smooth N. All published fixed-n searches used the even base (multiples of 2). **Route 13b asks,
for smooth N in the open range, whether a base of multiples of m = 3, 4, 6 (and 2 with gain 2)
has a configuration with n = N - g runners whose open arcs of radius 1/(n+1) cover the circle.**
It also continues route 13's n = 94 tiers ([PREREG_rules_g.md](PREREG_rules_g.md), interim
grading in [RESULTS_rules_g.md](RESULTS_rules_g.md)).

## Method (`rule_search_h.py`)

Same menu, point clauses and exact checks as route 13 (`rule_search_g.py`): touchable base
speeds are P-smooth multiples m j (j <= N); added speeds are P-smooth non-multiples of m up to
2 m N + 1; shifts are sigma0 + beta/(N+1) with sigma0 in {a/d : d in {1,2,3,4,6}} and beta in
halves on [-2, 2]. What changes:

- One **incremental SAT solver** per tier and turn (PySAT: CaDiCaL 1.9.5 if it supports conflict
  budgets in the gate, else Glucose 4). Route 13's CP-SAT rebuilt its model at every iteration
  (g6N: 10 iterations in 733 s).
- Every exactly uncovered point t also adds the clause of **-t**. Each is a necessary condition
  on any cover (the shift menu is closed under negation), so this is sound.
- The runner count is pure CNF: at most one option per base speed and per added speed, and two
  upward sequential counters for #removed - #added >= N - n. A base speed with nothing chosen
  is read as removed, which only raises the gain, so UNSAT stays a proof for the finite menu.
- Tiers take **turns of 160 s**, least-searched first, 6 processes at a time. Clauses are kept
  between turns and probes; route-13 tiers resume from route 13's clauses.
- FOUND = padded to exactly n runners, both global exact checkers of `slr.py` pass.

| tier | m | n | N | gain | role |
|---|---|---|---|---|---|
| g2H | 2 | 95 | 96 | 1 | sanity: Poliakova's rule as solver phases (P = {2,3}); must be FOUND |
| c63 | 2 | 63 | 64 | 1 | second sanity: Callens's n = 63, if it lies in our menu |
| e2G64, e4G64 | 2, 4 | 62 | 64 | 2 | targets: n = 62 |
| e3N81 | 3 | 80 | 81 | 1 | target: n = 80 |
| e6N72, e3N72 | 6, 3 | 71 | 72 | 1 | targets: n = 71 |
| e4N80 | 4 | 79 | 80 | 1 | target: n = 79 |
| e6N90 | 6 | 89 | 90 | 1 | target: n = 89 |
| e6N60, e4N60 | 6, 4 | 59 | 60 | 1 | targets: n = 59 |
| g6N, g3N, g4N, g12N | 6, 3, 4, 12 | 94 | 95 | 1 | route-13 targets (g12N new) |
| g6G2 | 6 | 94 | 96 | 2 | route-13 target |
| g2N | 2 | 94 | 95 | 1 | route-13 control (aadrianvv: none in a Z/4 menu) |

All tiers except g2H use P = {2, 3, 5}. Runs: gate probes H1, H2, H3, 520 s each.

## Sanity rules

- S1: `test_rules_h.py` passes. It checks the counter against exact counts, the whole CNF
  against brute force on 140 random small instances (with a DPLL written in the test), that
  Poliakova's configuration gives a satisfying assignment of the seed encoding of g2H and is
  decoded back exactly, and that the mirror clauses of a broken rule's gap points are satisfied
  by Poliakova's cover.
- S2: g2H ends FOUND, with both global exact checkers.
- S3: no tier reports BUG or ERROR.
- S4: Poliakova's configuration satisfies every clause collected for g2H.
Otherwise no route-13b result counts. c63 is not a sanity rule: Callens's configuration may
use options outside our menu, so a c63 negative would only say that.

## Predictions

- **H-R1.** PySAT installs in the gate and S1-S4 hold. **Yes** (70%).
- **H-R2.** On g6N, route 13b runs at least 5 times as many iterations per second as route 13
  (10 in 733 s). **Yes** (75%).
- **H-R3.** c63 ends FOUND within H1-H3. **Yes** (45%).
- **H-R4.** At least 3 of the 10 e-tiers are decided within H1-H3. **Yes** (40%). Decided
  e-tiers are INFEASIBLE (85% each).
- **H-R5.** Some tier other than g2H and c63 yields a certified counterexample for an n that is
  still open (58..62 or 64..94). **No** (7% yes).

## Claims policy

A FOUND configuration for an open n is claimed only after a scoop check on the day of
publishing (issue 110 and its pull requests, arXiv, GitHub, Zenodo API) and a re-check by a
third, fresh checker. A negative covers only the finite menu named. A new counterexample would
remove one n from the open range; it would not settle the range.
