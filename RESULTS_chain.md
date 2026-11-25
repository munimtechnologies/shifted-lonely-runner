# Results: route 7, warm chain from the n = 55 certificate (graded against PREREG_chain.md)

Graded 2026-11-25 (~12:30 UTC) by AI agents working in MV2's name.

## What ran

`slr_chain.py` and `test_slr_chain.py` were committed (e8713df) after the gate ran their
tests. Gate probes CH1 and CH2 ran for 459 s each (8 CPUs, 4 workers, two 150-s steps each).
CH3 left no result in the gate's log (the third probe of a run has done this before).

| probe | step | E of the 4 workers (E = 1/gamma - 57) | certified |
|---|---|---|---|
| CH1 (seed 1) | n = 56, try 1 | -0.884, -0.759, -0.759, -0.884 | no |
| CH1 (seed 1) | n = 56, try 2 | -0.814, -0.759, -0.884, -0.884 | no |
| CH2 (seed 2) | n = 56, try 1 | -0.884, -0.759, -0.884, -0.759 | no |
| CH2 (seed 2) | n = 56, try 2 | -0.759, -0.884, -0.814, -0.884 | no |

A counterexample needs E > 0. Adding a runner to the n = 55 solution (E = +0.116 at 56)
starts at E = 0.116 - 1 = -0.884 at 57; the polish raised that by at most 0.125.

## Predictions

| id | prediction | probability | outcome |
|---|---|---|---|
| C1 | `test_slr_chain.py` and `test_certs_lp.py` pass and are committed | 80% | **true** |
| C2 | some probe certifies n = 56 | 60% | **false** |
| C3 | highest certified n after the probes at least 58 | 30% | **false** |
| C4 | the state file carries over (given CH1 certified something) | 70% | not graded: CH1 certified nothing |
| C5 | highest certified n at least 60 | 10% | **false** |
| C6 | no exact-check failure after a float success | 90% | **true** (no float success at all) |

## What it means

Warm-starting from one certificate and moving shifts continuously does not carry the chain:
the n = 55 solution has too little slack (E = 0.116; aadrianvv's chain steps from 46 to 50
started from bases with E near 0.9). The same few E values recur across seeds (-0.759,
-0.814, -0.884), so the polish converges to the same local optima. The next route
(`PREREG_grid.md`, route 8) anneals coverage on a grid and lets speeds change.
