# Results so far: route 11c (cube-and-conquer rule search), interim grading

Written 2026-11-26 (about 15:40 UTC) from the reports of gate probes E1 and E2 (run 14:00 to
14:17 UTC). Probe E3's report was not returned; its state is cached and the next probe prints
it. MV2, Munim, Inc. Made with AI agents working in MV2's name; no human expert has checked it.
Text CC BY 4.0.

Pre-registration: [PREREG_rules_e.md](PREREG_rules_e.md). Code: `rule_search_e.py` (commit
e50f3c1, tests passed in the publish gate).

## Raw report lines

```
c2neg m=2 L=190 st=UNKNOWN cubes=29/38 infeasible frontier=72 open=96S,108R,108S,128R,128S,144R,144S,162R,162S t=680s
c4A58 m=4 L=236 st=UNKNOWN cubes=17/50 infeasible frontier=32 open=36R,48R,48S,60R,60S,64R,64S,72R,72S,80R,80S,96R..(+21) t=690s
c6A58 m=6 L=354 st=UNKNOWN cubes=13/50 infeasible frontier=36 open=48R,54R,54S,60R,60S,72R,72S,90R,90S,96R,96S,108R..(+25) t=1417s
SANITY c2chk 192R st=FOUND thr=95 it=3 t=9.9s
SANITY c6chk 576R st=FOUND thr=95 it=2 t=8.5s
```

## What is established (each for its finite menu only)

- **c2neg** (m = 2, L = 190, primes {2, 3}, menu A): no gain-1 rule whose touched speeds are all
  <= 72 (frontier). Of 38 cubes, 29 are INFEASIBLE: both cubes of every T <= 72, and 96R. The
  9 open cubes all have T >= 96 > L/2, where no untouched multiple of T is present to help.
- **c4A58** (m = 4, L = 236, primes {2, 3, 5}): frontier 32; 17 of 50 cubes INFEASIBLE.
- **c6A58** (m = 6, L = 354, primes {2, 3, 5}): frontier 36; 13 of 50 cubes INFEASIBLE.
- Unchanged from route 11: **c3A58 INFEASIBLE** (157 s).

## Grading

| prediction | stated | outcome |
|---|---|---|
| E-R1: tests pass, both sanity cubes FOUND | yes (75%) | **yes**: tests passed; c2chk 192R and c6chk 576R FOUND with threshold 95 |
| E-R2: c2neg INFEASIBLE within E1 | yes (45%) | **no**: 29 of 38 cubes, frontier 72 |
| E-R3: c4A58 decided within E1 | no (30% yes) | no (as predicted) |
| E-R4: c6A58 decided within E2 | no (20% yes) | no (as predicted) |
| E-R5: c6A58 frontier >= 144 after E2 | yes (60%) | **no**: frontier 36 |
| E-R6: a verified rule with threshold <= 94 | no (10% yes) | no (as predicted) |
| E-R7: 11b and 11c agree where both decide | yes (95%) | not testable yet: no tier is decided in both |

The cube split decides the small cubes quickly, but the cubes with a large top speed are as
hard as the whole menu was. Route 11c keeps running from its cache. Route 12
([PREREG_rules_f.md](PREREG_rules_f.md)) asks a narrower question that the solver can decide:
can Poliakova's own gadget be finished below 96 when the added runners may sit at thirds,
quarters or sixths?
