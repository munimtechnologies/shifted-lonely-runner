# shifted-lonely-runner

Does the **shifted Lonely Runner Conjecture** fail for every number of runners n >= 5?
Counterexamples are known for 5 <= n <= 17 (Blanco, Criado and Santos,
[arXiv:2603.24784](https://arxiv.org/abs/2603.24784)), for 18 <= n <= 54 (aadrianvv with
Claude, published 2026-11-22 in
[1337isnot1337/solved-conjectures](https://github.com/1337isnot1337/solved-conjectures/tree/main/results/shifted-lonely-runner-counterexamples),
unrefereed) and for n >= 95 (Poliakova, [arXiv:2609.23952](https://arxiv.org/abs/2609.23952)).
Counterexamples for the remaining cases would answer the first part of Zhang's
question ([arXiv:2608.13599](https://arxiv.org/abs/2608.13599), Question 9.4 / 8.5) of
whether it fails for every n >= 5. This repository searches for them and checks every
candidate exactly.

By MV2 of Munim, Inc. (mv2@munimtech.com). Code Apache-2.0; text and data CC BY 4.0.
The code and text were made with AI agents working in MV2's name. No human expert has
checked them yet.

## Status (2026-11-25, 11:45 UTC)

- **n = 55 is certified** (`certs_lp.json`, `RESULTS_lp.md`): the 54 speeds of the published
  n = 54 counterexample plus a runner of speed 195, with all 55 shifts re-optimised by
  route 6's polish. The open arcs of radius 10/561 = 1/56.1 cover the circle, so the
  loneliness is below 1/56; four exact checkers agree (`test_certs_lp.py`). Float value:
  1/gamma = 56.116 (E = +0.116; the best earlier value at n = 55 was E = -0.012).
- **Open now: 56 <= n <= 94.** Scoop check on 2026-11-25 (~11:10-11:25 UTC): nothing for
  55..94 in the 18..54 repository or its issue #110, GitHub, arXiv or the web.
- **Route 7** (`slr_chain.py`, `PREREG_chain.md`): a warm chain n -> n + 1 from the n = 55
  certificate with the same polish; three probes pre-registered.
- Route 6 (`slr_lp.py`): a polish that moves all shifts at once. Each hole's height changes by
  w (x_R - x_L) when runners' arcs move by x_i in time, so lowering the highest hole is a
  system of difference constraints, solved by Bellman-Ford with no LP library.
- Independent re-check of the published 18..54 certificates: all 37 pass MV2's three exact
  checkers (`test_external_certs.py`, commit c702698).
- Routes 1-3 (compete jobs) are still waiting for compute; routes 4 and 5 are graded
  (`RESULTS_br.md`, `RESULTS_sbr.md`).

## What is here

| file | what it does |
|---|---|
| `certs_lp.json`, `test_certs_lp.py` | **new counterexamples** (n = 55) and their exact re-check by four checkers |
| `slr.py` | two independent exact certificate checkers (Fractions sweep; integer endpoint test) and the float search |
| `test_slr.py` | standard-library tests; every expected value is proved by hand in a comment |
| `job_slr.py`, `PREREG.md` | route 1: direct search, n = 18..94 |
| `rules.py`, `rule_search.py`, `test_rules.py`, `job_rules.py`, `PREREG_rules.md` | route 2: Poliakova-type local rules (exact criterion with proof, CP-SAT search) |
| `rules_m.py`, `rule_search_m.py`, `test_rules_m.py`, `job_rules_m.py`, `PREREG_rules_m.md` | route 3: local rules on a base of multiples of m |
| `slr_br.py`, `test_slr_br.py`, `test_slr_br_gap.py`, `job_br.py`, `PREREG_br.md`, `RESULTS_br.md` | route 4: best-response search with exact Fraction check; n = 18, 19, 20 certified (not new) |
| `slr_sbr.py`, `test_slr_sbr.py`, `test_external_certs.py`, `PREREG_sbr.md`, `RESULTS_sbr.md` | route 5: best response over speed and shift; re-check of the published 18..54 certificates |
| `slr_lp.py`, `test_slr_lp.py`, `PREREG_lp.md`, `RESULTS_lp.md` | route 6: minimax polish by difference constraints, speed swaps, rigid time shifts; certified n = 55 |
| `slr_chain.py`, `test_slr_chain.py`, `PREREG_chain.md` | route 7: warm chain from the n = 55 certificate |

A certificate is (v, s, R) such that the arcs {t : ||v_i t + s_i|| < R} cover the
circle; then every time t has some runner closer than R to the origin, so with
R <= 1/(n+1) the shifted conjecture fails for v. In `certs_lp.json` the shifts are
`shift_num[i] / shift_den`.

```
python -m unittest -v test_certs_lp           # the n = 55 counterexample, seconds
python -m unittest -v test_slr test_rules test_rules_m test_slr_br test_slr_sbr test_slr_lp test_slr_chain
python -m unittest -v test_slr_br_gap        # n = 18, 19, 20; a few minutes
python -m unittest -v test_external_certs    # needs network
```

## Credit

The shifted conjecture's first counterexamples and the exact values of gamma_sh(1..n) are
Blanco, Criado and Santos's. The counterexamples for 18..54, and the ideas of warm chains,
speed changes, an LP polish and rigid time shifts, are aadrianvv's; the n = 55 certificate
here starts from their n = 54 configuration. The quantity E_n, the uniform-rule method, the
9 -> 8 rules and the result for n >= 95 are Poliakova's. The question is Zhang's.
