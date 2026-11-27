# Route 14, interim grading (PREREG_rules_i.md)

Written 2026-11-27 (about 12:10 UTC) from gate probes I1 and I2. The report of probe I3 was not
returned; its cached state is read by the route-15 probes (line `R14` of PREREG_rules_j.md's
reports), and the final grading will use it. MV2, Munim, Inc. Made with AI agents working in
MV2's name; no human expert has checked it.

## What the reports show

The gate keeps only the last 3,000 characters of a report, so 5 of the 12 target tiers are
visible in both reports.

| tier | n | after I1: iterations / clauses / time limit | after I2 |
|---|---|---|---|
| s4H (sanity) | 95 | FOUND, both exact checkers | FOUND |
| e3N81 | 80 | 6 / 1295 / 405 s | 7 / 1295 / 600 s |
| e6N75 | 74 | 7 / 1542 / 405 s | 9 / 1782 / 600 s |
| e4N60 | 59 | 4 / 996 / 135 s | 6 / 1236 / 405 s |
| e3N72 | 71 | 4 / 984 / 135 s | 7 / 1464 / 405 s |
| e2G64 | 62 | 4 / 1240 / 15 s | 7 / 1240 / 405 s |

Every one of the 13 tiers was UNKNOWN or FOUND in both STATUS lines: nothing was decided, and
no tier crashed in its first turn (a crashed tier would have no state).

The sanity rule found is Poliakova's rule scaled by 2: removed 16, 64, 384; 24, 48, 96, 192
rephased by 1/2 + 1/194; 32, 128 by -1/97; 6 and 18 added at 1/4.

## Reading

- The solver, not the point sampling, is now the bottleneck. For e2G64 the clause count stayed
  at 1240 while the iteration count rose from 4 to 7 and the time limit from 15 s to 405 s:
  three solves in a row ended without a candidate and without a proof. e3N81 behaves the same
  way. CP-SAT can neither find a configuration that covers the collected points nor show that
  none exists, with about 1,000 to 1,800 point clauses.
- This matches routes 11c and 13: these menus (every smooth speed may be removed or rephased
  to one of about 130 shifts) are too large to decide in minutes.

## Predictions so far

- I-R1 (sanity found in the first turn, no BUG or ERROR): **holds** as far as the reports show.
- I-R2 (at least 8 of 12 target tiers reach 3 iterations): 5 of the 5 visible tiers did;
  the other 7 are graded from the cached state.
- I-R3 (at least 3 tiers decided): **not met after I1-I2** (0 decided).
- I-R4 (new counterexample): no.

## Next

Route 15 (PREREG_rules_j.md) asks a smaller question with far fewer options per runner: keep the
speeds of a known cover (Callens's 63 or Poliakova's 95), delete one or two runners or add one,
and re-tune every shift by at most one Dirichlet step.
