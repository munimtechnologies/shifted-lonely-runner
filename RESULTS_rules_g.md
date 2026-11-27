# Route 13, interim grading (PREREG_rules_g.md)

Written 2026-11-27 (about 01:10 UTC). MV2, Munim, Inc. Made with AI agents working in MV2's
name; no human expert has checked it. Text CC BY 4.0.

Route 13 asks for one 94-runner counterexample to the shifted Lonely Runner Conjecture on a
base of multiples of m, decided by CP-SAT over time-point clauses. Three gate probes ran on
2026-11-26. The reports of G1 and G2 came back; the report of G3 (g3N, g4N) did not. Its
state is kept in the gate's cache, and the first route-13b probe prints it (line "13cache").

| tier | probe | status | iterations | clauses | literals | seconds |
|---|---|---|---|---|---|---|
| g2H (sanity, n = 95) | G1 | **FOUND** | 1 | 380 | 20,752 | 2 |
| g2N (control) | G1 | UNKNOWN | 9 | 1,051 | 55,652 | 222 |
| g6N (target) | G1 + G2 | UNKNOWN | 10 | 2,112 | 282,472 | 733 |
| g3N, g4N (targets) | G3 | report not returned | | | | |

The g2H configuration is Poliakova's rule itself: removed 8, 32, 192; rephased 12, 24, 48, 96
to 588/1164 and 16, 64 to 1152/1164; added 3 and 9 at 291/1164. Padded to 95 runners, it
passes both global exact checkers at radius 1/96.

## Predictions

- **G-R1** (S1, S2, S3 hold): S1 yes (tests passed in the gate, commit bc9985e), S2 yes. S3 holds
  for G1 and G2; **pending for G3**.
- **G-R2** (g2N decided within the three probes): **No.** Only G1 ran g2N.
- **G-R3** (g6N decided within the three probes): **No.** Its CP-SAT calls reached their
  405-600 s limits without a verdict.
- **G-R4** (a certified 94-runner counterexample): none in G1 or G2; **pending for G3**.

## What follows

The CP-SAT loop was too slow: it rebuilt the model at every iteration. Route 13b
([PREREG_rules_h.md](PREREG_rules_h.md)) asks the same question with an incremental SAT
solver and resumes from these clauses.
