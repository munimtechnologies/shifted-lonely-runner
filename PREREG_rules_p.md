# Pre-registration: route 19b, route 19 with a feasibility-only solver

Written 2026-11-27 (about 21:30 UTC), before any code of this route had run. MV2, Munim, Inc.
Made with AI agents working in MV2's name; no human expert has checked it. Text CC BY 4.0, code
Apache-2.0.

## Where the problem stands

The shifted Lonely Runner Conjecture is known to fail for 5 <= n <= 57 (Blanco, Criado and
Santos; aadrianvv; tomdif; Callens; Lean-checked in 1337isnot1337/solved-conjectures PR 755),
for n = 63 (Xavier Callens, [Zenodo 24051700](https://doi.org/10.5281/zenodo.24051700),
unrefereed) and for n >= 95 (Poliakova, [arXiv:2609.23952](https://arxiv.org/abs/2609.23952)).
**Open: 58..62 and 64..94.** Re-checked 27 November about 21:20 UTC: the Zenodo API ("shifted
lonely runner": the same four records, Bonfioli 24189338 and Callens 24132291, 24051700,
23842167; "lonely runner", newest first: 73 records, newest Zhang 24573706 on 26 November,
nothing new on the shifted conjecture), arXiv's newest lonely-runner listings (newest
2610.40694, 28 October), the solved-conjectures pull requests (newest F1Justin's PR 1017, open;
nothing claims n >= 58) and a web search.

## What route 19 showed so far (RESULTS_rules_o.md)

Gate probes O1 and O2 passed every calibration (cal=T cal1=F cal66=T calcert=T pol=T) and
found a gain-1 rule in all three sanity tiers: f96h (Poliakova's setting, N = 96), f64x
(Callens's setting, N = 64, menu x) and, unexpectedly, h64 (N = 64 with halves only). But none
of the 37 targets was decided: each got one to three CEGAR iterations.

The reason is the solver call, not the problem size. `rule_search_c.build_and_solve` minimises
the number of touched speeds, so CP-SAT keeps improving a candidate until its time limit
(20 s, then up to 45 s) instead of returning it. f64x needed 5 iterations in 154 s, about 30 s
each. A counterexample-guided loop only needs some candidate, or a proof that none exists.

## Method (`top_p.py`)

- `solve_feas`: the same model as `build_and_solve` (each touchable speed removed, untouched
  or rephased once; each added odd speed at most once; removed - added >= g; every clause of
  every collected class) **without the objective**, so CP-SAT stops at its first solution.
  INFEASIBLE keeps its meaning: no rule in the finite menu passes `top_o.fixed_check`.
- `cegar_p`: route 19's loop with `solve_feas`; each turn gives the solver all the time left in
  the turn; up to 16 failing classes per touched speed are added per iteration.
- Everything else is route 19's (`top_o.py`): the exact fixed-N closed-cover criterion at the
  slack radius r = 128/(128(n + 1) + 1), the clause builder, menus x and h, and `certify` (both
  global exact checkers of slr.py at R = 1/(n + 1)).
- Tiers: two sanity tiers re-run **from scratch** (pf64x = f64x, ph64 = h64), then the 37 targets
  of route 19 (x64g2 for n = 62; xN, g = 1, for N = 59..95 except 64), seeded with the classes
  route 19 collected for them (cache %TEMP%/mv2-slr-o1; a class's clauses depend only on N, g and
  the menu, so they stay valid). 60 s per turn (sanity 150 s), fewest turns first, 8 workers;
  state in %TEMP%/mv2-slr-p1. Gate probes P1, P2, P3 of 520 s each.
- Report: the route-19 rules for h64 and f64x in full (`OLD` lines) and route 19's final status
  counts (`O1STATE`), one token per tier (`tag:<F|I|U|B><iterations>/<seconds>`), a `PIT` line
  (iterations and mean solver seconds per iteration), then SANE, BUG, RULE, CERT, STATUS last.

## Sanity rules

- S1: `test_top_p.py` passes in the gate (tier tables; report formatting on Callens's rule; a
  feasible and an infeasible hand-made model; on N = 8, g = 1, menu h, a FOUND rule passes both
  global checkers and the old and new solvers never contradict each other).
- S2: pf64x is FOUND within P1-P3 and no tier is BUG. If S2 fails, no INFEASIBLE of this route
  counts.

## Predictions

- **P-R1.** S1 and S2 hold. **Yes** (70%).
- **P-R2.** The mean solver time per iteration (PIT) is below 5 s. **Yes** (70%).
- **P-R3.** x64g2 (n = 62 at N = 64) is decided within P1-P3, and the decision is INFEASIBLE.
  **Yes** (40%).
- **P-R4.** At least 10 of the 37 targets are decided INFEASIBLE within P1-P3. **Yes** (45%).
- **P-R5.** Some target is FOUND and certified, i.e. a counterexample for an open n. **No** (3%
  yes).

## Claims policy

Unchanged from PREREG_rules_o.md. A FOUND target is claimed only after a scoop check on the
day of publishing and a re-check by a fresh third checker in a committed test. INFEASIBLE is
reported as "no rule in this finite menu", never as "no counterexample for n". Credit: the
n = 63 cover and its shifts are Callens's (CC BY 4.0); local rules, their locality proof, the
9 -> 8 rule and E_n are Poliakova's; the CEGAR encoding is route 11's.
