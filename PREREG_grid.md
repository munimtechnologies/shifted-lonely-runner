# Pre-registration: route 8, grid annealing of whole-circle coverage (written before any run)

Written 2026-11-25 (~12:40 UTC) by AI agents working in MV2's name, before `slr_grid.py` has
been run anywhere. Committed before the probes it pre-registers.

## Why a new route

Route 7 (`slr_chain.py`, graded in `RESULTS_chain.md`) added one runner to the n = 55
certificate and polished all shifts together. At n = 56 every worker stopped between
E = -0.88 and E = -0.76 (E = 1/gamma - 57; a counterexample needs E > 0). The polish only
moves shifts continuously and keeps the speeds, so it stays in the basin of the n = 55
solution. aadrianvv's annealer (issue 110 of 1337isnot1337/solved-conjectures) reached
n = 41..54 by annealing a count of uncovered grid cells with moves that also change speeds.

## Method

`slr_grid.py`. The time circle is cut into G cells (G = 2^20, or 2^19 in GP3). A runner of
speed v at integer offset k covers the cells whose centres lie in its arcs of radius r (the
search radius 1/(n + 1 + e_g)); its shift is -v k / G. Each runner's cells are one big
integer of G bits, and coverage counts are kept bit-sliced in 7 big integers, so the change
in the number U of uncovered cells after a move costs a few big-integer operations.
Moves: push the runner whose arc edge is nearest to a random uncovered cell just far enough
to cover it (55%), small jitter (20%), push a random runner (15%), give a runner a new unused
speed up to 240 aimed at an uncovered cell (10%). Metropolis acceptance on U with a cyclic
geometric temperature (start 4, 8 or 16 cells by worker, end 0.3; cycle 6000 moves).

Each step starts from the highest certified configuration (the repository's `certs_lp.json`
or the gate's state file, re-checked exactly), and each of 6 workers adds a different
best-ranked new speed. When U = 0 the grid solution is converted to exact shifts, its true
loneliness is computed and polished (route 6), and it is certified only if `slr_sbr.certify`
(closed arcs of radius 1/(n+1) - 10^-11) and the two exact checkers of `slr.py` accept it;
otherwise e_g grows by 0.15 and the annealing continues. Grid results are never claimed.

Probes (470 s each in the publish test gate, fail by design to show their report; at most
440 s per step and 4 steps): GP1 seed 1, G = 2^20, e_g = 0.3; GP2 seed 2, same; GP3 seed 3,
G = 2^19, e_g = 0.5. The state file carries certificates from one probe to the next.

## Predictions

| id | prediction | probability |
|---|---|---|
| G1 | `test_slr_grid.py` passes in the gate and is committed | 75% |
| G2 | some probe certifies n = 56 | 30% |
| G3 | the highest certified n after the three probes is at least 58 | 8% |
| G4 | in GP1, the best E reported at n = 56 is above route 7's -0.76 | 60% |
| G5 | no probe reports a pool failure, and at least one worker per probe reaches U = 0 at its starting radius | 50% |
| G6 | no worker hits an exact-check failure after a float success | 90% |

Every reported certificate will be copied into `certs_lp.json` and re-checked by
`test_certs_lp.py` before any claim. If route 8 stalls too, the next options are a pool of
strong n = 55 solutions (anneal at fixed n with rising e_g), adding two runners at once, and
a C version of the same annealer as a compete job.
