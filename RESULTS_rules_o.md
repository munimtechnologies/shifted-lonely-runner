# Results: route 19 (PREREG_rules_o.md), final grade

Interim grade 2026-11-27 about 21:30 UTC from gate probes O1 (20:19 UTC) and O2 (20:27 UTC);
final grade 2026-11-27 about 23:00 UTC from route 19's final cache state, which route 19b's
probes P1 and P2 printed (`O1STATE`). MV2, Munim, Inc. Made with AI agents working in MV2's
name; no human expert has checked it. Text CC BY 4.0.

## What ran

`test_top_o.py` passed in the gate (commit cb68097, release v0.19.0). Probes O1, O2 and O3 ran
`top_o.probe_o(budget=520)` against one cache. The reports of O1 and O2, verbatim except line
breaks:

```
CHK cal=T cal1=F cal66=T calcert=T pol=T
f96h:F5/31 f64x:F5/154 h64:F4/37 x64g2:U3/64 x72:U2/42 x81:U2/52 x59:U2/47 x60:U2/44
x61:U1/21 x62:U2/42 x63:U3/47 x65:U2/41 x66:U2/41 x67:U2/44 x68:U2/47 x69:U2/37
x70:U2/47 x71:U1/41 x73:U2/44 x74:U2/39 x75:U1/25 (x76..x95 not yet run)
SANE f96h gain=1 touched=11
SANE f64x gain=1 touched=11
SANE h64 gain=1 touched=11
STATUS new_n=- -=19 FOUND=3 UNKNOWN=18      (after O2)
```

O3's report did not reach us. The final cache state, as printed by route 19b's probes:

```
O1STATE -=8 FOUND=3 UNKNOWN=29
```

So after O3, 29 of the 37 targets had been tried (all UNKNOWN), 8 were never run, and the
three sanity tiers were FOUND.

## Grades

| prediction | said | outcome |
|---|---|---|
| O-R1: S1 and S2 hold | yes, 85% | **Yes.** Tests passed; CHK exactly as expected; no BUG token. |
| O-R2: f96h FOUND | yes, 80% | **Yes.** 5 iterations, 31 s. |
| O-R3: f64x FOUND | yes, 45% | **Yes.** 5 iterations, 154 s: the search re-derives a gain-1 rule at N = 64 in Callens's menu. |
| O-R4: h64 INFEASIBLE | yes, 55% | **No.** h64 was FOUND (4 iterations, 37 s): eighths of delta are not needed; shifts in halves of delta already give an n = 63 cover at N = 64. |
| O-R5: >= 10 targets INFEASIBLE | yes, 40% | **No.** 0 of 37 decided; 29 tried, all UNKNOWN. |
| O-R6: a certified new n | no, 3% yes | **No** (as predicted). |

Calibration facts confirmed by the gate: Callens's cover, read as a rule at N = 64, is a closed
cover at radius exactly 66/4225 = delta(1 + delta) (cal66=T) and not at delta = 1/65 (cal1=F),
and both global exact checkers accept it at R = 1/64 (calcert=T).

## Why the targets were not decided

Every target got one to three iterations. The solver call (rule_search_c.build_and_solve)
minimises the number of touched speeds, so it runs to its time limit on every iteration
(f64x: about 30 s per iteration). Route 19b (PREREG_rules_p.md) removed the objective; that
alone did not decide any target either (RESULTS_rules_p.md).

## Verdict

Route 19 is closed: a sound, calibrated exact search that is too slow in menu x to decide its
targets in 45 s turns. Its collected classes seed routes 19b and 19c.

## Limits

Nothing here is a new case of the conjecture. A FOUND sanity tier at N = 64 is a cover for
n = 63, which Callens found first. The route decided no target, so it says nothing about the
open range.
