# Results: route 6 (minimax polish), graded against PREREG_lp.md

Graded 2026-11-25 (~11:30 UTC) by AI agents working in MV2's name. Code Apache-2.0, text CC BY 4.0.
No human expert has checked this yet.

## Headline

**n = 55 is certified: the shifted Lonely Runner Conjecture fails for 55 runners.** The
smallest case left open after the published counterexamples for 18..54 now has an exact
certificate, `certs_lp.json`:

- speeds: the 54 speeds of the published n = 54 counterexample (aadrianvv,
  [1337isnot1337/solved-conjectures](https://github.com/1337isnot1337/solved-conjectures/tree/main/results/shifted-lonely-runner-counterexamples))
  plus one new runner of speed **195**;
- shifts: all 55 starting positions moved together by route 6's polish, rounded to
  multiples of 10^-6 (`shift_num / 10^6`).

With these, the open arcs {t : ||v_i t + s_i|| < 10/561} cover the circle, so the loneliness
is below 10/561 = 1/56.1 < 1/56. The probe's float value is 1/gamma = 56.116, i.e.
E = 1/gamma - 56 = **+0.116** (a counterexample needs E > 0). Before route 6 the best
reported value at n = 55 was E = -0.012 (aadrianvv, issue #110 of that repository) and
ours was -0.257 (route 5).

## How it is checked

`test_certs_lp.py` (standard library) checks the certificate with four exact checkers, none
of which uses floating point:

| checker | where | radius | result |
|---|---|---|---|
| `covers_int`: integer sweep, time scaled by 10^6 * 56 * lcm(v) | `test_certs_lp.py` (new) | open, 1/56 and 10/561 | covers |
| `covers_sweep`: Fraction sweep | `slr.py` | open, 1/56 and 10/561 | covers |
| `covers_endpoints`: every arc endpoint strictly inside another arc | `slr.py` | open, 1/56 | covers |
| `exact_cover`: closed arcs, Fractions | `slr_br.py` | closed, 1/56 - 10^-11 | covers |

As a control, the same certificate does **not** cover at radius 1/57 (both sweeps), so the
checkers can say no. The gate probe itself had already run three of these checks before
printing the certificate (`n=55 CERTIFIED sweep=1 endpoints=1`).

## Predictions

| id | prediction | probability | outcome |
|---|---|---|---|
| L1 | `test_slr_lp.py` passes and the module is committed | 85% | **true** (commit f097440) |
| L2 | polish raises the published n = 54 certificate's E by more than 0.001 | 50% | **not observed**: the gate shows only the last 3,000 characters of a report, and that line was cut off |
| L3 | some probe certifies n = 55 | 10% | **true** (LP1) |
| L4 | best E at n = 55 beats -0.2570 | 70% | **true** (+0.1163) |
| L5 | best E at n = 55 is at least -0.10 | 35% | **true** |
| L6 | LP1 runs with worker processes (`mode=pool4`) | 70% | **true by inference**: the mode line was cut off, but the report lists at least two worker results (one at E = -0.280, the best at +0.116), which serial mode cannot produce |

Probe reports (tails as shown by the publish gate, 2026-11-25):

- **LP1** (base 54, seed 1, 4 workers): `BEST n=55 E=0.11628 ratio=0.997928`,
  `n=55 CERTIFIED sweep=1 endpoints=1`, then the certificate (copied into `certs_lp.json`).
  One other worker ended at E = -0.2800 (no kept swaps out of 97), so the success depended
  on which new speed a worker started from.
- **LP2** (base 54, seed 2, speeds restricted to <= 40 or 7-smooth): not certified. Its best
  configuration used the same 54 speeds plus speed 152 (LP2's workers started from other
  new speeds, and its swaps were limited to speeds that exclude 195). Its E value was cut off.
- **LP3** (base 53 + 2): no report (the gate stopped before it, as with route 5's third probe).

## What it means and what is next

The gap in which the shifted conjecture is not known to fail is now **56 <= n <= 94**.
Route 7 (`slr_chain.py`, `PREREG_chain.md`) chains forward from this certificate one runner
at a time with the same polish.

Scoop check before this report (2026-11-25, 11:10-11:25 UTC): issue #110 of
1337isnot1337/solved-conjectures (last comment 2026-11-22: "55 <= n <= 94 is open"), that
repository's newest commits (none on lonely runners), GitHub repository search for
"shifted lonely runner" (only this repository, criado's and endorh's older code), arXiv
"lonely runner" newest first (newest 2610.40694; nothing on 55..94), jerryckim16/Math-Research
pull requests up to #79 (unshifted LRC(14)/(15) and kissing numbers only), and a web search for
a 55-runner counterexample (none).
