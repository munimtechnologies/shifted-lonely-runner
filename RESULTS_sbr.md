# Route 5 graded (PREREG_sbr.md)

Graded 2026-11-25 by AI agents working in MV2's name. No human expert has checked this.

Route 5 (`slr_sbr.py`) is best response over speed and shift, warm-started from the published
n = 54 certificate (aadrianvv, 1337isnot1337/solved-conjectures). It ran in the repository's
publish test gate (one Windows process, Python standard library, 500 s per probe).

| item | prediction | outcome |
|---|---|---|
| S1 `test_slr_sbr.py` passes, module committed | 85% | **true** (commit b5eeae6) |
| S2 all 37 published certificates (18 <= n <= 54) pass MV2's three exact checkers | 95% | **true** (commit c702698: the test needs every certificate to pass the sweep checker, the integer-endpoint checker and the closed cover at the recorded gamma) |
| P-any: a probe certifies n = 55 | 10% | **false** |
| P-close: best ratio gamma*(n+1) below 1.005 | 50% | **true**, barely: P1 reached 1.00461 |
| P-speed: P1 or P3 (speed moves) beats P2 (shifts only) | 60% | **true** for P1 (1.00461 against 1.00505); P3's report did not come back |

Probe reports (from the gate output):

| probe | seed | speed moves | best ratio | E = 1/gamma - 56 | sweeps | kicks |
|---|---|---|---|---|---|---|
| P1 | 1 | p = 0.3, 40 candidates | 1.00461 | -0.2570 | 1065 | 111 |
| P2 | 2 | none | 1.00505 | -0.2814 | 7821 | 864 |
| P3 | 3 | p = 0.6, 80 candidates | no report | | | |

The published n = 54 certificate has E = 0.7186 (1/gamma = 55.72). Adding a 55th runner
and moving one runner at a time raised 1/gamma only to 55.74; 56 is needed. The 18..54
authors' own best at n = 55, with a compiled annealer and a sequential-LP polish, was
E = -0.012. Best response alone is far weaker than that, so route 6 (`slr_lp.py`,
`PREREG_lp.md`) adds the missing piece, a polish that moves all shifts at once.

Independent re-check of the published 18..54 certificates (S2): this is the first check of
them with code written separately from the authors' `verify.py`. All 37 passed.
