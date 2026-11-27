# Route 16, final grading (PREREG_rules_k.md)

Interim written 2026-11-27 (about 17:00 UTC) from gate probes K1 and K2; final written
2026-11-27 (about 20:00 UTC) from the `R16` line that route 18's probes N1 and N2 print from
route 16's cache (it holds the state after K3). MV2, Munim, Inc. Made with AI agents working in
MV2's name; no human expert has checked it.

## What the reports show

`best` is the smallest float uncovered measure reached at the shrunk search radius
R (1 - 10^-7); `m0` is the measure of the start at the true radius R = 1/(n+1).

| tier | n | start | m0 | best after K1 | best after K2 | best after K3 (R16) |
|---|---|---|---|---|---|---|
| cC63 (calibration) | 63 | Callens's speeds, random shifts | - | not visible | not visible | 0.0191 (start 0.142) |
| kC62 | 62 | Callens minus 126 | 1.55e-4 | 1.4e-9 | 1.4e-9 | 1.41e-9 |
| kC61 | 61 | Callens minus 124 and 126 | 2.65e-5 | 1.99e-9 | 1.87e-9 | 1.87e-9 |
| kC64 | 64 | Callens plus 256 at its best shift | 1.21e-15 | 3.08e-9 | 3.08e-9 | 3.08e-9 |
| kP94 | 94 | Poliakova minus 190 | 6.78e-5 | 4.42e-9 | 4.42e-9 | 4.42e-9 |

All five tiers ended UNKNOWN after three turns (`R16 ... =UNK/.../tu3`). No cover.

## Predictions, final

- **K-R1** (tests pass, no ERROR or BUG): **held as far as visible.**
- **K-R2** (cC63 re-finds a cover at 1/64 within K1-K3): **failed.** From random shifts on
  Callens's speeds the search stopped at an uncovered measure of 0.0191, far from a cover. The
  calibration shows that this search cannot rediscover Callens's cover, so its silence on the
  target tiers says little.
- **K-R3** (kC62 best at most a tenth of its start): **held** (1.4e-9 against 1.55e-4).
- **K-R4** (a new counterexample): **no.**

## What the plateau meant

Route 17 (RESULTS_rules_l.md) checked the end points exactly: the kC64 and kP94 end points
touch with chain margin exactly 0, so the 1e-9 floor is what shrinking the radius produces at
touching arcs. Route 16 is closed.
