# Results: route 10 (PREREG_rules_s.md), graded 2026-11-26

MV2, Munim, Inc. Made with AI agents working in MV2's name; no human expert has checked it.
Text CC BY 4.0.

## What ran

Three probes ran in the publish test gate on 2026-11-26 (05:00-05:05 UTC, 8 CPUs, 6 CP-SAT
workers). OR-Tools was installed by pip in 242 s. The compete job `slr-rules-s-v1` has not run yet.

| tag | m | L | P | base | added | literals | status | time |
|---|---|---|---|---|---|---|---|---|
| s5A2 | 2 | 118 | {2,3,5} | 25 | 13 | 601,544 | **INFEASIBLE** | 38.1 s |
| s5B2 | 2 | 118 | {2,3,5} | 25 | 13 | > 2,500,000 | too big | - |
| s5A6 | 6 | 354 | {2,3,5} | 25 | 40 | > 2,500,000 | too big | - |
| s7B2 | 2 | 118 | {2,3,5,7} | 33 | 22 | > 2,500,000 | too big | - |
| s5B6 | 6 | 354 | {2,3,5} | 25 | 40 | > 2,500,000 | too big | - |
| s7A6 | 6 | 354 | {2,3,5,7} | 33 | 72 | > 2,500,000 | too big | - |
| allA2 | 2 | 118 | all | 59 | 119 | > 2,500,000 | too big | - |
| s7B6 | 6 | 354 | {2,3,5,7} | 33 | 72 | > 2,500,000 | too big | - |
| s5C12 | 12 | 708 | {2,3,5} | 25 | 61 | > 2,500,000 | too big | - |
| chk192 (sanity) | 2 | 192 | {2,3} | 20 | 4 | 303,604 | OPTIMAL, gain 1, local check passed, threshold 95 | 13.6 s |

The sensitivity tier found this rule at L = 192 (gain 1, passes `rules_m.local_check`):
removed {8, 32, 192}; rephased 12 and 24 to (1/2, -1/2), 48 and 96 to (1/2, 1/2), 16 to (0, 1),
64 to (0, -1); added 3 and 9 at (3/4, 0) (pairs are (sigma0, beta)). It is Poliakova's 9 -> 8
rule with some signs mirrored, so the solver setup can find rules where they exist.

## Grades

- Sanity S1 and S2 passed (the commit's tests ran in the gate before commit 6c9dd61). S3: no
  encoding bug was reported. S4: no configuration was certified, so it was not tested.
- **R1** (a rule with threshold <= 58 is found; predicted no): **not found**. Only one of the
  nine tiers was decided, so this is mostly undecided rather than a negative.
- **R2** (both m = 2, 5-smooth tiers end INFEASIBLE; predicted yes): **half**. s5A2 is
  INFEASIBLE; s5B2 was too big to build.
- **R3**: not applicable (no rule).

## Two problems found after the run

1. **Helpers were left out.** `rule_search_s.py` built the pools from P-smooth speeds only, so
   untouched base speeds that are not P-smooth (for m = 2 and P = {2, 3, 5}: 14, 22, 26, 28,
   ...) could not cover anything in the encoding. `rules_m.local_check` allows them. The
   INFEASIBLE for s5A2 therefore excludes only rules whose helpers are 5-smooth too; it is
   weaker than the pre-registration said. Route 11 (`rule_search_c.py`, PREREG_rules_c.md)
   counts every untouched base speed as a helper.
2. **m = 2 was already covered.** The search notes of the 18..57 work
   ([solved-conjectures, search/NOTES.md](https://github.com/1337isnot1337/solved-conjectures/blob/main/results/shifted-lonely-runner-counterexamples/search/NOTES.md))
   report SAT searches (tomdif's `rule3.py`, `rule4.py`) with no gain-1 rule at L <= 190 for
   primes {2, 3} or {2, 3, 5} on the m = 2 base. aadrianvv's structured-patch solver
   ([issue 110](https://github.com/1337isnot1337/solved-conjectures/issues/110)) proved UNSAT
   for N = 95, 94 and 72 on Poliakova's base. We missed both when we pre-registered route 10,
   so its m = 2 tiers were not new. Route 11 moves to bases of multiples of 3, 4, 6 and 12.
   Their added runners sit at thirds, quarters and sixths of the base time scale, which those
   searches did not allow.

The too-big failures came from building every class of every base speed up front. Route 11
adds a class's clauses only when a candidate rule fails that class.
