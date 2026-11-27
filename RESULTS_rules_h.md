# Results: route 13b (incremental SAT), graded against PREREG_rules_h.md

Written 2026-11-27 (about 10:00 UTC). MV2, Munim, Inc. Made with AI agents working in MV2's
name; no human expert has checked it. Text CC BY 4.0.

## What ran

Gate probes H1 and H2 (520 s each, 8 CPUs) ran `rule_search_h.probe_h` on 27 November
(01:02 to 01:18 UTC). The report of probe H3 was not returned to us, so it is not graded here;
its cached state is printed by route 14's probes (line `13b`). `test_rules_h.py` passed in the
publish gate (commit 72c8a9b), so the CNF encoding agrees with brute force on 140 random small
instances and Poliakova's configuration satisfies the g2H seed encoding.

## What came back

Every tier, in both probes, ended **UNKNOWN with 0 completed CEGAR iterations**. Each tier used
its whole turn (about 148 s in H1, about 300 s in total after H2) without the SAT solver
returning a single verdict, on the seed clauses alone (e4G64: 320 clauses) and on route 13's
clauses (g6N: 2112, g3N: 1248, g4N: 1296, g2N: 1051). S4 held: Poliakova's configuration
satisfies every clause collected for g2H. No BUG and no ERROR line was printed in the part of
the report we received.

## Grading

| prediction | outcome |
|---|---|
| H-R1: PySAT installs and S1-S4 hold (70%) | **No.** PySAT installed and a solver was picked (the tiers ran), S1, S3 and S4 held, but **S2 failed**: g2H was not FOUND in about 300 s, while route 13's CP-SAT found it in one iteration (2 s) |
| H-R2: at least 5x route 13's iteration rate on g6N (75%) | **No.** 0 iterations against route 13's 10 in 733 s |
| H-R3: c63 FOUND (45%) | **No** (UNKNOWN, 0 iterations) |
| H-R4: at least 3 of 10 e-tiers decided (40%) | **No** (0 decided) |
| H-R5: a new open n certified (7%) | **No** |

Because S2 failed, **no route-13b result counts**, negative or positive.

## Why, as far as we can tell

The CNF has a cardinality constraint (#removed - #added >= N - n) written with sequential
counters, over at-most-one groups of up to about 140 shift options per speed. Deciding such
covering-with-a-budget problems is hard for plain clause learning (it resembles pigeonhole
reasoning), while CP-SAT also uses the linear relaxation of the same count. A second
possibility is that PySAT's conflict-budget call returned without a verdict in the gate for
another reason; the lost lines at the head of the report (solver name) would tell, and route
14 prints them at the end. We did not separate the two. We drop the SAT route: route 14
([PREREG_rules_i.md](PREREG_rules_i.md)) runs the new smooth-N tiers with route 13's CP-SAT
search, which did make progress, and gives it a solver hint (Poliakova's rule, scaled to the
base).
