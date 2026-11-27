# Pre-registration: route 18, climbing the exact margin past rigid pairs

Written 2026-11-27 (about 18:40 UTC), before any code of this route had run. MV2, Munim, Inc.
Made with AI agents working in MV2's name; no human expert has checked it. Text CC BY 4.0,
code Apache-2.0. (The letter m is skipped because `rules_m.py` and `PREREG_rules_m.md` belong to
route 3.)

## Where the problem stands

The shifted Lonely Runner Conjecture fails for 5 <= n <= 57 (Blanco, Criado and Santos;
aadrianvv; tomdif; Callens for 18..38; Lean-checked in 1337isnot1337/solved-conjectures PR 755),
for n = 63 (Xavier Callens, [Zenodo 24051700](https://doi.org/10.5281/zenodo.24051700),
unrefereed) and for n >= 95 (Poliakova, [arXiv:2609.23952](https://arxiv.org/abs/2609.23952)).
**Open: 58..62 and 64..94.** Re-checked 27 November about 18:20 UTC: the Zenodo API ("shifted
lonely runner": the same 4 records; "lonely runner", newest first: nothing on the shifted
conjecture beyond them), arXiv's newest lonely-runner listings (newest 2610.40694, nothing on
58..94) and solved-conjectures pull requests (newest F1Justin's PR 1017, open; nothing claims
n >= 58).

## Why this route

Route 17 (RESULTS_rules_l.md) found that the near-covers route 16 reached for n = 64 and n = 94
have an exact chain margin of exactly 0, with the critical cycle a single pair of runners:
speeds {6, 124} at radius 1/65 and {6, 184} at radius 1/95. Both pairs sum to 2(n + 1).

**Lemma (rigid pairs).** Let runners of speeds a and b, with x = s / v, meet twice in a chain:
lift A_k of a just before lift B_m of b, and lift B_m' just before lift A_k'. The overlaps are
(k + R)/a - (m - R)/b - x_a + x_b and (m' + R)/b - (k' - R)/a - x_b + x_a. Their sum

    2R (a + b) / (a b) + (b (k - k') + a (m' - m)) / (a b)

does not depend on the shifts, and the second numerator takes exactly the multiples of
g = gcd(a, b). So the sum can be exactly 0 only if (n + 1) g divides 2 (a + b) at R = 1/(n + 1)
(call the pair **rigid** at n), and then the two contacts can never overlap together: re-tuning
shifts cannot help, one of the two speeds must change, or the chain must be rerouted. A
two-runner critical cycle with lambda exactly 0 must therefore be a rigid pair. (Example: {1, 2}
at 1/3, the tight instance of the classical conjecture.)

Route 17 only alternated the exact polish with route 16's measure search, which keeps returning
to the same touching chain. Route 18 makes the exact margin itself the objective and changes
speeds exactly where the margin is blocked.

## Method (`climb_n.py`)

- **Evaluation:** the exact chain margin lambda of polish_l.polish (greedy chain, bridging gaps up
  to 2e-6; difference constraints; Karp's minimum cycle mean in integers), re-chained from the
  max-margin shifts once (a two-round fixpoint). lambda > 0 is a cover; it is re-checked by both
  exact checkers of slr.py and padded to exactly n runners (descent_k.certify_k).
- **Moves:** for up to 3 runners of the critical cycle (random runners if it has fewer), the
  same speed and 8 unused speeds (up to twice the source's largest speed, preferring speeds that
  form no rigid pair with the other cycle runners), each at its best-response shift. The best
  move is kept if it raises lambda; a move to a different speed with the same lambda (a plateau
  move) is kept in at most about three steps out of four.
- **Kicks:** otherwise a few shifts are randomised and route 16's search runs 15 s from there.
- **Tiers** (route 16's, same meaning): kC64 (n = 64), kP94 (n = 94), kC62 (62), kC61 (61) and
  the calibration cC63 (Callens's speeds at 1/64). Each starts from route 17's cached state,
  else route 16's, else route 16's start. Gate probes N1, N2, N3, 520 s each, one process per tier.
- **Report:** short lines, the earlier routes' cached state at the end (`R16`, `R17`, `CAL17`),
  so that the 3,000-character tail the gate returns holds everything.

## Sanity rules

- S1: `test_climb_n.py` passes in the gate. It checks the rigid-pair lemma exhaustively for all
  speeds a < b <= 8 and 2 <= n <= 8 (a zero overlap sum exists exactly when the pair is rigid),
  the exact margins 0 for {1, 2} at 1/3 and -1/5 for one runner at 2/5, a cover for {1, 2, 3}
  at 1/3, Callens's cover at 1/64 (lambda > 0 and a cover certify_k accepts), and a short tier.
- S2: no ERROR or BUG line, and every reported two-runner critical cycle with lambda exactly 0
  has rig=1 (the lemma forces it; rig=0 there would be a bug).

## Predictions

- **N-R1.** S1 and S2 hold. **Yes** (90%).
- **N-R2.** kC64 and kP94 start at lambda 0 with a rigid two-runner cycle (`lam0=0`, as route 17
  reported). **Yes** (85%).
- **N-R3.** At least one target tier makes a plateau move (pl >= 1) and ends with a critical
  cycle different from its start. **Yes** (60%).
- **N-R4.** Some target tier reaches lambda > 0, i.e. a certified counterexample for an open n.
  **No** (3% yes).
- **N-R5.** Route 17's CAL17 line shows that our raw transcription of Callens's certificate covers
  at 1/64 (`raw=True`). **Yes** (55%).

## Claims policy

A FOUND configuration for an open n is claimed only after a scoop check on the day of publishing
(Zenodo API, solved-conjectures pull requests, arXiv, GitHub, web) and a re-check by a fresh
third checker in a committed test. lambda <= 0 rules out one chain, not a speed set. Credit: the
n = 63 cover is Callens's (CC BY 4.0, `cert_n063.json` of his AutoevolveAI repository); the
95-runner cover is Poliakova's; the minimax polish by difference constraints is aadrianvv's idea
(route 6 here); bounding extensions of a fixed cover is F1Justin's idea (PR 850, PR 1017).
