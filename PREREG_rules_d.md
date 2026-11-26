# Pre-registration: route 11b, the route-11 rule search in feasibility mode

Written 2026-11-26, before any code of this route had run. MV2, Munim, Inc. Made with AI
agents working in MV2's name; no human expert has checked it. Text CC BY 4.0, code Apache-2.0.

## Where route 11 stands (PREREG_rules_c.md)

Route 11 searches for local rules on bases of multiples of m = 3, 4, 6 and 12 (criterion and
proof in `rules_m.py`; search in `rule_search_c.py`). Its first two gate probes (2026-11-26,
07:57 and 08:05 UTC) reported:

| tier | m | L | menu | status | iterations | classes | seconds |
|---|---|---|---|---|---|---|---|
| c2chk | 2 | 192 | A, primes {2,3} | FOUND (Poliakova's rule, mirrored) | 3 | 88 | 25 |
| c3A58 | 3 | 177 | A, primes {2,3,5} | **INFEASIBLE** | 4 | 134 | 157 |
| c6A58 | 6 | 354 | A, primes {2,3,5} | UNKNOWN | 8 | 144 | 816 |

So the sanity tier passed, and **menu A on the base of multiples of 3 has no gain-1 rule with
threshold 58** (touched and added speeds 5-smooth, every other multiple of 3 up to 177 a
helper, beta in steps of 1/2 on [-2, 2], shift denominators {1, 2, 3, 4, 6}). This is a
statement about that finite menu only. On c6A58, CP-SAT (asked to minimise the number of
touched speeds) returned no candidate at all in its last calls. Predictions C-R1 to C-R4 will
be graded when the remaining tiers are decided or the compete job `slr-rules-c-v1` reports.

## What changes (`rule_search_d.py`)

1. **Feasibility mode.** Same clauses, same constraints (one state per touchable base speed, at
   most one shift per added speed, gain >= 1), no objective; the last candidate is passed to
   CP-SAT as a hint. The threshold does not depend on the size of the rule, so the objective
   was never needed. INFEASIBLE on a subset of the classes still proves that the finite menu
   has no rule, because every rule that passes `local_check` satisfies every class's clauses.
2. **A time cap per tier**, so one hard tier no longer takes every probe.
3. **A sanity tier for modulus 6.** c6chk: m = 6, L = 576, primes {2, 3}, menu A. Poliakova's
   rule scaled by 3 lies in this menu (`test_rules_d.py`), so the search must end FOUND there,
   with threshold 95. It checks the m = 6 path the way c2chk checked m = 2.
4. Tier states are cached; UNKNOWN tiers resume from the classes route 11 collected.

Runs: three gate probes (530 s each, 6 workers): D1 = c6chk (cap 170 s), c4A58 (200 s), c2neg
(140 s); D2 = c6A58 (500 s, resuming route 11's 144 classes); D3 = c3A94 (230 s), c4A94
(230 s), c4A58 (60 s more if still open). Compete job `slr-rules-d-v1`: every tier of
`ORDER_D`, 40 minutes each in a first pass, then the time left for the open ones (5.5 hours,
4 CPUs).

## Sanity rules (if one fails, the negatives of that modulus are not graded)

- S1: `test_rules_d.py` passes (the scaled rule is in the c6chk menu and passes `local_check`;
  hints, state seeding and certification behave as stated).
- S2: c6chk ends FOUND. If it ends UNKNOWN, the m = 6 and m = 12 negatives are reported as
  unchecked; if it ends INFEASIBLE, that is an encoding error and nothing of m = 6 counts.
- S3: no tier reports BUG.

## Predictions

- **D-R1.** c6chk ends FOUND within its cap. **Yes** (80%).
- **D-R2.** c2neg ends INFEASIBLE (agreeing with tomdif's rule3 negative). **Yes** (85%).
- **D-R3.** c4A58 is decided within the gate probes (D1 and D3). **Yes** (50%).
- **D-R4.** c6A58 is decided within probe D2 in feasibility mode. **No** (35% yes).
- **D-R5.** Any tier finds a verified rule with threshold <= 94. **No** (15% yes).
- **D-R6.** If a tier finds a rule with threshold <= 94, both global checkers of `slr.py`
  certify every n from its threshold to 94 that the probe reaches. **Yes** (90%, conditional).

## Claims policy

As for route 11: a negative covers only the finite menu named. A rule is claimed only for n
whose full configurations pass both global checkers, after a scoop search on the day of
publishing, and after a fresh third checker re-checks the certificates.
