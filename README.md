# shifted-lonely-runner

Does the **shifted Lonely Runner Conjecture** fail for every number of runners n >= 5?
Counterexamples are known for 5 <= n <= 17 (Blanco, Criado and Santos,
[arXiv:2603.24784](https://arxiv.org/abs/2603.24784)), for 18 <= n <= 54 (aadrianvv with
Claude, published 2026-11-22), for n = 55, 56 and 57 (tomdif, published 2026-11-25; all in
[1337isnot1337/solved-conjectures](https://github.com/1337isnot1337/solved-conjectures/tree/main/results/shifted-lonely-runner-counterexamples),
unrefereed; 18..57 Lean-checked there in PR 755), and for n >= 95 (Poliakova,
[arXiv:2609.23952](https://arxiv.org/abs/2609.23952)). Counterexamples for the remaining cases
would answer the first part of Zhang's question
([arXiv:2608.13599](https://arxiv.org/abs/2608.13599), Question 8.5) of whether it fails for
every n >= 5. This repository searches for them and checks every candidate exactly.

By MV2 of Munim, Inc. (mv2@munimtech.com). Code Apache-2.0; text and data CC BY 4.0.
The code and text were made with AI agents working in MV2's name. No human expert has
checked them yet.

## Status (2026-11-26, 05:00 UTC)

- **Open: 58 <= n <= 94** (checked 2026-11-26: arXiv, GitHub, solved-conjectures pull requests).
- **No new case from this repository.** Our n = 55 (`certs_lp.json`, commit 9276b4f,
  E = +0.116) was found on the same day as tomdif's; we count it as an independent certificate,
  not as a new case. Routes 1 and 4-9 are graded; none reached the open range.
- **Route 10 (new, pre-registered in [PREREG_rules_s.md](PREREG_rules_s.md)).** One local rule
  of Poliakova's kind with gain 1 and threshold at most 58 would settle all of 58..94 at once.
  Route 10 searches only at that size (largest speed L = 59 m on a base of multiples of m), over
  smooth speeds, so that CP-SAT can decide each menu rather than time out. It runs as three
  test-gate probes and the compete job `slr-rules-s-v1`.
- Routes 2 and 3 (compete jobs for Poliakova-type rules over all speeds, climbing L from 16)
  are still waiting for compute.
- Independent re-check of the published 18..54 certificates: all 37 pass MV2's three exact
  checkers (`test_external_certs.py`, commit c702698).

## What is here

| file | what it does |
|---|---|
| `certs_lp.json`, `test_certs_lp.py` | our n = 55 counterexample and its exact re-check by four checkers |
| `slr.py` | two independent exact certificate checkers (Fractions sweep; integer endpoint test) and the float search |
| `test_slr.py` | standard-library tests; every expected value is proved by hand in a comment |
| `job_slr.py`, `PREREG.md`, `RESULTS_gap.md` | route 1: direct search, n = 18..94 (certified 18-25, 27; not new) |
| `rules.py`, `rule_search.py`, `test_rules.py`, `job_rules.py`, `PREREG_rules.md` | route 2: Poliakova-type local rules (exact criterion with proof, CP-SAT search) |
| `rules_m.py`, `rule_search_m.py`, `test_rules_m.py`, `job_rules_m.py`, `PREREG_rules_m.md` | route 3: local rules on a base of multiples of m |
| `rule_search_s.py`, `test_rules_s.py`, `job_rules_s.py`, `PREREG_rules_s.md` | route 10: local rules at threshold 58 over smooth speeds, then certificates for every n they reach |
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
python -m unittest -v test_slr test_rules test_rules_m test_rules_s test_slr_br test_slr_sbr test_slr_lp test_slr_chain test_slr_grid test_slr_consec
python -m unittest -v test_slr_br_gap        # n = 18, 19, 20; a few minutes
python -m unittest -v test_external_certs    # needs network
pip install "ortools>=9.10" && python job_rules_s.py --out-dir out --minutes 120
```

## Credit

The shifted conjecture's first counterexamples and the exact values of gamma_sh(1..n),
including the n = 5 and n = 11 configurations route 9 starts from, are Blanco, Criado and
Santos's. The counterexamples for 18..54 are aadrianvv's, and so are the ideas of warm chains,
speed changes, grid-cell annealing, an LP polish and rigid time shifts. Those for 55, 56 and 57
are tomdif's. The quantity E_n, the uniform-rule method, the 9 -> 8 rules and the result for
n >= 95 are Poliakova's. The question is Zhang's.
