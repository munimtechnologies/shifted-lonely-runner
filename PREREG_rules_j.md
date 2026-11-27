# Pre-registration: route 15, neighbours of the two known structured covers

Written 2026-11-27 (about 12:10 UTC), before any code of this route had run. MV2, Munim, Inc.
Made with AI agents working in MV2's name; no human expert has checked it. Text CC BY 4.0,
code Apache-2.0.

## Where the problem stands

The shifted Lonely Runner Conjecture fails for 5 <= n <= 57 (Blanco, Criado and Santos;
aadrianvv; tomdif; Callens for 18..38; Lean-checked in 1337isnot1337/solved-conjectures
PR 755), for n = 63 (Xavier Callens, [Zenodo 24051700](https://doi.org/10.5281/zenodo.24051700),
unrefereed) and for n >= 95 (Poliakova, [arXiv:2609.23952](https://arxiv.org/abs/2609.23952)).
**Open: 58..62 and 64..94.** Checked 27 November about 12:00 UTC: the Zenodo API ("shifted
lonely runner": 4 records, newest Bonfioli 13 Nov; "lonely runner" newest first, newest Zhang
26 Nov), the arXiv listing newest first (newest 2610.40694, 28 Oct), solved-conjectures pull
requests (newest: F1Justin's PR 1017, open, 27 Nov: the fixed 57-runner configuration plus any
seven extra runners still leaves an uncovered time at radius 1/59; it states that 58..94 stay
open) and a web search.

## The question

A configuration of k runners whose open arcs of radius 1/(n+1) cover the circle is a
counterexample for every n >= k at that radius. The two structured covers next to the open
range are Callens's 63 runners (radius 1/64, shifts a/520) and Poliakova's 95 runners on
2, 4, ..., 192 (radius 1/96, shifts on 1/1164). PR 850 and PR 1017 study going up from tomdif's
57 by adding runners. Nobody has published the neighbours of these two covers:

- **Down.** Delete d runners. The radius grows to 1/(k-d+1), so every arc gets longer; the
  extra length added over all arcs is about the measure the deleted runners carried. Does some
  deletion, with every remaining shift re-tuned a little, still cover? d = 1 from Callens gives
  n = 62, from Poliakova n = 94; d = 2 gives 61 and 93. All four are open.
- **Up.** Callens's cover plus at most one more runner at radius 1/65 gives n = 64 (open).

Callens's companion search ([Zenodo 24132291](https://doi.org/10.5281/zenodo.24132291)) ran
base-and-move menus at 39..94 and was inconclusive; it did not fix the speeds of a known cover
and re-tune every shift, which is what this route does.

## Method (`descent_j.py`)

Menu of a tier: every source runner is deleted, or kept with its shift moved by j/Dg,
|j| <= J (J/Dg = 1/65 for Callens, 12/1164 = 1/97 for Poliakova); any number of added runners,
speeds {2,3,5}-smooth up to max(v) (up to 2 max(v) in the up tier), not in the source, any shift
on the 1/Dg grid; (added) - (deleted) <= n - k. Point CEGAR with CP-SAT: each time point gives
the clause of every menu option whose open arc contains it (exact integer test, `cover_res`), so
INFEASIBLE proves the finite menu has no cover. Seeds: for down tiers, the exact uncovered
points left by deleting each source runner alone, without re-tuning (the "del1" diagnostic also
reports the smallest uncovered measure and its speed). FOUND = padded to exactly n runners,
distinct speeds, both global exact checkers of `slr.py`.

| tier | source | k | n | radius | role |
|---|---|---|---|---|---|
| sC63 | Callens | 63 | 63 | 1/64 | sanity: must be FOUND (re-checks the certificate as we transcribed it) |
| sP95 | Poliakova | 95 | 95 | 1/96 | sanity: must be FOUND |
| dC62, dC61 | Callens | 63 | 62, 61 | 1/63, 1/62 | down, d >= 1, 2 |
| dP94, dP93 | Poliakova | 95 | 94, 93 | 1/95, 1/94 | down, d >= 1, 2 |
| uC64 | Callens | 63 | 64 | 1/65 | up, at most one more runner |

Tiers take turns of 150 s, 3 processes with 2 CP-SAT workers each; state is cached between gate
probes J1, J2 and J3 (520 s each). Each probe also prints route 14's cached state, so route 14
(PREREG_rules_i.md) is graded from the same reports.

## Sanity rules

- S1: `test_descent_j.py` passes in the gate.
- S2: sC63 and sP95 end FOUND with both exact checkers.
- S3: no tier reports BUG or ERROR.
Otherwise no route-15 result counts.

## Predictions

- **J-R1.** S1-S3 hold and both sanity tiers are FOUND in their first turn. **Yes** (75%).
- **J-R2.** No single deletion covers without re-tuning: the del1 minimum uncovered measure is
  positive in dC62 and in dP94. **Yes** (95%).
- **J-R3.** At least 2 of the 5 target tiers are decided within J1-J3. **Yes** (40%). Decided
  target tiers are INFEASIBLE (90% each).
- **J-R4.** Some target tier yields a certified counterexample for an open n. **No** (3% yes).

## Claims policy

A FOUND configuration for an open n is claimed only after a scoop check on the day of
publishing (Zenodo API, solved-conjectures pull requests, arXiv, GitHub, web) and a re-check by
a fresh third checker in a committed test. A negative covers only the finite menu named. Credit:
the n = 63 cover is Callens's (CC BY 4.0, transcribed from `cert_n063.json` of his AutoevolveAI
repository); the 95-runner cover is Poliakova's; the idea of studying one-step extensions of a
fixed cover is F1Justin's (PR 850, PR 1017).
