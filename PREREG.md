# Pre-registration: shifted Lonely Runner counterexamples for 18 <= n <= 94 (job `slr-gap-v1`)

MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-11-24, before the job ran, by AI
agents working in MV2's name. No human expert has checked it. Text CC BY 4.0, code Apache-2.0.

## The question

The **shifted Lonely Runner Conjecture** (sLRC; attributed to Wills, first in print in
2019 as Conjecture 10 of reference [3] of arXiv:2603.24784) says: for n runners with distinct positive integer speeds
v_1..v_n and ANY starting positions s_1..s_n on a circle of length 1, some time t has every
runner at distance at least 1/(n+1) from the origin. In the notation of Blanco, Criado and
Santos, gamma_sh(v) >= 1/(n+1).

- It holds for n <= 4 (Alcantara, Criado and Santos, arXiv:2506.13379, for n = 4).
- It is **false for 5 <= n <= 17** (Blanco, Criado and Santos, arXiv:2603.24784,
  Prop. 5.14: gamma_sh(1, ..., n) < 1/(n+1)).
- It is **false for every n >= 95** (Poliakova, arXiv:2609.23952, Theorem 2: E_n >= 1).
- Poliakova writes: "finding counterexamples for the remaining 18 <= n <= 94 would
  establish that SLR is false for all n >= 5", which would answer the first part of
  Zhang's Question 9.4 (arXiv:2608.13599). As of 2026-11-24 we found no paper or
  repository that does this (searches listed in the README).

**This job asks: is there, for each n from 18 to 94, a speed vector of length n and shifts
whose open arcs of radius 1/(n+1) cover the whole circle?** If yes for all 77 values, then
together with the two papers above the sLRC is false for every n >= 5.

## Certificates (what counts as a counterexample)

A certificate is (v, s, R) with v distinct positive integers, s rationals with
denominator 2^48, R = 1/(n+1+e) with e > 0 rational, such that the open arcs
{t : ||v_i t + s_i|| < R} cover R/Z. Then gamma(v; s) < R < 1/(n+1). Each certificate is
checked by two exact methods in `slr.py` written independently of each other:
`covers_sweep` (Fractions, sweep over lifts of the arcs) and `covers_endpoints` (integer
arithmetic, "every endpoint of every arc lies strictly inside some arc"). A certificate
also gives the lower bound E_n > e, where (Poliakova) 1/(n+1+E_n) is the infimum of
gamma_sh over all speed vectors of length n.

The search itself (iterated local search over shifts, exact best response of one runner
at a time for the uncovered measure) is a float heuristic and proves nothing; only the
exact checks count.

## What the job does

1. `python -m unittest -v test_slr` (hand-proved cases; the job stops if any fails).
2. S0: the three published n = 5 shift vectors for (1,2,3,4,5) (paper Fig. 1, the
   authors' README, `output/consecutive.out` of github.com/criado/shifted_lonely_runner_conjecture_counterexample).
3. Validation: (1..n) for n = 5..17, 20 s per n plus up to 40 s of improvement.
4. Main: (1..n) for n = 18..94, 90 s for the first certificate (e = 1/20), then up to 45 s
   pushing e through 1/4, 1/2, 3/4, 1, 5/4, 3/2, 7/4, 2, 5/2, 3, 4, 5, 6, 8.
5. Retries for any n without a certificate: (1..n) with a new seed, then (2..n+1),
   (1..n+1) minus 2, (1..n+1) minus n; 300 s each; 200-minute overall cap.

## Pre-registered checks and predictions

- **S0 (sanity, published data).** Each of the three published n = 5 shift vectors
  covers at R = 1/6 and does not cover at R = 15/94, under both checkers. *If S0 fails,
  grade nothing else until the cause (our checker or a transcription) is found.*
- **S1 (sanity, cannot beat a known optimum).** No certificate for (1..n), n = 5..15, has
  R <= the exact gamma_sh(1..n) of Table 2 of arXiv:2603.24784. *A violation means a bug:
  withdraw every result of the job.*
- **S2.** The two exact checkers agree on every record. *A disagreement means a bug in one
  of them: no certificate counts until it is explained.*
- **V1 (reproduction).** Certificates at e = 1/20 are found for (1..n) for every n in
  8..17 (Prop. 5.14 of arXiv:2603.24784). n = 5, 6, 7 are reported, not predicted
  (their margins are small: gamma_sh(1..5) = 15/94 against 1/6).
- **H1 (main).** A certificate is found for every n in 18..94.
- **H2 (exploratory).** For at least half of n in 18..94, (1..n) gets a certificate with
  e >= 1, i.e. gamma_sh(1..n) < 1/(n+2), extending Poliakova's E_n >= 1 below n = 95.

## What happens next

- H1 holds, S0-S2 clean: publish all certificates; re-check every one with a third,
  separately written standard-library checker in the publishing test (`test_first`);
  search again for prior work; then write it up as "the shifted Lonely Runner Conjecture
  fails for every n >= 5", crediting Blanco-Criado-Santos and Poliakova for every other n,
  and list the authors worth telling for Sheehan (no cold emails).
- H1 fails for some n: report which; run v2 for those n only (longer budgets, a C version,
  or other speed sets). A miss by this heuristic is not evidence that the sLRC holds there.
- Any S-check fails: fix, bump to v2, grade nothing from v1.

## Limits

This is a counterexample search for a variant of the Lonely Runner Conjecture. It says
nothing about the original (unshifted) conjecture, which is still open for 16 or more
runners. The search is heuristic; certificates are exact.
