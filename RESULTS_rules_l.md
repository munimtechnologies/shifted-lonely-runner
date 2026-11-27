# Route 17, final grading (PREREG_rules_l.md)

Interim written 2026-11-27 (about 18:30 UTC) from gate probes L1 and L2; final written
2026-11-27 (about 20:00 UTC) from the `R17` and `CAL17` lines that route 18's probes N1 and N2
print from route 17's cache (state after L3). MV2, Munim, Inc. Made with AI agents working in
MV2's name; no human expert has checked it.

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

**No speed works, for either source.** The longest gap has length exactly 2R/256 = 1/8320, so
every w >= 256 has an arc no longer than that gap and cannot cover it; every w <= 255 was
decided. The best single speeds reach only a minority of the gaps: 130 reaches 64 of 144, 192
reaches 58, 195 and 65 reach 34-35, 160 reaches 33 (256, not admissible, would reach 82). This is
the same kind of statement as F1Justin's bound on extending tomdif's fixed 57-runner cover
(solved-conjectures PR 850 and PR 1017), applied to Callens's cover: a small, exact negative.

## Parts B/C: exact margins of the near-covers

| tier | n | lambda (final) | critical cycle | speeds sum to |
|---|---|---|---|---|
| kC64 | 64 | 0 | 6, 124 | 130 = 2 x 65 |
| kP94 | 94 | 0 | 6, 184 | 190 = 2 x 95 |
| kC62 | 62 | 0 | 22, 104 | 126 = 2 x 63 |
| kC61 | 61 | 0 | 58, 66 | 124 = 2 x 62 |
| cC63 | 63 | no chain (uncovered 0.018) | - | - |

Every target near-cover touches exactly, and every blocking cycle is a single pair of speeds
summing to 2(n + 1), a rigid pair in the sense of route 18's lemma (README).

Calibration (`CAL17`): our raw transcription of Callens's certificate covers at 1/64
(`raw=True`), its exact margin prints as +3.7e-6 (matching 1/64 - 66/4225 = 1/270400, i.e.
his gamma = 66/4225),
and the polished cover is certified (`cert=True`). The kC64 start (Callens plus speed 256)
has margin exactly 0, blocked by {6, 124}.

## Predictions, final

- **L-R1** (tests pass; no ERROR or BUG; Callens calibration gives lambda > 0 and a cover):
  **held.**
- **L-R2** (A complete, no w works; 256 reaches every gap in floats but fails exactly): **main
  claim held; the detail was wrong** (256 reaches at most 82 of the 144 gaps even in floats).
- **L-R3** (lambda of the kC64 start <= 0): **held** (exactly 0).
- **L-R4** (cC63 re-finds a certified cover at 1/64 within L1-L3): **failed** (no chain).
- **L-R5** (a new open n): **no.**

Route 17 is closed.
