# Route 14, final grading (PREREG_rules_i.md)

Interim grading written 2026-11-27 about 12:10 UTC from gate probes I1 and I2; final grading
written 2026-11-27 about 15:40 UTC from route 14's cached state, which the route-15 probes J1
and J2 printed (line `R14`; probe I3's own report was not returned). MV2, Munim, Inc. Made with
AI agents working in MV2's name; no human expert has checked it.

## Final state of every tier

`R14` line of J1 and J2 (identical): status / CEGAR iterations / point clauses.

| tier | n | status | iterations | clauses |
|---|---|---|---|---|
| s4H (sanity) | 95 | FOUND, certificate cached | 2 | 740 |
| e2G64 | 62 | UNKNOWN | 8 | 1240 |
| e4N60 | 59 | UNKNOWN | 7 | 1236 |
| e6N60 | 59 | UNKNOWN | 8 | 1584 |
| e2N72 | 71 | UNKNOWN | 8 | 1160 |
| e3N72 | 71 | UNKNOWN | 8 | 1464 |
| e4N72 | 71 | UNKNOWN | 9 | 1764 |
| e6N72 | 71 | UNKNOWN | 9 | 1644 |
| e6N75 | 74 | UNKNOWN | 10 | 1782 |
| e2N80 | 79 | UNKNOWN | 8 | 1236 |
| e4N80 | 79 | UNKNOWN | 11 | 2124 |
| e3N81 | 80 | UNKNOWN | 8 | 1295 |
| e6N90 | 89 | UNKNOWN | 8 | 2040 |

No tier crashed (no `ERR:` entry). The sanity rule found is Poliakova's rule scaled by 2:
removed 16, 64, 384; 24, 48, 96, 192 rephased by 1/2 + 1/194; 32, 128 by -1/97; 6 and 18 added
at 1/4.

## Predictions, graded

- I-R1 (sanity found in the first turn, no BUG or ERROR): **holds**.
- I-R2 (at least 8 of 12 target tiers reach 3 iterations): **holds** (12 of 12, 7 to 11
  iterations).
- I-R3 (at least 3 tiers decided): **failed** (0 of 12 decided).
- I-R4 (new counterexample): **no**.

## Reading

The solver, not the point sampling, was the bottleneck: on several tiers the clause count stayed
fixed while the time limit grew to 405-600 s and solves ended without a candidate or a proof.
These menus (every smooth speed removed or rephased to one of about 130 shifts) are too large to
decide in minutes with CP-SAT, as in routes 11c and 13. Route 14 is closed without a result.
Routes 15 and 16 (PREREG_rules_j.md, PREREG_rules_k.md) work next to the known covers instead.
