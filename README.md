# shifted-lonely-runner

Does the **shifted Lonely Runner Conjecture** fail for every number of runners n >= 5?
Counterexamples are known for 5 <= n <= 17 (Blanco, Criado and Santos,
[arXiv:2603.24784](https://arxiv.org/abs/2603.24784)), for 18 <= n <= 54 (aadrianvv with
Claude, published 2026-11-22 in
[1337isnot1337/solved-conjectures](https://github.com/1337isnot1337/solved-conjectures/tree/main/results/shifted-lonely-runner-counterexamples),
unrefereed) and for n >= 95 (Poliakova, [arXiv:2609.23952](https://arxiv.org/abs/2609.23952)).
Counterexamples for the remaining **55 <= n <= 94** would answer the first part of Zhang's
question ([arXiv:2608.13599](https://arxiv.org/abs/2608.13599), Question 9.4 / 8.5) of
whether it fails for every n >= 5. This repository searches for them and checks every
candidate exactly.

By MV2 of Munim, Inc. (mv2@munimtech.com). Code Apache-2.0; text and data CC BY 4.0.
The code and text were made with AI agents working in MV2's name. No human expert has
checked them yet.

## Status (2026-11-25)

- **Route 4 graded** (`RESULTS_br.md`): MV2's best-response search certified speeds 1..n
  for n = 18, 19 and 20 in the repository's test gate, as pre-registered. These are **not
  new**: counterexamples for 18..54 had been published three days earlier (link above),
  which MV2's prior-work searches missed. They are an independent re-finding only.
- **Route 5** (`PREREG_sbr.md`, `slr_sbr.py`): best response over speed and shift,
  warm-started from the published n = 54 certificate, aimed at n = 55 and up; plus an
  independent exact re-check of all 37 published certificates (`test_external_certs.py`).
  No result yet.
- Routes 1-3 (compete jobs) are still waiting for compute. Routes 2 and 3 search for small
  Poliakova-type local rules; the 18..54 authors report an exhaustive search showing that
  no gain-1 rule over the primes {2, 3} or {2, 3, 5} has L <= 190, so those jobs are
  expected to find nothing in those menus.

Prior work searched on 2026-11-24 and 2026-11-25 (arXiv "lonely runner" listing, newest
first, 46 results, newest 2610.40694; web searches for the shifted conjecture and for
counterexamples at n = 18..20; GitHub, including the code of Blanco, Criado and Santos and
the 18..54 repository above).

## What is here

| file | what it does |
|---|---|
| `slr.py` | two independent exact certificate checkers (Fractions sweep; integer endpoint test) and the float search |
| `test_slr.py` | standard-library tests; every expected value is proved by hand in a comment |
| `job_slr.py`, `PREREG.md` | route 1: direct search, n = 18..94 |
| `rules.py`, `rule_search.py`, `test_rules.py`, `job_rules.py`, `PREREG_rules.md` | route 2: Poliakova-type local rules (exact criterion with proof, CP-SAT search) |
| `rules_m.py`, `rule_search_m.py`, `test_rules_m.py`, `job_rules_m.py`, `PREREG_rules_m.md` | route 3: local rules on a base of multiples of m |
| `slr_br.py`, `test_slr_br.py`, `test_slr_br_gap.py`, `job_br.py`, `PREREG_br.md`, `RESULTS_br.md` | route 4: best-response search with exact Fraction check; n = 18, 19, 20 certified (not new) |
| `slr_sbr.py`, `test_slr_sbr.py`, `test_external_certs.py`, `PREREG_sbr.md` | route 5: best response over speed and shift for n >= 55; re-check of the published 18..54 certificates |

A certificate is (v, s, R) such that the arcs {t : ||v_i t + s_i|| <= R} cover the
circle; then every time t has some runner within R of the origin, so with
R < 1/(n+1) the shifted conjecture fails for v.

```
python -m unittest -v test_slr test_rules test_rules_m test_slr_br test_slr_sbr
python -m unittest -v test_slr_br_gap        # n = 18, 19, 20; a few minutes
python -m unittest -v test_external_certs    # needs network
```

## Credit

The shifted conjecture's first counterexamples and the exact values of gamma_sh(1..n) are
Blanco, Criado and Santos's. The counterexamples for 18..54 are aadrianvv's. The quantity
E_n, the uniform-rule method, the 9 -> 8 rules and the result for n >= 95 are Poliakova's.
The question is Zhang's.
