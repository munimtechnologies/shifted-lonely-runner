# shifted-lonely-runner

Does the **shifted Lonely Runner Conjecture** fail for every number of runners n >= 5?
It is known to fail for 5 <= n <= 17 (Blanco, Criado and Santos,
[arXiv:2603.24784](https://arxiv.org/abs/2603.24784)) and for n >= 95 (Poliakova,
[arXiv:2609.23952](https://arxiv.org/abs/2609.23952)). Poliakova notes that
counterexamples for 18 <= n <= 94 would settle Zhang's question
([arXiv:2608.13599](https://arxiv.org/abs/2608.13599), Question 9.4) of whether it fails for
every n >= 5. This repository searches for them and checks every candidate exactly.

By MV2 of Munim, Inc. (mv2@munimtech.com). Code Apache-2.0; text and data CC BY 4.0.
The code and text were made with AI agents working in MV2's name. No human expert has
checked them yet.

## Status (2026-11-25)

Two independent routes, both pre-registered, **no result yet**:

1. **Direct search** (`PREREG.md`, job `slr-gap-v1`): a float search for shifts of
   (1..n) and nearby speed sets, every candidate re-checked exactly.
2. **Small local rules** (`PREREG_rules.md`, job `slr-rules-v1`, added 2026-11-25).
   Poliakova's n >= 95 comes from one "9 -> 8" rule that edits the even speeds 2, 4, ..., 2N
   and touches speeds up to 192, which is why it needs n >= 95. A gain-1 rule touching only
   speeds up to L works for every n >= L/2 - 1. `rules.py` states and proves an exact local
   criterion for such rules; `rule_search.py` searches for rules with small L as a CP-SAT
   problem. A rule with L <= 38 would close the whole gap 18..94.

Prior work searched on 2026-11-24 and again on 2026-11-25 (web and arXiv: "shifted lonely
runner conjecture counterexample all n", "lonely runner conjecture sixteen runners arXiv";
the papers above; arXiv:2610.40694, which is about unshifted four-runner spectra; the
authors' code at github.com/criado/shifted_lonely_runner_conjecture_counterexample, whose
`output/` lists (1..n) up to n = 13): nothing covers 18 <= n <= 94.

## What is here

| file | what it does |
|---|---|
| `slr.py` | two independent exact certificate checkers (Fractions sweep; integer endpoint test) and the float search |
| `test_slr.py` | standard-library tests; every expected value is proved by hand in a comment |
| `job_slr.py` | job 1: sanity checks on published n = 5 data, validation for n = 5..17, main search n = 18..94, retries |
| `PREREG.md` | pre-registration of job 1 |
| `rules.py` | local rules: the exact criterion with its proof, Poliakova's two 9 -> 8 rules, full-configuration builder |
| `rule_search.py` | CP-SAT encoding of the criterion (needs `ortools`; only the solver call does) |
| `test_rules.py` | tests: Poliakova's rules pass, broken variants fail where they should, her n = 95 configuration passes both global checkers, encoder cases worked by hand |
| `job_rules.py` | job 2: sanity checks, rule search over L = 16..128, global certificates for every n the rule reaches |
| `PREREG_rules.md` | pre-registration of job 2 |

A certificate is (v, s, R) such that the open arcs {t : ||v_i t + s_i|| < R} cover the
circle; then every time t has some runner closer than R to the origin, so with
R < 1/(n+1) the shifted conjecture fails for v. Job 1 stores shifts as integers P with
s = P / 2^48; job 2 stores them as exact fractions.

```
python -m unittest -v test_slr test_rules
python job_slr.py --out-dir out --minutes 200 --workers 2
pip install "ortools>=9.10,<10"
python job_rules.py --out-dir out --minutes 290 --workers 2
```

## Credit

The conjecture's shifted form and its first counterexamples, the exact values of
gamma_sh(1..n) used as sanity checks, and the published n = 5 certificates are Blanco,
Criado and Santos's. The quantity E_n, the uniform-rule method, the 9 -> 8 rules and the
result for n >= 95 are Poliakova's; job 2 only searches for smaller rules of her kind. The
question is Zhang's.
