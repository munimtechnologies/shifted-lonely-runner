# Pre-registration: best-response route (slr_br.py), written 2026-11-25 before its first run

By MV2 of Munim, Inc. Made with AI agents working in MV2's name; no human expert has
checked it. Text CC BY 4.0.

## Why a fourth route

The three earlier routes (PREREG.md, PREREG_rules.md, PREREG_rules_m.md) are compete jobs
that have waited for free memory on MV2's machines since 2026-11-24. `slr_br.py` is a small
standard-library search that runs inside the repository's own test gate (`test_slr_br_gap.py`),
so the smallest open cases can be tried now.

## Method

- Speeds 1..n. Certificate radius R = 1/(n+1) - 1/10^11, so R < 1/(n+1).
- `find_cover` (float): best-response dynamics. Each runner in turn takes the shift that
  covers the largest measure of what the other runners leave uncovered; that optimum is
  computed exactly among the breakpoints of a piecewise-linear function. Radius continuation
  from 1.25 R down to R (2% steps, halved on failure), random kicks, restarts. Deterministic
  for seed 1; time limit 150 s per n in the gate (60 s for the n = 8 sanity case).
- `exact_cover` (Fractions): re-checks the exact binary values of the float shifts at R.
  Nothing is claimed for an n unless this check passes.

## Sanity checks (in test_slr_br.py; if one fails nothing below is graded)

- **B0a** Speeds 1..n with zero shifts cover the circle at radius exactly 1/(n+1) and not
  at 1/(n+1) - 10^-6 (Dirichlet; n = 1..13).
- **B0b** Float and exact coverage agree on 300 random configurations; the best response
  is at least as good as every shift on a 400-point grid.
- **B1** The search certifies n = 8 (gamma_sh(1..8) = 1/10 < 1/9 by Blanco, Criado and
  Santos, so a certificate exists). Predicted: **yes** (about 85%).

## Predictions for the open cases (test_slr_br_gap.py)

- **B2** n = 18 certified. Predicted: **yes**, about 45%. Blanco-Criado-Santos' exact values
  give gamma_sh(1..n)(n+1) between 0.85 and 0.89 for n = 9..15, slowly rising; if the trend
  holds to n = 18, a cover at R exists with about 10% to spare, but a heuristic may miss it.
- **B3** n = 19 certified. Predicted: **yes**, about 40%.
- **B4** n = 20 certified. Predicted: **yes**, about 35%.

The gate commits `test_slr_br_gap.py` only if all three pass, so a commit means all three
are certified. If the gate fails, its output (best radius ratio reached for each n) is
recorded in RESULTS and the route is changed, not the predictions.

## What will be claimed

Only n whose shifts pass `exact_cover` at R < 1/(n+1): then max_t min_i ||i t + s_i|| <= R
< 1/(n+1), a counterexample to the shifted conjecture for n runners. A failure of the
heuristic says nothing about whether such shifts exist.
