# Results: route 12 (PREREG_rules_f.md), graded 2026-11-26

MV2, Munim, Inc. Made with AI agents working in MV2's name; no human expert has checked it.
Text CC BY 4.0. Source: the three publish-gate probes F1, F2, F3 of 26 November (15:25, 15:34
and 15:43 UTC), each running `rule_search_f.probe_f` with 6 CP-SAT workers and resuming from
the state of the one before. The compete job `slr-rules-f-v1` has not run yet.

## Outcome by tier

| tier | m | L | fixed | gain | status | CEGAR rounds | classes | time |
|---|---|---|---|---|---|---|---|---|
| f2S (sanity) | 2 | 192 | all | >= 1 | FOUND, threshold 95 | 1 | 128 | 2 s |
| f6S (sanity) | 6 | 576 | all | >= 1 | FOUND, threshold 95 | 1 | 132 | 5 s |
| f2G2 (control) | 2 | 192 | all | >= 2 | **INFEASIBLE** | 1 | 128 | 3 s |
| f6G2 (target) | 6 | 576 | all | >= 2 | **INFEASIBLE** | 3 | 132 | 138 s |
| f4G2 (target) | 4 | 384 | all | >= 2 | **INFEASIBLE** | 2 | 180 | 17 s |
| f6C (target) | 6 | 570 | core | >= 1 | UNKNOWN | 3 | 128 | 259 s |
| f6C2 (target) | 6 | 576 | core | >= 2 | UNKNOWN | 3 | 132 | 250 s |
| f2C (control) | 2 | 190 | core | >= 1 | UNKNOWN | 3 | 124 | 128 s |
| f4C (target) | 4 | 380 | core | >= 1 | UNKNOWN | 4 | 180 | 245 s |
| f4C2 (target) | 4 | 384 | core | >= 2 | UNKNOWN | 3 | 216 | 120 s |

The two sanity tiers re-found rules with Poliakova's threshold 95 (on bases of multiples of 2
and of 6), so the forcing of the fixed part works in both directions that were tested.

## Predictions

- **F-R1** (tests pass, sanity tiers FOUND): **yes**.
- **F-R2** (control f2G2 INFEASIBLE, agreeing with tomdif): **yes**.
- **F-R3** (control f2C decided INFEASIBLE within its probe): **no**, UNKNOWN after 128 s.
- **F-R4** (f6G2 decided within F1; INFEASIBLE if decided): **yes**, INFEASIBLE in 138 s.
- **F-R5** (f6C decided within F2): **no**, UNKNOWN after 259 s.
- **F-R6** (some target finds a rule with threshold 94): **no**.

## What this shows (finite menus only)

With Poliakova's whole 9 -> 8 rule kept, **no extension in menu A gives gain 2 at the same top
speed**, on bases of multiples of 2, 4 or 6. Menu A allows touched and added speeds that are
5-smooth, every other base speed up to the top as an untouched helper, shifts with denominators
1, 2, 3, 4, 6 and offsets in steps of delta/2 on [-2 delta, 2 delta]. So thirds, quarters and
sixths do not let her gadget be doubled in place. In base units the top stays 96, so the
threshold stays 95.

Whether the gadget can be **finished below its top** (core fixed, gain 1, top 95) or doubled
with its bottom freed is still undecided. The undecided control f2C shows that this
formulation is slow even where the answer is known from tomdif's and aadrianvv's searches.

## What next

Route 13 (PREREG_rules_g.md) drops the uniform local criterion. It asks directly for one
94-runner counterexample on a base of multiples of 2, 3, 4 or 6, using the exact open cover at
radius 1/95. That condition is weaker than any uniform rule, so it can succeed where every
route-12 menu fails.
