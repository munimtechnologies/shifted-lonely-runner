# shifted-lonely-runner

Does the **shifted Lonely Runner Conjecture** fail for every number of runners n >= 5?
Counterexamples are known for 5 <= n <= 17 (Blanco, Criado and Santos,
[arXiv:2603.24784](https://arxiv.org/abs/2603.24784)), for 18 <= n <= 54 (aadrianvv with
Claude, published 2026-11-22), for n = 55, 56 and 57 (tomdif, published 2026-11-25; all in
[1337isnot1337/solved-conjectures](https://github.com/1337isnot1337/solved-conjectures/tree/main/results/shifted-lonely-runner-counterexamples),
unrefereed; 18..57 Lean-checked there in PR 755), for n = 63 (Callens,
[Zenodo 24051700](https://doi.org/10.5281/zenodo.24051700), 2026-11-08, unrefereed) and for
n >= 95 (Poliakova, [arXiv:2609.23952](https://arxiv.org/abs/2609.23952)). Counterexamples for the remaining cases
would answer the first part of Zhang's question
([arXiv:2608.13599](https://arxiv.org/abs/2608.13599), Question 8.5) of whether it fails for
every n >= 5. This repository searches for them and checks every candidate exactly.

By MV2 of Munim, Inc. (mv2@munimtech.com). Code Apache-2.0; text and data CC BY 4.0.
The code and text were made with AI agents working in MV2's name. No human expert has
checked them yet.

## Status (2026-11-27, 17:00 UTC)

- **Open: 58 <= n <= 62 and 64 <= n <= 94.** n = 63 is Xavier Callens's
  ([Zenodo 24051700](https://doi.org/10.5281/zenodo.24051700), 8 November 2026: a
  Poliakova-type move on 2, 4, ..., 128, gamma = 66/4225 < 1/64; no human audit). Our status
  lines from 24 to 26 November said "58..94 open"; that was wrong, because our searches had
  missed Zenodo. Re-checked 2026-11-27 about 16:45 UTC: the Zenodo API and solved-conjectures
  pull requests (F1Justin's PR 850, merged, and PR 1017, open: the fixed 57-runner
  configuration plus any seven extra runners still leaves an uncovered time at radius 1/59).
- **No new case from this repository.** Our n = 55 (`certs_lp.json`, commit 9276b4f,
  E = +0.116) was found on the same day as tomdif's; we count it as an independent certificate,
  not as a new case.
- **Route 17 (new, pre-registered in [PREREG_rules_l.md](PREREG_rules_l.md)).** Exact answers
  where route 16 could only measure: (A) can one added runner of any speed turn Callens's
  fixed-shift cover into an n = 64 cover (decided exactly for every speed that could work)?
  (B) what is the largest overlap margin that any re-tuning of the shifts gives a near-cover's
  chain of arcs (a minimum cycle mean, computed exactly)? (C) polish and search alternately.
- **Route 16, interim** ([RESULTS_rules_k.md](RESULTS_rules_k.md)). Every target tier fell
  from 1e-5..1e-4 to an uncovered measure of 1e-9..4e-9 at its shrunk radius and stopped; no
  cover. That floor is about what touching arcs give under the shrink. The calibration tier had
  not re-found Callens's cover after two probes.
- **Route 15 graded** ([RESULTS_rules_j.md](RESULTS_rules_j.md)). Both sanity tiers re-found
  covers next to Callens's and Poliakova's; 0 of 5 targets decided after three probes. No
  single runner can be dropped from either cover without re-tuning (smallest uncovered
  measures 1.6e-4 and 6.8e-5). Closed.
- **Route 14 graded** ([RESULTS_rules_i.md](RESULTS_rules_i.md)). The sanity tier found
  Poliakova's rule scaled to multiples of 4; all 12 target tiers stayed undecided after 7 to 11
  CEGAR iterations each. Closed without a result.
- **Route 13b graded** ([RESULTS_rules_h.md](RESULTS_rules_h.md)). The incremental SAT solver
  made no iteration in about 300 s per tier and failed its sanity tier, so none of its results
  count. Dropped.
- **Route 13, interim** ([RESULTS_rules_g.md](RESULTS_rules_g.md)). The sanity tier found
  Poliakova's rule; the control and the m = 6 target stayed undecided under CP-SAT.
- **Route 12 graded** ([RESULTS_rules_f.md](RESULTS_rules_f.md)). With Poliakova's whole rule
  kept, **no extension in menu A gives gain 2 at the same top**, on bases of multiples of 2, 4
  or 6 (CP-SAT INFEASIBLE). So thirds, quarters and sixths do not double her gadget in place.
- **Route 11c** ([PREREG_rules_e.md](PREREG_rules_e.md), interim grading in
  [RESULTS_rules_e.md](RESULTS_rules_e.md)). For each finite menu, no gain-1 rule has all its
  touched speeds at or below the frontier: 72 for c2neg, 32 for c4A58, 36 for c6A58.
- **Route 11** ([PREREG_rules_c.md](PREREG_rules_c.md)). **Menu A on the base of multiples of 3
  has no gain-1 rule with threshold 58** (CP-SAT INFEASIBLE). This covers that finite menu only.
- **Routes 10 and 11b** ([RESULTS_rules_s.md](RESULTS_rules_s.md), [PREREG_rules_d.md](PREREG_rules_d.md)):
  superseded.
- Independent re-check of the published 18..54 certificates: all 37 pass MV2's three exact
  checkers (`test_external_certs.py`, commit c702698).

A fact used by route 12, with its proof: **no single added runner covers every class of a
touched base speed q.** The classes are k in [0, q) with gcd(k, q/m) = 1. With j = q/m, their
differences generate 1 if j is odd (k = 1, 2, or k = 0 and 1 when j = 1) and 2 if j is even
(1, 1 + j and j - 1). A runner of speed w covers class k only if (w/q) k + s0 is an integer,
so one runner covering all classes needs (w/q) * 1 or (w/q) * 2 to be an integer. Then w is a
multiple of q or of q/2 = m j/2, so a multiple of m: a base speed, not an added one.

A fact used by route 14: **multiplying every speed of a cover by an integer k keeps it a cover
with the same shifts** (at time t the scaled runners sit where the old ones sit at time k t).
So Poliakova's 95-runner configuration on 2, 4, ..., 192 gives 95-runner configurations on the
multiples of 4 and of 6 up to 96 m.

A fact used by routes 15 to 17: **k runners that cover at radius 1/(n+1) give a counterexample
for n whenever k <= n**, because extra runners at shift 0 only add arcs. So deleting d runners
from a k-runner cover is enough for n = k - d if the survivors, possibly re-tuned, still cover
at the larger radius 1/(k - d + 1).

A fact used by route 17, with its proof: **for a fixed chain of arcs, the best overlap margin is
a minimum cycle mean.** Runner i, lift k covers ((k - s_i - R)/v_i, (k - s_i + R)/v_i). With
x_i = s_i / v_i, the two overlaps of consecutive chain arcs A, B are c1 - x_A + x_B and
c2 - x_B + x_A with c1, c2 independent of the shifts, so "every overlap >= eps" is a system of
difference constraints. It is feasible iff the constraint graph with weights c - eps has no
negative cycle, so the largest eps is the minimum cycle mean of the weights c.

## What is here

| file | what it does |
|---|---|
| `certs_lp.json`, `test_certs_lp.py` | our n = 55 counterexample and its exact re-check by four checkers |
| `slr.py` | two independent exact certificate checkers (Fractions sweep; integer endpoint test) and the float search |
| `test_slr.py` | standard-library tests; every expected value is proved by hand in a comment |
| `job_slr.py`, `PREREG.md`, `RESULTS_gap.md` | route 1: direct search, n = 18..94 (certified 18-25, 27; not new) |
| `rules.py`, `rule_search.py`, `test_rules.py`, `job_rules.py`, `PREREG_rules.md` | route 2: Poliakova-type local rules (exact criterion with proof, CP-SAT search) |
| `rules_m.py`, `rule_search_m.py`, `test_rules_m.py`, `job_rules_m.py`, `PREREG_rules_m.md` | route 3: local rules on a base of multiples of m |
| `rule_search_s.py`, `test_rules_s.py`, `job_rules_s.py`, `PREREG_rules_s.md`, `RESULTS_rules_s.md` | route 10: local rules at threshold 58 over smooth speeds (graded) |
| `rule_search_c.py`, `test_rules_c.py`, `job_rules_c.py`, `fetch_deps_c.py`, `PREREG_rules_c.md` | route 11: counterexample-guided exact search for rules on bases of multiples of 3, 4, 6, 12 |
| `rule_search_d.py`, `test_rules_d.py`, `job_rules_d.py`, `fetch_deps_d.py`, `PREREG_rules_d.md` | route 11b: the same search in feasibility mode, with caps and an m = 6 sanity tier |
| `rule_search_e.py`, `test_rules_e.py`, `job_rules_e.py`, `fetch_deps_e.py`, `PREREG_rules_e.md`, `RESULTS_rules_e.md` | route 11c: cubes by the largest touched speed, mirror symmetry broken, cubes in parallel |
| `rule_search_f.py`, `test_rules_f.py`, `fetch_deps_f.py`, `PREREG_rules_f.md`, `RESULTS_rules_f.md` | route 12: Poliakova's gadget fixed, the rest searched with thirds, quarters and sixths (graded) |
| `rule_search_g.py`, `test_rules_g.py`, `fetch_deps_g.py`, `PREREG_rules_g.md`, `RESULTS_rules_g.md` | route 13: exact fixed-n search for a 94-runner counterexample (CEGAR over time points, CP-SAT) |
| `rule_search_h.py`, `test_rules_h.py`, `PREREG_rules_h.md`, `RESULTS_rules_h.md` | route 13b: the same question with an incremental SAT solver (graded: failed its sanity tier) |
| `rule_search_i.py`, `test_rules_i.py`, `PREREG_rules_i.md`, `RESULTS_rules_i.md` | route 14: fixed-n CP-SAT searches at smooth N inside 58..94 with a scaled Poliakova hint (graded) |
| `descent_j.py`, `test_descent_j.py`, `PREREG_rules_j.md`, `RESULTS_rules_j.md` | route 15: delete from or add to the known 63- and 95-runner covers, every shift re-tuned on a grid (graded) |
| `descent_k.py`, `test_descent_k.py`, `PREREG_rules_k.md`, `RESULTS_rules_k.md` | route 16: the same neighbours, continuous best-response shifts, speed swaps and kicks (interim) |
| `polish_l.py`, `test_polish_l.py`, `PREREG_rules_l.md` | route 17: exact one-added-runner decision for Callens's cover; exact max-margin polish (minimum cycle mean) of near-covers |
| `slr_br.py`, `test_slr_br.py`, `test_slr_br_gap.py`, `job_br.py`, `PREREG_br.md`, `RESULTS_br.md` | route 4: best-response search with exact Fraction check; n = 18, 19, 20 certified (not new) |
| `slr_sbr.py`, `test_slr_sbr.py`, `test_external_certs.py`, `PREREG_sbr.md`, `RESULTS_sbr.md` | route 5: best response over speed and shift; re-check of the published 18..54 certificates |
| `slr_lp.py`, `test_slr_lp.py`, `PREREG_lp.md`, `RESULTS_lp.md` | route 6: minimax polish by difference constraints, speed swaps, rigid time shifts; n = 55 |
| `slr_chain.py`, `test_slr_chain.py`, `PREREG_chain.md`, `RESULTS_chain.md` | route 7: warm chain from the n = 55 certificate (stalled at 56) |
| `slr_grid.py`, `test_slr_grid.py`, `PREREG_grid.md`, `RESULTS_grid.md` | route 8: bitset grid annealing with speed moves (stalled at 56) |
| `slr_consec.py`, `test_slr_consec.py`, `PREREG_consec.md`, `RESULTS_consec.md` | route 9: slack-carrying chain on consecutive speeds 1..n (stalled at 23) |

A certificate is (v, s, R) such that the arcs {t : ||v_i t + s_i|| < R} cover the
circle; then every time t has some runner closer than R to the origin, so with
R <= 1/(n+1) the shifted conjecture fails for v. In `certs_lp.json` the shifts are
`shift_num[i] / shift_den`.

```
python -m unittest -v test_certs_lp           # the n = 55 counterexample, seconds
python -m unittest -v test_slr test_rules test_rules_m test_rules_s test_rules_c test_rules_d test_rules_e test_rules_f test_rules_g test_rules_h test_rules_i test_descent_j test_descent_k test_polish_l test_slr_br test_slr_sbr test_slr_lp test_slr_chain test_slr_grid test_slr_consec
python -m unittest -v test_slr_br_gap        # n = 18, 19, 20; a few minutes
python -m unittest -v test_external_certs    # needs network
pip install ortools && python descent_j.py --out-dir out --minutes 120
python descent_k.py --out-dir out --minutes 120   # standard library only
python polish_l.py --out-dir out --minutes 120    # standard library only
```

## Credit

The shifted conjecture's first counterexamples and the exact values of gamma_sh(1..n),
including the n = 5 and n = 11 configurations route 9 starts from, are Blanco, Criado and
Santos's. The counterexamples for 18..54 are aadrianvv's, and so are the ideas of warm chains,
speed changes, grid-cell annealing, an LP polish (which route 17 makes exact) and rigid time
shifts. Those for 55, 56 and 57
are tomdif's. The quantity E_n, the uniform-rule method, the 9 -> 8 rules and the result for
n >= 95 are Poliakova's. The question is Zhang's. The m = 2 rule-search negatives that routes 11
and 12 build on are tomdif's (`rule3.py`, `rule4.py`) and aadrianvv's (structured patch, issue
110). aadrianvv also ran the first fixed-n search on Poliakova's even base, the idea route 13
extends, and listed bases of multiples of 3 or 6 as a direction to try (issue 110,
2026-11-21), without reporting a result. The one-runner extension bound for n = 57 is
F1Justin's (PR 850), and so is the idea of bounding extensions of a fixed cover (PR 1017), which
route 17's part A applies to Callens's cover.
The n = 63 counterexample, the first inside 58..94, and the observation that its menu fails for
N = 60..63 and 65..95 are Xavier Callens's (Zenodo 24051700 and 24132291; CC BY 4.0); routes 15
to 17 start from his certificate `cert_n063.json`, and the choice of smooth N in routes 13b and
14 follows from his work.
