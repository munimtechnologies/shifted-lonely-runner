# Route 16, interim grading (PREREG_rules_k.md)

Written 2026-11-27 (about 17:00 UTC) from gate probes K1 and K2 (about 460 s of search per tier
each). The K3 report was not returned; route 17's probes print route 16's cached state (line
`R16`), and the final grade will use it. MV2, Munim, Inc. Made with AI agents working in MV2's
name; no human expert has checked it.

## What the reports show

The gate keeps only the last 3,000 characters of a report, so the line of the calibration tier
cC63 was cut off both times; its status (UNKNOWN) is in the STATUS lines. `best` is the smallest
float uncovered measure reached at the shrunk search radius R (1 - 10^-7); `m0` is the measure of
the start at the true radius R = 1/(n+1).

| tier | n | start | m0 | best after K1 | best after K2 | gaps | sweeps after K2 |
|---|---|---|---|---|---|---|---|
| cC63 (calibration) | 63 | Callens's speeds, random shifts | - | not visible | not visible | - | - |
| kC62 | 62 | Callens minus 126 | 1.55e-4 | 1.4e-9 | 1.4e-9 | - | - |
| kC61 | 61 | Callens minus 124 and 126 | 2.65e-5 | 1.99e-9 | 1.87e-9 | 10 | 2,897 |
| kC64 | 64 | Callens plus 256 at its best shift | 1.21e-15 | 3.08e-9 | 3.08e-9 | 17 | 2,549 |
| kP94 | 94 | Poliakova minus 190 | 6.78e-5 | 4.42e-9 | 4.42e-9 | 51 | 751 |

No tier found a cover. Every target tier fell five or more orders of magnitude in K1 and then
stopped moving: K2 improved only kC61, and only by 6%.

## Predictions so far

- **K-R1** (tests pass, no ERROR or BUG): the code commit passed its tests; no ERROR or BUG line is
  visible (the start of each report, where such lines would be, was cut off). **Holds as far as
  visible.**
- **K-R2** (cC63 re-finds a cover at 1/64 within K1-K3): **not met after K2.**
- **K-R3** (kC62 best at most a tenth of its start): **held**: 1.4e-9 against 1.55e-4.
- **K-R4** (a new counterexample): **no.**

## What the plateau means, and a gap in route 16's design

The floor near 1e-9 is about what the shrink alone produces. Shrinking every radius by
R x 10^-7 opens a gap of about 10^-7 R (1/v_a + 1/v_b) in time wherever two arcs of speeds v_a
and v_b meet exactly. With R = 1/63 that is about 3e-10 for speeds near 10, and 10 to 50 such
meetings give 1e-9 to 5e-9. So route 16's end points are probably configurations whose arcs
**touch** at a few dozen points: covers in the closed sense, but not in the open sense the
conjecture needs, unless the shifts can be re-tuned so that every touching pair overlaps.

Route 16 cannot tell these cases apart. It checks a configuration exactly only when its
shrunk-radius measure drops below 10^-13, so its end points were never checked at the true
radius. The clearest case is kC64: Callens's cover plus one runner of speed 256 at its
best-response shift leaves a float measure of only 1.2e-15 at the true radius 1/65, which is
rounding noise. Route 17 (PREREG_rules_l.md) settles both questions exactly: whether an added
runner can turn Callens's fixed shifts into an n = 64 cover, and the largest overlap margin any
re-tuning of the shifts can give each near-cover.
