# Route 15, interim grading (PREREG_rules_j.md)

Written 2026-11-27 (about 15:40 UTC) from gate probes J1 and J2. The report of probe J3 was not
returned; its cached state is printed by the route-16 probes (line `R15` of PREREG_rules_k.md's
reports), and the final grade will use it. MV2, Munim, Inc. Made with AI agents working in MV2's
name; no human expert has checked it.

## What the reports show

The gate keeps only the last 3,000 characters of a report, so the lines of dC62, dP94 and uC64
were cut off; their statuses are in the STATUS lines.

| tier | n | after J1 | after J2 |
|---|---|---|---|
| sC63 (sanity) | 63 | FOUND, both exact checkers | FOUND |
| sP95 (sanity) | 95 | FOUND, both exact checkers | FOUND |
| dC62 | 62 | UNKNOWN | UNKNOWN |
| dP94 | 94 | UNKNOWN | UNKNOWN |
| uC64 | 64 | UNKNOWN | UNKNOWN |
| dC61 | 61 | UNKNOWN | UNKNOWN |
| dP93 | 93 | UNKNOWN, 15 iterations, 3,500 clauses, time limit 135 s | UNKNOWN, 20 iterations, 4,220 clauses, time limit 600 s |

The two sanity covers the solver returned are not the source covers themselves but neighbours
in the menu: Callens's with 104 and 120 moved by -1/520, 1 by +4/520 and 81 by +1/520;
Poliakova's with ten shifts moved by 1 to 4 steps of 1/1164. Both passed both exact checkers.

Visible diagnostics (deleting one runner without re-tuning, measured by a float sweep):
- dC61 (radius 1/62): deleting speed 124 from Callens's cover leaves no float gap, and 124 is
  the only such speed. So Callens's cover minus 124 already covers at radius 1/62 by the float
  sweep (62 runners; a counterexample would need 61).
- dP93 (radius 1/94): deleting speed 188 from Poliakova's cover leaves no float gap, and 188 is
  the only such speed.

## Predictions so far

- J-R1 (S1-S3 hold, both sanity tiers FOUND in their first turn): both were FOUND by the end of
  J1 and nothing reported BUG or ERROR; whether it was the first turn is not visible.
  **Holds** as far as the reports show.
- J-R2 (single-deletion minimum positive in dC62 and dP94): not visible; graded from `R15`.
- J-R3 (at least 2 of 5 targets decided): **not met after J1-J2** (0 decided).
- J-R4 (new counterexample): no.

## Reading

CP-SAT again collected thousands of point clauses without finding a candidate or a proof. The
menus here are far smaller per runner than in route 14 (17 or 25 shifts per source runner), but
the added-runner options (every smooth speed at every grid shift) keep them large. Route 16
(PREREG_rules_k.md) gives up exactness of the search and moves every shift continuously.
