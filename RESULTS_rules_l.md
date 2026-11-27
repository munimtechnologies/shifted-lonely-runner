# Route 17, interim grading (PREREG_rules_l.md)

Written 2026-11-27 (about 18:30 UTC) from gate probes L1 and L2 (about 470 s each). The L3
report was not returned. The gate keeps only the last 3,000 characters of a report, so the
calibration line (`CAL`), the route-16 line (`R16`) and the lines of tiers cC63, kC62 and kC61
were cut off both times. Route 18's probes print route 17's cached state at the end of their
reports (`R17`, `CAL17`), and the final grade will use those lines. MV2, Munim, Inc. Made with AI
agents working in MV2's name; no human expert has checked it.

## Part A: one added runner on Callens's fixed shifts (n = 64): an exact negative

Part A decided, for every speed w that could possibly work, whether one runner of speed w added
to Xavier Callens's n = 63 cover ([Zenodo 24051700](https://doi.org/10.5281/zenodo.24051700)),
with his shifts kept fixed, gives an n = 64 cover at radius 1/65. It ran on two versions of his
shifts: C64, the neighbour certified by both our exact checkers at 1/64 (route 15), and R64, our
raw transcription of his certificate.

| source | gaps at 1/65 | of which single points | uncovered measure | longest gap | speeds decided | complete | speeds that work |
|---|---|---|---|---|---|---|---|
| C64 | 144 | 90 | 5.93e-4 | 1.2e-4 | 1..255 | yes | none |
| R64 | 144 | 90 | 5.86e-4 | 1.2e-4 | 1..255 | yes | none |

**No speed works, for either source.** The longest gap has length exactly 2R/256 = 1/8320 (the
reported half-width for w = 256 is exactly 0), so every w >= 256 has an arc no longer than that
gap and cannot cover it; every w <= 255 was decided, and none can even reach all 144 gaps (the
float pre-filter, which widens every arc by 1e-12 and so never under-counts, found no such w).
The best single speeds reach only a minority of the gaps:

| speed w | most gaps one shift of w reaches (C64) | (R64) |
|---|---|---|
| 130 | 64 of 144 | 64 |
| 192 | 58 | 58 |
| 195 | 34 | 35 |
| 65 | 34 | 35 |
| 160 | 33 | 33 |
| 256 (not admissible) | 82 | 82 |

The best speeds 65, 130 and 195 are the multiples of n + 1 = 65. So Callens's cover, with its
shifts as published, is far from extending by one runner: the extension needs re-tuned shifts,
which tiers kC64 (route 16) and route 18 search. This is the same kind of statement as
F1Justin's bound on extending tomdif's fixed 57-runner cover (solved-conjectures PR 850 and PR
1017), applied to Callens's n = 63 cover. It is a small, exact negative, not a result about the
conjecture.

## Part B/C: exact margins of the route-16 end points

| tier | n | chain arcs | lambda at the start | lambda after L2 | critical cycle |
|---|---|---|---|---|---|
| kC64 | 64 | 2,140 | 0 | 0 (24 polishes) | speeds 6 and 124 |
| kP94 | 94 | 4,952 | 0 | 0 (24 polishes) | speeds 6 and 184 |

Both near-covers are **exactly touching**: the best margin any re-tuning of the shifts gives
their chains is exactly 0, and alternating 40 s searches did not leave that chain. In both, the
critical cycle is a single pair of runners whose speeds sum to 2(n + 1): 6 + 124 = 130 at
n = 64 and 6 + 184 = 190 at n = 94. Route 18 explains why (PREREG_rules_n.md): for two contacts
between runners of speeds a and b, the sum of the two overlaps does not depend on the shifts and
can be exactly 0 only when (n + 1) gcd(a, b) divides 2(a + b). Both pairs satisfy this (gcd 2).

## Predictions so far

- **L-R1** (tests pass; no ERROR or BUG; Callens calibration gives lambda > 0 and a cover):
  `test_polish_l.py` passed in the gate, including the test that polishes Callens's cover at 1/64
  to lambda > 0 and a cover that `certify_k` accepts. No ERROR or BUG line is visible (the front
  of each report, where they would be, was cut). **Holds as far as visible.**
- **L-R2** (A complete, no w works; 256 reaches every gap in floats but fails exactly): **the
  main claim held** (complete, no w works). **The detail was wrong**: speed 256 reaches at most 82
  of the 144 gaps even in floats; it is excluded because its arc is exactly as long as the
  longest gap.
- **L-R3** (lambda of the kC64 start <= 0): the CAL line was cut; **pending**. The kC64 tier's
  route-16 end point has lambda exactly 0.
- **L-R4** (cC63 re-finds a certified cover at 1/64 within L1-L3): STATUS cC63=UNKNOWN after L2;
  **pending** (L3 unseen).
- **L-R5** (a new open n): **no** after L1-L2.
