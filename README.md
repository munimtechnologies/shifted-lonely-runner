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

## Status (2026-11-24)

- `PREREG.md`: the pre-registered job `slr-gap-v1`, its sanity checks and predictions,
  written before it ran. **No result yet.**
- Prior work searched on 2026-11-24 (web and arXiv: "shifted lonely runner conjecture
  false for all n counterexamples 18 94", "\"shifted lonely runner\" counterexample 2026";
  the papers above; the authors' code at
  github.com/criado/shifted_lonely_runner_conjecture_counterexample, whose `output/`
  lists (1..n) up to n = 13): nothing covers 18 <= n <= 94.

## What is here

| file | what it does |
|---|---|
| `slr.py` | two independent exact certificate checkers (Fractions sweep; integer endpoint test) and the float search |
| `test_slr.py` | standard-library tests; every expected value is proved by hand in a comment |
| `job_slr.py` | the job: sanity checks on published n = 5 data, validation for n = 5..17, main search n = 18..94, retries |
| `PREREG.md` | pre-registration |

A certificate is (v, s, R) such that the open arcs {t : ||v_i t + s_i|| < R} cover the
circle; then every time t has some runner closer than R to the origin, so with
R < 1/(n+1) the shifted conjecture fails for v. Shifts are stored as integers P with
s = P / 2^48.

```
python -m unittest -v test_slr
python job_slr.py --out-dir out --minutes 200 --workers 2
```

## Credit

The conjecture's shifted form and its first counterexamples, the exact values of
gamma_sh(1..n) used as sanity checks, and the published n = 5 certificates are Blanco,
Criado and Santos's. The quantity E_n and the result for n >= 95 are Poliakova's. The
question is Zhang's. This repository only searches the remaining range.
