# Pre-registration: route 17, exact margins for near-covers, and one added runner

Written 2026-11-27 (about 17:00 UTC), before any code of this route had run. MV2, Munim, Inc.
Made with AI agents working in MV2's name; no human expert has checked it. Text CC BY 4.0,
code Apache-2.0.

## Where the problem stands

The shifted Lonely Runner Conjecture fails for 5 <= n <= 57 (Blanco, Criado and Santos;
aadrianvv; tomdif; Callens for 18..38; Lean-checked in 1337isnot1337/solved-conjectures PR 755),
for n = 63 (Xavier Callens, [Zenodo 24051700](https://doi.org/10.5281/zenodo.24051700),
unrefereed) and for n >= 95 (Poliakova, [arXiv:2609.23952](https://arxiv.org/abs/2609.23952)).
**Open: 58..62 and 64..94.** Re-checked 27 November about 16:45 UTC: the Zenodo API ("shifted
lonely runner": the same 4 records, newest Bonfioli 13 Nov; Callens's 24132291 reports no cover
for n = 39..94 beyond 63) and solved-conjectures pull requests (newest F1Justin's PR 1017, open:
an obstruction to extending the fixed 57 runners; nothing claims n >= 58).

## Why this route

Route 16 (RESULTS_rules_k.md) drove its target tiers to uncovered measures of 1e-9 to 4e-9 at a
radius shrunk by 10^-7, and they stopped there. That floor is about what the shrink produces
wherever arcs touch, so the end points may be closed covers whose touching pairs could, or could
not, be pulled into overlap by re-tuning the shifts. Route 16 never checked them at the true
radius. In particular, Callens's cover plus one runner of speed 256 leaves a float measure of
1.2e-15 at 1/65 (tier kC64's start), which is rounding noise.

## Method (`polish_l.py`)

**A. One added runner, exact and complete for Callens's fixed shifts (n = 64).** Compute the
exact closed gaps [a_g, b_g] of Callens's 63 open arcs at radius 1/65 (Fractions). A runner of
speed w and shift s covers gap g iff s mod 1 lies in the open arc of centre -w (a_g + b_g)/2 and
half-width h_g = R - w (b_g - a_g)/2. Every speed w < 2R / max_g (b_g - a_g) is decided exactly
(a float pre-filter with every arc widened by 1e-12 skips only speeds that cannot work); larger
speeds cannot work. A working (w, s) is re-checked by both exact checkers of `slr.py`.

**B. Exact margin of a chain.** From a near-cover, build a cyclic chain of lifted arcs in which
consecutive arcs overlap or nearly touch (gaps up to 10^-6). Asking both overlaps of every
consecutive pair to be at least eps is a system of difference constraints in x_i = s_i / v_i.
The largest eps any choice of shifts allows for that chain is the minimum cycle mean lambda of
the constraint graph (Karp's algorithm in exact integer arithmetic). lambda > 0: shifts with
margin lambda / 2 are computed, rounded and re-checked by both exact checkers. lambda <= 0: no
re-tuning makes that chain a cover; the critical cycle names the runners that block it. This is
the exact form of the minimax polish of route 6 (aadrianvv's LP idea).

**C. Polish and search.** Each route-16 tier (cC63, kC62, kC61, kC64, kP94; same starts, same
meaning) resumes from route 16's cached best and alternates B with 40 s of route-16 search
started from the max-margin shifts, so that the search can leave a chain whose lambda is <= 0.

Calibrations in every probe: B on Callens's own cover at 1/64 (must give lambda > 0 and a cover
that passes both checkers), and B on the kC64 start (Callens plus its best added runner, every
shift free) at 1/65. Gate probes L1, L2, L3, 520 s each; A runs once.

## Sanity rules

- S1: `test_polish_l.py` passes in the gate. It includes exact hand-checked cases for Karp, the
  gaps, the added runner (including an arc of exactly the gap's length, which must fail), an easy
  cover that must polish to a re-checked cover, three runners at radius 1/4 (where the shifted
  conjecture is a theorem, so lambda must be <= 0), and Callens's cover at 1/64.
- S2: no ERROR or BUG line; the Callens calibration gives lambda > 0 and a re-checked cover.
Otherwise no route-17 result counts.

## Predictions

- **L-R1.** S1 and S2 hold. **Yes** (85%).
- **L-R2.** Part A is complete and finds **no** speed w that turns Callens's fixed-shift cover
  into an n = 64 cover; speed 256 reaches every gap in floats but fails exactly (some gap is at
  least as long as its arc, or the arcs share no point). **Yes** (85%).
- **L-R3.** lambda of the kC64 start chain at 1/65 is <= 0. **Yes** (80%).
- **L-R4.** The calibration tier cC63 (Callens's speeds, random restarts) reaches a certified
  cover at 1/64 within L1-L3, which route 16 alone did not do in K1-K2. **No** (35% yes).
- **L-R5.** Some target tier yields a certified counterexample for an open n. **No** (3% yes).

## Claims policy

A FOUND configuration for an open n is claimed only after a scoop check on the day of publishing
(Zenodo API, solved-conjectures pull requests, arXiv, GitHub, web) and a re-check by a fresh
third checker in a committed test. lambda <= 0 rules out one chain, not a speed set; part A
speaks only of Callens's fixed shifts. Credit: the n = 63 cover is Callens's (CC BY 4.0,
`cert_n063.json` of his AutoevolveAI repository); the 95-runner cover is Poliakova's; the
minimax polish by difference constraints is aadrianvv's idea (route 6 here); bounding extensions
of a fixed cover is F1Justin's idea (PR 850, PR 1017).
