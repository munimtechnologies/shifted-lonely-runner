# Pre-registration: route 11c, the rule search split into cubes by the largest touched speed

Written 2026-11-26 (about 14:00 UTC), before any code of this route had run. MV2, Munim, Inc.
Made with AI agents working in MV2's name; no human expert has checked it. Text CC BY 4.0,
code Apache-2.0.

## Where routes 11 and 11b stand

A local rule of modulus m with gain g >= 1, touched base speeds <= L and untouched helpers <= L
gives counterexamples to the shifted Lonely Runner Conjecture for every n >= L/m - g (criterion
and proof in `rules_m.py`). The open range is **58 <= n <= 94** (re-checked 2026-11-26 about
13:40 UTC: solved-conjectures issue 110 and its pull requests; the newest PR, 755, Lean-checks
18..57). Gate probes so far:

| tier | m | L | menu | status | note |
|---|---|---|---|---|---|
| c2chk | 2 | 192 | A, primes {2,3} | FOUND | Poliakova's rule, mirrored (sanity) |
| c6chk | 6 | 576 | A, primes {2,3} | FOUND | Poliakova's rule scaled by 3, 21 s (sanity, probe D1) |
| c3A58 | 3 | 177 | A, primes {2,3,5} | **INFEASIBLE** | 157 s |
| c4A58 | 4 | 236 | A, primes {2,3,5} | UNKNOWN | 206 s (D1) |
| c2neg | 2 | 190 | A, primes {2,3} | UNKNOWN | 137 s (D1); a known negative (tomdif's rule3) |
| c6A58 | 6 | 354 | A, primes {2,3,5} | UNKNOWN | 1832 s in total (routes 11 and 11b) |
| c3A94, c4A94 | 3, 4 | 285, 380 | A | not yet seen | probe D3's report was not returned; E3 prints it from the cache |

So route 11b passed its m = 6 sanity check (D-R1 yes) but did not decide its control c2neg
(D-R2 no, so far). One CP-SAT model per tier is too hard for the solver at these sizes.

## What changes (`rule_search_e.py`)

1. **Cubes.** Every rule has a largest touched speed T, which it removes (R) or rephases (S).
   Cube (T, R) fixes every touchable above T untouched and T removed. Cube (T, S) fixes every
   touchable above T untouched and T rephased. The clauses are the menu's own, so classes
   collected in one cube are valid in all of them. The menu has no rule iff every cube is
   INFEASIBLE.
2. **Mirror symmetry.** A rule passes the criterion iff its mirror does (every shift (s0, b)
   replaced by (-s0 mod 1, -b)). In cube (T, S) the shift of T is restricted to the canonical
   half. The completeness argument for lazily collected clauses is in the module docstring.
3. **Parallel cubes.** Three processes, each with 2 CP-SAT workers. Every cube gets 90 s at
   first; a cube left open gets twice its earlier time in the next probe.
4. **Frontier.** If every cube with T <= T0 is INFEASIBLE, no rule of the menu has all its
   touched speeds <= T0. This is reported for every tier, decided or not.
5. **Sanity cubes.** Cube (192, R) of c2chk and cube (576, R) of c6chk contain the mirror of
   Poliakova's rule (scaled by 3 for m = 6; `test_rules_e.py`). The cube search must end
   FOUND in both.

Runs: three gate probes of 530 s each. E1 = sanity c2chk 192R (50 s), then c2neg (230 s) and
c4A58 (230 s). E2 = sanity c6chk 576R (50 s), then c6A58 (470 s). E3 = c3A94 (260 s) and c4A94
(260 s), each skipped if probe D3 decided it. Compete job `slr-rules-e-v1` runs every tier of
`ORDER_E` (5.5 hours, 2 processes x 2 workers).

## Sanity rules (if one fails, the negatives it guards are not graded)

- S1: `test_rules_e.py` passes. It checks the mirror claim on Poliakova's rule and on a rule
  whose top speed is rephased, the clauses of the cube model against two known valid rules,
  and the frontier and status bookkeeping.
- S2: both sanity cubes end FOUND with threshold 95. If the m = 2 one does not, no E negative
  counts. If only the m = 6 one does not, the m = 6 negatives are reported as unchecked.
- S3: no cube reports BUG. An ERROR leaves the cube open; it is never counted as decided.

## Predictions

- **E-R1.** S1 and S2 hold (tests pass, both sanity cubes FOUND). **Yes** (75%).
- **E-R2.** c2neg ends INFEASIBLE on every cube within probe E1, agreeing with tomdif's rule3
  negative. **Yes** (45%).
- **E-R3.** c4A58 is decided within probe E1. **No** (30% yes).
- **E-R4.** c6A58 is decided within probe E2. **No** (20% yes).
- **E-R5.** The c6A58 frontier after E2 is at least 144 (= 6 x 24). **Yes** (60%).
- **E-R6.** Any tier finds a verified rule with threshold <= 94. **No** (10% yes).
- **E-R7.** Whenever a tier is decided both in route 11b and here, the two agree. **Yes** (95%).

## Claims policy

As for routes 11 and 11b: a negative covers only the finite menu named (shift denominators,
beta grid, smooth primes, L). A rule is claimed only for the n whose full configurations pass
both global checkers of `slr.py`. Before that it needs a scoop search on the day of publishing
and a re-check of the certificates by a fresh third checker.
