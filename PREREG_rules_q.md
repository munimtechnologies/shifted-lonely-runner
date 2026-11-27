# Pre-registration: route 19c, the exact fixed-N search in a small menu

Written 2026-11-27 (about 23:00 UTC), before any code of this route had run. MV2, Munim, Inc.
Made with AI agents working in MV2's name; no human expert has checked it. Text CC BY 4.0, code
Apache-2.0.

## Where the problem stands

The shifted Lonely Runner Conjecture is known to fail for 5 <= n <= 57 (Blanco, Criado and
Santos; aadrianvv; tomdif; Callens; Lean-checked in 1337isnot1337/solved-conjectures PR 755),
for n = 63 (Xavier Callens, [Zenodo 24051700](https://doi.org/10.5281/zenodo.24051700),
unrefereed) and for n >= 95 (Poliakova, [arXiv:2609.23952](https://arxiv.org/abs/2609.23952)).
**Open: 58..62 and 64..94.** Re-checked 27 November about 22:45 UTC: the Zenodo API ("shifted
lonely runner": the same four records, Bonfioli 24189338 and Callens 24132291, 24051700,
23842167; "lonely runner": 73 records, newest Zhang 24573706 on 26 November), arXiv's newest
lonely-runner listings (newest 2610.40694, 28 October), the solved-conjectures pull requests
(newest F1Justin's PR 1017, open, on extending the fixed 57-runner configuration; nothing claims
n >= 58).

## What route 19b showed (RESULTS_rules_p.md, interim)

Its sanity tiers re-found two n = 63 covers at N = 64 from scratch. One of them (tier ph64,
4 iterations, 8 s) is much smaller than Callens's certificate (11 touched speeds against 18):

- base 2, 4, ..., 128 at shift 0 (delta = 1/65); remove 8, 32, 96; rephase 12, 24, 48 to
  1/2 + delta/2, 16 to -3 delta/2, 64 to -delta and 128 to +delta; add 3 and 9 at 3/4.

It is Poliakova's 9 -> 8 local rule cut off at 2N = 128 by the top trick (`top_q.py`
docstring), and it is committed with four exact re-checks as `cover_n063_simple.json`. Both
known gain-1 rules (this one at N = 64, Poliakova's at N = 96) use shifts s0 in quarters and
beta in halves of delta only. Route 19b's 37 targets used the much larger menu x (s0 also in
thirds and sixths, beta also in eighths: about 4.7 times as many options per speed) and got
one to three iterations each. Almost every solver call ran out of its time (about 20 s per
iteration on average). None was decided.

## Method (`top_q.py`)

- Menu q: s0 in {0, 1/4, 1/2, 3/4}, beta in halves on [-2, 2]; touchable speeds are the
  P-smooth multiples of 4 up to 2N (and 2N itself if P-smooth); added speeds the odd P-smooth
  speeds up to 2N + 1 (`top_o.pools_o`). Menu q is a subset of route 19's menu x, so
  "INFEASIBLE in menu q" is weaker than in menu x, and FOUND in q is FOUND in x.
- Search: `top_p.cegar_p` unchanged (exact criterion `top_o.fixed_check` at the slack radius
  r = 128/(128(n + 1) + 1), clauses `top_o.class_clauses_o`, feasibility-only CP-SAT).
  Targets are seeded with up to 8 class ids per speed collected by route 19b (or route 19)
  for the same N and g. A class id is valid in any menu; its clauses are rebuilt.
- Tiers: sanity q64 (N = 64, g = 1) and q96 (N = 96, g = 1), both from scratch; targets
  q64g2 (n = 62), q96g2 (n = 94), q72, q81, q95, q63, q65, then qN (g = 1, n = N - 1) for
  every other N in 59..95 except 64, then q64g2p5 and q96g2p5 (gain 2 with 5-smooth speeds,
  no seeds). 40 targets; 40 s per turn (sanity 60 s); fewest turns first; 8 workers;
  state in %TEMP%/mv2-slr-q1. Gate probes Q1, Q2, Q3 of 520 s each.
- Every FOUND rule is re-checked by three global exact checkers at R = 1/(n + 1): both of
  slr.py (`top_o.certify`) and `top_q.indep_cover` (an integer endpoint test written for this
  route). A failure there is a BUG, never a result.
- Report: route 19b's final cache state (`P1STATE`, and `P1RULE` in full for any target
  route 19b decided FOUND, since probe P3's report was not seen), one token per tier
  (`tag:<F|I|U|B><iterations>/<seconds>`), `QIT` (mean solver seconds per iteration), then
  BUG, SANE, RULE, CERT, STATUS last.

## Sanity rules

- S1: `test_top_q.py` and `test_cover_n063_simple.py` pass in the gate.
- S2: q64 and q96 are FOUND within Q1-Q3 and no tier is BUG. If S2 fails, no INFEASIBLE of
  this route counts.

## Predictions

- **Q-R1.** S1 and S2 hold. **Yes** (75%).
- **Q-R2.** QIT (mean solver seconds per iteration) is below 10 s after Q3. **Yes** (50%).
- **Q-R3.** At least 10 of the 40 targets are decided (INFEASIBLE or FOUND) within Q1-Q3.
  **Yes** (40%).
- **Q-R4.** q64g2 (n = 62 at N = 64) is decided within Q1-Q3, and the decision is INFEASIBLE.
  **Yes** (35%).
- **Q-R5.** Some target is FOUND and certified by all three checkers, i.e. a counterexample for
  an open n. **No** (3% yes).

## Claims policy

A FOUND target is claimed only after a scoop check on the day of publishing and a commit of its
certificate with a re-check by a fresh checker in a test. INFEASIBLE is reported as "no rule in
menu q at this N and gain", never as "no counterexample for n". Credit: the n = 63 case and its
first certificate are Callens's (CC BY 4.0); local rules, their locality proof, the 9 -> 8 rule
and E_n are Poliakova's; the CEGAR encoding is route 11's; the menu restriction is suggested by
the two known gain-1 rules.
