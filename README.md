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

## Status (2026-11-27, 23:00 UTC)

- **Open: 58 <= n <= 62 and 64 <= n <= 94.** Re-checked 2026-11-27 about 22:45 UTC: the Zenodo
  API, arXiv's newest listings and solved-conjectures pull requests (F1Justin's PR 850, merged,
  and PR 1017, open). Nothing claims a case in 58..62 or 64..94.
- **No new case from this repository.** Our n = 55 (`certs_lp.json`, commit 9276b4f) was found
  on the same day as tomdif's; we count it as an independent certificate, not as a new case.
- **A smaller n = 63 cover** (`cover_n063_simple.json`, below). It touches 11 speeds of the
  base where Callens's certificate touches 18. It is Poliakova's 9 -> 8 rule cut off at
  2N = 128 by the top trick. n = 63 is Callens's case; this is a second certificate, not a new
  case.
- **Route 19 closed** ([RESULTS_rules_o.md](RESULTS_rules_o.md)): calibrated and sound, but 0 of
  37 targets decided. **Route 19b, interim** ([RESULTS_rules_p.md](RESULTS_rules_p.md)): a
  feasibility-only solver did not help. Almost every call on a target still ran out of time.
- **Route 19c (new, pre-registered in [PREREG_rules_q.md](PREREG_rules_q.md)).** The same exact
  search (`top_q.py`) in the small menu that both known gain-1 rules use (s0 in quarters, beta
  in halves of delta). Targets: n = N - 1 for N = 59..95 and gain 2 at N = 64 and 96.
- **Routes 15-18 closed** ([RESULTS_rules_j.md](RESULTS_rules_j.md),
  [RESULTS_rules_k.md](RESULTS_rules_k.md), [RESULTS_rules_l.md](RESULTS_rules_l.md),
  [RESULTS_rules_n.md](RESULTS_rules_n.md)). Local searches around Callens's and Poliakova's
  covers for n = 61, 62, 64 and 94 all ended at configurations that touch exactly. Every
  blocking cycle is a pair of speeds summing to 2(n + 1), a rigid pair (below).
- **Earlier routes** (2-14): see the table below and their RESULTS files. Independent re-check of
  the published 18..54 certificates: all 37 pass MV2's three exact checkers
  (`test_external_certs.py`, commit c702698).

## A smaller n = 63 cover: Poliakova's 9 -> 8 rule with a top trick

On the base 2, 4, ..., 128 at shift 0 (delta = 1/65): remove 8, 32 and 96; rephase 12, 24 and
48 to 1/2 + delta/2, 16 to -3 delta/2, 64 to -delta and 128 to +delta; add 3 and 9 at 3/4.
These 63 runners' open arcs of radius 1/64 cover the circle (`test_cover_n063_simple.py`: a
fresh Fraction endpoint checker, both checkers of `slr.py`, `top_q.indep_cover` and the fixed-N
criterion all accept it). Compare Poliakova's 9 -> 8 rule, which works for every N >= 96: remove
8, 32 and 192; rephase 12, 24, 48 and 96 to 1/2 + delta/2 and 16, 64 to -delta; add 3 and 9 at
1/4. At N = 64 there is no 192. 96 is removed instead of rephased, 128 at +delta takes over
the top, and the slack between delta and 1/64 closes what is left. Route 19b's search found it
from scratch in 8 s (sanity tier ph64).

## How Callens's n = 63 cover works: a top trick

On the base 2, 4, ..., 128 (delta = 1/65), Callens's certificate removes 4, 8, 32, 72, 96, 108,
rephases 12, 24, 36 by (1 + delta)/2, 48 by (1 - delta)/2, 16 and 128 by -delta and 64 by
+delta, and adds 1, 3, 9, 27, 81 at 3/4 + (small) delta. Read with Poliakova's locality proof:
the odd runners w and 3w at about 3/4 cover the times for which 4w is responsible, so 4, 12, 36
and 108 are free; 36 at 1/2 covers 72; 12, 24, 48 at about 1/2 cover 96 and give the 3q/2
helpers of the chain 8, 16, 32, 64, 128. What a uniform rule cannot do is the end: 128 = 2N at
-delta leaves part of its own times open, and no larger speed exists. The slack closes them:
for t in [1/130, 1/128], speed 2 is within delta (1 + delta) up to t = 33/4225 and speed 128
from there on, meeting at radius exactly 66/4225 = delta (1 + delta) < 1/64. A rule for a single
N may use this; Poliakova's rules, which work for every N, may not. `top_o.fixed_check` turns
this into an exact test at a fixed N that counts every runner, near misses included.

## Facts used, with proofs

**No single added runner covers every class of a touched base speed q** (route 12). The classes
are k in [0, q) with gcd(k, q/m) = 1. With j = q/m, their differences generate 1 if j is odd and
2 if j is even. A runner of speed w covers class k only if (w/q) k + s0 is an integer, so one
runner covering all classes needs (w/q) * 1 or (w/q) * 2 to be an integer. Then w is a multiple
of m: a base speed, not an added one.

**Multiplying every speed of a cover by an integer k keeps it a cover with the same shifts**
(route 14): at time t the scaled runners sit where the old ones sit at time k t.

**k runners that cover at radius 1/(n+1) give a counterexample for n whenever k <= n**
(routes 15-19): extra runners at shift 0 only add arcs.

**For a fixed chain of arcs, the best overlap margin is a minimum cycle mean** (route 17).
Runner i, lift k covers ((k - s_i - R)/v_i, (k - s_i + R)/v_i). With x_i = s_i / v_i, the two
overlaps of consecutive chain arcs A, B are c1 - x_A + x_B and c2 - x_B + x_A with c1, c2
independent of the shifts, so "every overlap >= eps" is a system of difference constraints;
the largest eps is the minimum cycle mean of the weights c.

**Rigid pairs** (route 18). If runners of speeds a and b meet twice in a chain (A_k before B_m,
and B_m' before A_k'), the sum of the two overlaps is 2R(a + b)/(ab) + (b(k - k') +
a(m' - m))/(ab), whatever the shifts. The second numerator runs over the multiples of
g = gcd(a, b), so at R = 1/(n + 1) the sum can be exactly 0 only if (n + 1) g divides 2(a + b).
Then the two contacts can never both overlap.

**Fixed-N criterion** (route 19, proof in `top_o.py`): a rule on the base 2, ..., 2N is a closed
cover at radius r = rho/(N + 1), rho >= 1, if and only if, for every touched q, class k and z in [-1, 1],
some runner (speed w, shift s0 + beta/(N + 1)) and integer J satisfy
|(x - J)(N + 1) + (w/q) z + beta| <= rho with x = (w/q) k + s0.

**Endpoint criterion** (`top_q.indep_cover`): finitely many open arcs cover the circle if and
only if every arc endpoint lies inside some arc. If a point is missed, the uncovered set is
closed, non-empty and not the whole circle, so it has a boundary point, and that point is an
arc endpoint.

## What is here

| file | what it does |
|---|---|
| `certs_lp.json`, `test_certs_lp.py` | our n = 55 counterexample and its exact re-check by four checkers |
| `cover_n063_simple.json`, `test_cover_n063_simple.py` | the smaller n = 63 cover and its exact re-check by four checkers |
| `slr.py` | two independent exact certificate checkers (Fractions sweep; integer endpoint test) and the float search |
| `test_slr.py` | standard-library tests; every expected value is proved by hand in a comment |
| `job_slr.py`, `PREREG.md`, `RESULTS_gap.md` | route 1: direct search, n = 18..94 (certified 18-25, 27; not new) |
| `rules.py`, `rule_search.py`, `test_rules.py`, `job_rules.py`, `PREREG_rules.md` | route 2: Poliakova-type local rules (exact criterion with proof, CP-SAT search) |
| `rules_m.py`, `rule_search_m.py`, `test_rules_m.py`, `job_rules_m.py`, `PREREG_rules_m.md` | route 3: local rules on a base of multiples of m |
| `rule_search_s.py`, `test_rules_s.py`, `job_rules_s.py`, `PREREG_rules_s.md`, `RESULTS_rules_s.md` | route 10: local rules at threshold 58 over smooth speeds (graded) |
| `rule_search_c.py`, `test_rules_c.py`, `job_rules_c.py`, `fetch_deps_c.py`, `PREREG_rules_c.md` | route 11: counterexample-guided exact search for rules on bases of multiples of 3, 4, 6, 12 |
| `rule_search_d.py`, `test_rules_d.py`, `job_rules_d.py`, `fetch_deps_d.py`, `PREREG_rules_d.md` | route 11b: the same search in feasibility mode |
| `rule_search_e.py`, `test_rules_e.py`, `job_rules_e.py`, `fetch_deps_e.py`, `PREREG_rules_e.md`, `RESULTS_rules_e.md` | route 11c: cubes by the largest touched speed |
| `rule_search_f.py`, `test_rules_f.py`, `fetch_deps_f.py`, `PREREG_rules_f.md`, `RESULTS_rules_f.md` | route 12: Poliakova's gadget fixed, the rest searched (graded) |
| `rule_search_g.py`, `test_rules_g.py`, `fetch_deps_g.py`, `PREREG_rules_g.md`, `RESULTS_rules_g.md` | route 13: exact fixed-n search for a 94-runner counterexample (CEGAR over time points) |
| `rule_search_h.py`, `test_rules_h.py`, `PREREG_rules_h.md`, `RESULTS_rules_h.md` | route 13b: incremental SAT (graded: failed its sanity tier) |
| `rule_search_i.py`, `test_rules_i.py`, `PREREG_rules_i.md`, `RESULTS_rules_i.md` | route 14: fixed-n CP-SAT at smooth N with a scaled Poliakova hint (graded) |
| `descent_j.py`, `test_descent_j.py`, `PREREG_rules_j.md`, `RESULTS_rules_j.md` | route 15: delete from or add to the known covers, shifts re-tuned on a grid (graded) |
| `descent_k.py`, `test_descent_k.py`, `PREREG_rules_k.md`, `RESULTS_rules_k.md` | route 16: continuous best-response shifts, speed swaps and kicks (graded) |
| `polish_l.py`, `test_polish_l.py`, `PREREG_rules_l.md`, `RESULTS_rules_l.md` | route 17: exact one-added-runner decision; exact max-margin polish (graded) |
| `climb_n.py`, `test_climb_n.py`, `PREREG_rules_n.md`, `RESULTS_rules_n.md` | route 18: climb of the exact margin; rigid-pair lemma (graded) |
| `top_o.py`, `test_top_o.py`, `PREREG_rules_o.md`, `RESULTS_rules_o.md` | route 19: exact fixed-N criterion with the slack radius; complete CEGAR over 3-smooth menus for N = 59..96 (graded, closed) |
| `top_p.py`, `test_top_p.py`, `PREREG_rules_p.md`, `RESULTS_rules_p.md` | route 19b: route 19 with a feasibility-only solver (interim grade) |
| `top_q.py`, `test_top_q.py`, `PREREG_rules_q.md` | route 19c: the same search in the small menu of the two known gain-1 rules; third exact checker |
| `slr_br.py`, `test_slr_br.py`, `test_slr_br_gap.py`, `job_br.py`, `PREREG_br.md`, `RESULTS_br.md` | route 4: best-response search; n = 18, 19, 20 certified (not new) |
| `slr_sbr.py`, `test_slr_sbr.py`, `test_external_certs.py`, `PREREG_sbr.md`, `RESULTS_sbr.md` | route 5: best response over speed and shift; re-check of the published 18..54 certificates |
| `slr_lp.py`, `test_slr_lp.py`, `PREREG_lp.md`, `RESULTS_lp.md` | route 6: minimax polish by difference constraints; n = 55 |
| `slr_chain.py`, `test_slr_chain.py`, `PREREG_chain.md`, `RESULTS_chain.md` | route 7: warm chain from the n = 55 certificate (stalled at 56) |
| `slr_grid.py`, `test_slr_grid.py`, `PREREG_grid.md`, `RESULTS_grid.md` | route 8: bitset grid annealing (stalled at 56) |
| `slr_consec.py`, `test_slr_consec.py`, `PREREG_consec.md`, `RESULTS_consec.md` | route 9: slack-carrying chain on consecutive speeds (stalled at 23) |

A certificate is (v, s, R) such that the open arcs {t : ||v_i t + s_i|| < R} cover the
circle; then every time t has some runner closer than R to the origin, so with
R <= 1/(n+1) the shifted conjecture fails for v.

```
python -m unittest -v test_certs_lp test_cover_n063_simple   # the n = 55 and n = 63 certificates
python -m unittest -v test_slr test_rules test_rules_m test_rules_s test_rules_c test_descent_j test_descent_k test_polish_l test_climb_n test_top_o test_top_p test_top_q
pip install ortools && python -c "import top_q; print(top_q.probe_q(budget=3600))"
```

## Credit

The shifted conjecture's first counterexamples and the exact values of gamma_sh(1..n) are
Blanco, Criado and Santos's. The counterexamples for 18..54 are aadrianvv's, and so are the
ideas of warm chains, speed changes, grid-cell annealing, an LP polish and rigid time shifts.
Those for 55, 56 and 57 are tomdif's. The quantity E_n, local rules, their locality proof, the
9 -> 8 rules and the result for n >= 95 are Poliakova's. The question is Zhang's. The m = 2
rule-search negatives that routes 11 and 12 build on are tomdif's (`rule3.py`, `rule4.py`) and
aadrianvv's (structured patch, issue 110). The one-runner extension bound for n = 57 and the
idea of bounding extensions of a fixed cover are F1Justin's (PR 850, PR 1017). The n = 63
counterexample, the first inside 58..94, and the observation that its menu fails for N = 60..63
and 65..95 are Xavier Callens's (Zenodo 24051700 and 24132291; CC BY 4.0); routes 15 to 19
start from his certificate `cert_n063.json`. Route 19's reading of his cover as a rule with a
top trick, and the smaller n = 63 cover read as Poliakova's 9 -> 8 rule at N = 64, are ours.
