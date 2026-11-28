# Pre-registration: route 19d, menu q with 5-smooth speeds

Written 2026-11-28 (about 00:45 UTC), before any code of this route had run. MV2, Munim, Inc.
Made with AI agents working in MV2's name; no human expert has checked it. Text CC BY 4.0, code
Apache-2.0.

## Where the problem stands

The shifted Lonely Runner Conjecture is known to fail for 5 <= n <= 57 (Blanco, Criado and
Santos; aadrianvv; tomdif; Callens; Lean-checked in 1337isnot1337/solved-conjectures PR 755),
for n = 63 (Xavier Callens, [Zenodo 24051700](https://doi.org/10.5281/zenodo.24051700),
unrefereed) and for n >= 95 (Poliakova, [arXiv:2609.23952](https://arxiv.org/abs/2609.23952)).
**Open: 58..62 and 64..94.** Re-checked 2026-11-28 about 00:30 UTC: the Zenodo API ("shifted
lonely runner": the same four records; "lonely runner": 73 records, newest Zhang 24573706 on
26 November), arXiv's newest lonely-runner listings (newest 2610.40694), the solved-conjectures
pull requests (newest F1Justin's PR 1017, open) and F1Justin's MathLab repository, which reports
E_n >= floor(n/125) and fixed-seed and phase-menu negatives at 58 and 91..95 runners but no
case in 58..94.

## What route 19c showed (RESULTS_rules_q.md)

In menu q (s0 in quarters, beta in halves of delta on [-2, 2], 3-smooth speeds) the exact CEGAR
decided 38 of its 40 targets, all INFEASIBLE: no gain-1 rule at any N in 59..95 except 64, and no
gain-2 rule at N = 64 or 96. Both sanity tiers re-found certified covers. The two undecided
tiers were gain 2 with 5-smooth speeds (about 22 s per solver call).

## Method (`top_r.py`)

- Menu q as in route 19c, with P = (2, 3, 5). Touchable speeds are the 5-smooth multiples of 4
  up to 2N and 2N itself if 5-smooth. That adds 20, 40, 60, 80, 100, 120, 160, 180 and the top
  speed at N = 60, 75, 80, 90. Added speeds are the odd 5-smooth speeds up to 2N + 1 (adds 5,
  15, 25, 45, 75, 125, 135).
- Search: `top_p.cegar_p` unchanged. Tiers are seeded with the classes route 19c collected for
  the same N and g (cache %TEMP%/mv2-slr-q1). A class id is valid in any menu, and its clauses
  are rebuilt from menu q with P5.
- Tiers: sanity r64 (N = 64, gain 1, from scratch; menu q with P5 contains SIMPLE_63, so it must
  not be INFEASIBLE). Targets: r64g2 and r96g2 (gain 2 at N = 64 and 96, n = 62 and 94, resumed
  from route 19c's q64g2p5 / q96g2p5 classes), then gain 1 at N = 60, 75, 80, 90, 72, 81 (2N
  5-smooth), then gain 1 at every other N in 59..95 except 64. 38 targets. Caps: 150 s per
  turn for the gain-2 tiers, 120 s for r64, 60 s for the others. Fewest turns first. State in
  %TEMP%/mv2-slr-r1. Gate probes R1, R2, R3 of 520 s each; later runs add probes until every
  tier is decided.
- Every FOUND rule is re-checked by three global exact checkers at R = 1/(n + 1)
  (`top_q.full_cert`). A failure there is a BUG, never a result.
- **Clause-soundness check** (new, in `test_top_r.py`, run before the route is committed).
  `violations(rule, N, g, P)` rebuilds every clause of every class of every speed a rule touches
  and lists those it falsifies. Five certified cases must falsify none: SIMPLE_63 at N = 64 (P3
  and P5), route 19c's two sanity rules RULE_Q64 and RULE_Q96, and Poliakova's 9 -> 8 rule at
  N = 96. Two failing rules must falsify some clause, and only in classes where `fixed_check`
  also fails. Route 19c's negatives count only if this test passes.
- Report: `QSTATE` (route 19c's final counts and solver seconds per iteration), `QTOK` (route
  19c's sanity, first and 5-smooth tokens, including those cut off in Q1 and Q2), `QBUG`, then
  one token per route-19d tier, `RIT`, BUG, SANE, RULE, CERT, and STATUS last.

## Sanity rules

- S1: `test_top_r.py` passes in the gate.
- S2: r64 is FOUND within the probes that decide its turn, and no tier is BUG. If S2 fails, no
  INFEASIBLE of this route counts.
- S3 (for route 19c): `QBUG none` and `QTOK` shows q64g2, q96g2, q72, q81, q95 and q63 as I. If
  S3 fails, RESULTS_rules_q.md is corrected before anything is published.

## Predictions

- **R-R1.** S1, S2 and S3 hold. **Yes** (75%).
- **R-R2.** r64 is FOUND within its first two turns. **Yes** (70%).
- **R-R3.** At least 20 of the 38 targets are decided within R1-R6 (two runs of probes).
  **Yes** (45%).
- **R-R4.** Every decided target is INFEASIBLE: 5 does not add a gain-1 rule anywhere in
  59..95. **Yes** (85%).
- **R-R5.** Some target is FOUND and certified by all three checkers, i.e. a counterexample for
  an open n. **No** (5% yes).

## Claims policy

A FOUND target is claimed only after a scoop check on the day of publishing and a commit of its
certificate with a re-check by a fresh checker in a test. INFEASIBLE is reported as "no rule in
menu q with 5-smooth speeds at this N and gain", never as "no counterexample for n". Credit: the
n = 63 case and its first certificate are Callens's (CC BY 4.0); local rules, their locality
proof, the 9 -> 8 rule and E_n are Poliakova's; the CEGAR encoding is route 11's.
