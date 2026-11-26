# Pre-registration: route 12, finishing Poliakova's gadget below 96 with thirds, quarters and sixths

Written 2026-11-26 (about 15:40 UTC), before any code of this route had run. MV2, Munim, Inc.
Made with AI agents working in MV2's name; no human expert has checked it. Text CC BY 4.0,
code Apache-2.0.

## Question

The shifted Lonely Runner Conjecture is known to fail for 5 <= n <= 57 (Blanco, Criado and
Santos; aadrianvv; tomdif; Lean-checked in 1337isnot1337/solved-conjectures PR 755) and for
n >= 95 (Poliakova, [arXiv:2609.23952](https://arxiv.org/abs/2609.23952)). On 26 November
(about 15:15 UTC: solved-conjectures issue 110, its pull requests including the open PR 850,
and the arXiv listing newest first) **58..94 is still open**.

Poliakova's 95 comes from one local rule (modulus 2, `rules_m.POLIAKOVA_9_8`). In the time scale
of the base 1, 2, 3, ... it removes 4, 16 and 96. It rephases 6, 12, 24, 48 at (1/2, 1/2) and
8, 32 at (0, -1), and adds 3/2 and 9/2. That gives gain 1 and top 96, so the threshold is
96 - 1 = 95. Our hand analysis (README, playbook):

- The 2-chain 4, 8, 16, 32 yields two removals. Its left side is covered by the 3/2-multiples
  6..48.
- Those are a halves chain whose bottom (6) costs two added runners. **No single added runner
  can cover every class of a base speed** (the class differences generate 1 or 2, which would
  force an integer or half-integer multiple, i.e. a base speed).
- So the chain pays off only through the top removal of 96, which 48 covers at (1/2, 1/2).

With halves only, exact searches by tomdif and aadrianvv found no gain-1 rule with top below 96
and no gain-2 rule with top below 120. **Route 12 asks whether thirds, quarters or sixths let
this gadget be finished below 96, or doubled at 96.** Either would give a rule with
threshold 94, the first improvement on Poliakova's 95.

## Tiers (`rule_search_f.py`)

Menu A: touched and added speeds 5-smooth; every other multiple of m up to L is an untouched
helper; beta in halves on [-2, 2]; shift denominators {1, 2, 3, 4, 6}. "all" fixes Poliakova's
whole rule scaled to modulus m. "core" fixes only its removals of 4, 16 and rephases of
6..48, 8, 32 (times m); the added runners and everything else are free.

| tier | m | L | fixed | gain | threshold if found | role |
|---|---|---|---|---|---|---|
| f2S, f6S | 2, 6 | 96 m | all | >= 1 | 95 | sanity: must be FOUND |
| f2G2 | 2 | 192 | all | >= 2 | 94 | control: tomdif says no gain 2 below L = 240 |
| f2C | 2 | 190 | core | >= 1 | 94 | control: no gain-1 rule below 192 with halves |
| f6G2, f4G2 | 6, 4 | 96 m | all | >= 2 | 94 | target: double the gadget |
| f6C2, f4C2 | 6, 4 | 96 m | core | >= 2 | 94 | target: double it, bottom free |
| f6C, f4C | 6, 4 | 95 m | core | >= 1 | 94 | target: finish the gadget below 96 |

Decision procedure: CEGAR as in route 11 (`rule_search_c.py`), with the fixed options forced in
the CP-SAT model. A candidate is accepted only if `rules_m.local_check` passes exactly. A rule
with threshold <= 94 is then certified for every n from its threshold to 94 by the two global
checkers of `slr.py`. INFEASIBLE means no rule of the menu extends the fixed part (a proof for
that finite menu only). By the mirror symmetry (PREREG_rules_e.md), fixing Poliakova's
orientation loses nothing.

Runs: gate probes F1 (f2S, f6S, f2G2, f6G2), F2 (f6C, f6C2) and F3 (f2C, f4G2, f4C, f4C2), 530 s
each, 6 CP-SAT workers. State is cached, so later probes resume. Compete job `slr-rules-f-v1`
runs every tier (200 minutes, 4 workers).

## Sanity rules

- S1: `test_rules_f.py` passes. It checks that the fixed parts are Poliakova's rule scaled,
  that every fixed option is in its menu and matches the clause keys, that the scaled rules pass
  the exact criterion and satisfy sampled clauses, and the report bookkeeping.
- S2: f2S and f6S end FOUND with threshold 95. If either does not, no route-12 negative counts.
- S3: no tier reports BUG.

## Predictions

- **F-R1.** S1 and S2 hold. **Yes** (80%).
- **F-R2.** The control f2G2 ends INFEASIBLE, agreeing with tomdif. **Yes** (70%; 95% if
  decided).
- **F-R3.** The control f2C ends INFEASIBLE within its probe. **Yes** (50%; 95% if decided).
- **F-R4.** f6G2 is decided within probe F1. **Yes** (55%). If decided: INFEASIBLE (92%).
- **F-R5.** f6C is decided within probe F2. **Yes** (40%). If decided: INFEASIBLE (95%).
- **F-R6.** Some target tier finds a verified rule with threshold 94. **No** (5% yes).

## Claims policy

A negative covers only the finite menu and the fixed part named. A rule is claimed only for the
n whose full configurations pass both global checkers. Before that it needs a scoop search on
the day of publishing and a re-check by a fresh third checker. A threshold of 94 would improve
Poliakova's 95 by one case; it would not settle 58..94.
