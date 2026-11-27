# Results: route 19b (PREREG_rules_p.md), interim grade

Graded 2026-11-27 about 23:00 UTC from gate probes P1 (21:28 UTC) and P2 (21:37 UTC). Probe
P3's report did not reach us; route 19c's probes print route 19b's final cache state
(`P1STATE`, and in full any target it decided), and P-R3 to P-R5 are graded from it next.
MV2, Munim, Inc. Made with AI agents working in MV2's name; no human expert has checked it.
Text CC BY 4.0.

## What ran

`test_top_p.py` passed in the gate (commit fabcd40, release v0.20.0). Probes P1 and P2 ran
`top_p.probe_p(budget=520)` against one cache (only the end of each report is returned).
After P2:

```
pf64x:F3/53 ph64:F4/8 x64g2:U1/63 x72:U2/64 x81:U3/63 x59:U1/60 x60:U1/62 x61:U2/61 x62:U1/61
x63:U1/61 x65:U1/63 x66:U1/61 x67:U3/65 x68:U2/63 x69:U2/62 x70:U2/63 x71:U2/61 (x73..x95 not yet run)
PIT iterations=32 solve_s=702 per_it=22.0          (after P1: 18, 345, 19.2)
SANE pf64x R=8,32,72,96,108 S=12@1/2,1/2 16@0,-3/2 24@1/2,1/2 36@1/2,0 48@1/2,1/2 64@0,-1 128@0,1 A=3@3/4,1/8 9@3/4,0 27@3/4,0 81@3/4,-1/4
SANE ph64 R=8,32,96 S=12@1/2,1/2 16@0,-3/2 24@1/2,1/2 48@1/2,1/2 64@0,-1 128@0,1 A=3@3/4,0 9@3/4,0
STATUS new_n=- -=22 FOUND=2 UNKNOWN=15
```

A rule is written R = removed, S = rephased w@s0,beta (shift s0 + beta delta), A = added odd
speeds, on the base 2, 4, ..., 2N, delta = 1/(N + 1). SANE means FOUND and accepted by both
global exact checkers of slr.py at R = 1/(n + 1).

## Grades so far

| prediction | said | outcome |
|---|---|---|
| P-R1: S1 and S2 hold | yes, 70% | **Yes** so far: tests passed, pf64x FOUND from scratch (3 iterations, 53 s), no BUG through P2. |
| P-R2: PIT below 5 s | yes, 70% | **No.** 19.2 s after P1, 22.0 s after P2. |
| P-R3: x64g2 INFEASIBLE within P1-P3 | yes, 40% | Pending (UNKNOWN after one iteration of 63 s). |
| P-R4: >= 10 targets INFEASIBLE | yes, 45% | Pending (0 of 15 tried after P2). |
| P-R5: a certified new n | no, 3% yes | Pending (none after P2). |

## What we learned

1. **The objective was not the bottleneck.** Without it the sanity tiers are fast (ph64:
   4 iterations in 8 s), but on the targets almost every feasibility call still ran out of
   time. The seeded clause sets in menu x are hard for CP-SAT to satisfy or refute in a minute.
2. **A much smaller n = 63 cover.** ph64 removes 8, 32, 96, rephases 12, 24, 48 to
   1/2 + delta/2, 16 to -3 delta/2, 64 to -delta and 128 to +delta, and adds 3 and 9 at 3/4.
   That is 11 touched speeds against 18 in Callens's certificate, and only two added odd
   speeds against five. It is Poliakova's 9 -> 8 rule (remove 8, 32, 192; rephase 12, 24, 48,
   96 to 1/2 + delta/2 and 16, 64 to -delta; add 3, 9 at 1/4) cut off at 2N = 128 by the top
   trick: 96 is removed instead of rephased and 128 at +delta does the work of the missing
   192. Callens's own note calls his cover "sporadic"; this suggests that n = 63 is the
   N = 64 instance of Poliakova's gadget, with nothing else needed. The explicit cover is
   `cover_n063_simple.json`, re-checked by four exact checkers in `test_cover_n063_simple.py`.
   n = 63 is Callens's case; this is a second, simpler certificate, not a new case. Route 19,
   whose solver minimised the number of touched speeds, also ended at 11 touched speeds in
   f64x and h64 (RESULTS_rules_o.md, `SANE ... touched=11`); the end of P1's `OLD` line shows
   route 19's f64x rule closes with 128@0,1 A=3@3/4,1/8 9@3/4,0, a variant of the same gadget.
   So 11 is the smallest size either solver found in these menus, not a proven minimum.
3. **pf64x** is a third n = 63 cover, between the two: it keeps 4 (Callens removes it) and adds
   3, 9, 27, 81 but not 1.

Both known gain-1 rules use shifts s0 in quarters and beta in halves of delta only. Route 19c
(PREREG_rules_q.md) searches that small menu.

## Limits

Nothing here is a new case of the conjecture. No target was decided by P2.
