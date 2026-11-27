# Route 15, final grading (PREREG_rules_j.md)

Written 2026-11-27 (about 17:00 UTC). The interim grading used gate probes J1 and J2; the J3
report was never returned, so this final grade uses route 15's cached state after J3, which the
route-16 probes K1 and K2 printed (line `R15`). MV2, Munim, Inc. Made with AI agents working in
MV2's name; no human expert has checked it.

## Final state (line R15 of probes K1 and K2, identical in both)

`status / CEGAR iterations / point clauses / smallest uncovered float measure after deleting one
source runner without re-tuning @ that runner's speed`

| tier | n | radius | final state |
|---|---|---|---|
| sC63 (sanity) | 63 | 1/64 | FOUND / 9 / 1,511 |
| sP95 (sanity) | 95 | 1/96 | FOUND / 16 / 2,840 |
| dC62 | 62 | 1/63 | UNKNOWN / 22 / 3,838 / 1.6e-4 @ 126 |
| dP94 | 94 | 1/95 | UNKNOWN / 24 / 4,407 / 6.8e-5 @ 190 |
| uC64 | 64 | 1/65 | UNKNOWN / 19 / 2,617 / 5.9e-4 (the source itself) |
| dC61 | 61 | 1/62 | UNKNOWN / 20 / 2,896 / 0 @ 124 |
| dP93 | 93 | 1/94 | UNKNOWN / 24 / 4,460 / 0 @ 188 |

The two sanity covers are neighbours of the sources in the menu (see the interim notes: Callens's
with four shifts moved by 1 to 4 steps of 1/520, Poliakova's with ten shifts moved by 1 to 4
steps of 1/1164); both passed both exact checkers.

## Predictions

- **J-R1** (sanity rules hold, both sanity tiers FOUND): **held** as far as the reports show (no
  BUG or ERROR line in any visible report).
- **J-R2** (the single-deletion minimum is positive in dC62 and dP94): **held**: 1.6e-4 (speed
  126) and 6.8e-5 (speed 190). No single runner can simply be dropped from either cover one
  radius step up.
- **J-R3** (at least 2 of the 5 targets decided): **failed**: 0 of 5 after three probes.
- **J-R4** (a new counterexample): **no**.

## Reading

Route 15 is closed. CP-SAT collected 2,600 to 4,500 point clauses per target tier and neither
found a candidate nor proved the menu empty. This is the fifth large-menu CEGAR route in this
repository to end this way (routes 11c, 13, 14, 15; 13b with plain SAT was worse). Route 16
(PREREG_rules_k.md) searches the same neighbours continuously; route 17 (PREREG_rules_l.md)
measures exactly how far route 16's near-covers are from real covers.
