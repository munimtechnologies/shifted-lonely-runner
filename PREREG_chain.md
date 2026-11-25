# Pre-registration: route 7, a warm chain from the n = 55 certificate (written before any run)

Written 2026-11-25 (~11:40 UTC) by AI agents working in MV2's name, before `slr_chain.py` has
been run anywhere. Committed before the probes it pre-registers.

## Question

Starting from the exact n = 55 counterexample (`certs_lp.json`, E = 1/gamma - 56 = +0.116),
can route 6's polish carry the shifted Lonely Runner counterexamples forward one runner at a
time, n = 56, 57, ..., toward the open range's end at 94?

## Method

`slr_chain.py`. Each step adds one runner to the highest certified configuration (each of 4
worker processes starts from a different one of the best-ranked new speeds), then runs the
minimax polish of `slr_lp.py` and speed-swap / rigid-time-shift moves. A worker stops once
E >= e_stop; the step ends when one worker gets there (or at its time limit). A step counts
only if `slr_sbr.certify` (closed arcs, radius 1/(n+1) - 10^-11, shifts rounded to 10^-6)
and both exact checkers of `slr.py` (open arcs of radius 1/(n+1)) accept it. Each certificate
is printed (shifts in fixed-width base 36) and saved to a state file in the publish gate's temp
folder, so the next probe continues from the highest certified n (re-checked exactly before
use). Every reported certificate will be copied into `certs_lp.json` and re-checked by
`test_certs_lp.py` (four exact checkers) before any claim.

Probes (470 s each in the publish test gate; fail by design to show their report):
CH1 seed 1, e_stop 0.15; CH2 seed 2, e_stop 0.15; CH3 seed 3, e_stop 0.30. Each takes at
most 300 s per step and at most 4 steps.

## Predictions

| id | prediction | probability |
|---|---|---|
| C1 | `test_slr_chain.py` and `test_certs_lp.py` pass and are committed | 80% |
| C2 | some probe certifies n = 56 | 60% |
| C3 | the highest certified n after the three probes is at least 58 | 30% |
| C4 | the state file carries over: CH2's report says it started from a base above 55, given CH1 certified something | 70% |
| C5 | the highest certified n after the three probes is at least 60 | 10% |
| C6 | no probe hits an exact-check failure after a float success (`no(certify)` or `no(slr checkers)`) | 90% |

If the chain stalls (two failed steps at the same n), the next run tries jumping (adding two
runners at once), larger e_stop on the step before, and a pool of new speeds that includes
values above 240.
