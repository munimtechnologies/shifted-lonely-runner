# Route 18, grading (PREREG_rules_n.md)

Written 2026-11-27 (about 20:00 UTC) from gate probes N1 and N2 (about 480 s each). The N3
report was not returned. The gate keeps only the last 3,000 characters of a failing report, so
the lines of tiers kC64, kP94 and kC62 were cut off both times; what is visible is the end of the
kC61 line, the cC63 line, the cached lines of routes 16 and 17 and the STATUS line. MV2, Munim,
Inc. Made with AI agents working in MV2's name; no human expert has checked it.

## What the reports show

| tier | n | after N1 | after N2 |
|---|---|---|---|
| kC61 | 61 | lambda 0, cycle {22, 102}, rigid, 0 rises, 67 plateau moves, 24 kicks | lambda 0, cycle {2, 122}, rigid, 0 rises, 137 plateau moves, 47 kicks |
| cC63 (calibration) | 63 | no chain (lambda -1), uncovered 0.018 | the same |
| kC64, kP94, kC62 | 64, 94, 62 | cut off | cut off |

STATUS after N1 and after N2: all five tiers UNKNOWN. No margin ever rose (`up=0`).

## Predictions

- **N-R1** (tests pass; every lambda-0 two-runner cycle is rigid): **held as far as visible**
  (commit 03a03bc passed `test_climb_n.py`; both visible cycles have rig=1; no BUG line).
- **N-R2** (kC64 and kP94 start at lambda 0 with a rigid pair): **not visible** (their lines
  were cut); route 17's cache, which seeds them, has exactly that state.
- **N-R3** (a plateau move that changes the critical cycle): **held**: kC61 moved from
  {22, 102} to {2, 122}, both summing to 124 = 2(n + 1).
- **N-R4** (a new open n): **no.**
- **N-R5** (CAL17 raw=True): **held.**

## What it means

Changing the speeds at the blocking pair only trades one rigid pair for another: every critical
cycle route 17 or 18 saw is a pair of speeds summing to 2(n + 1), and no move raised the margin.
The obstruction looks structural, not a matter of tuning. Local search around the known covers
(routes 15-18) is closed. Route 19 (PREREG_rules_o.md) changes method: it asks for exact
rules at a single N that use the slack between 1/(N + 1) and 1/(n + 1), the mechanism behind
Callens's n = 63 cover, and decides finite menus of them completely.
