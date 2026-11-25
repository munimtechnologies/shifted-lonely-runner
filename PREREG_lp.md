# Pre-registration: route 6, minimax polish for n = 55 (written before any run)

Written 2026-11-25 (~08:50 UTC) by AI agents working in MV2's name, before `slr_lp.py`
has been run anywhere. Committed before the probes it pre-registers.

## Question

Can a polish that moves all shifts together (sequential difference-constraint programs,
`slr_lp.slp_polish`) plus speed-swap and rigid time-shift moves turn the published
n = 54 certificate (E = 0.7186) into a counterexample for **n = 55**, the smallest open case
of the shifted Lonely Runner Conjecture?

## Method

`slr_lp.py`. A change of shift Delta for runner i moves all of its arcs by x_i = -Delta/v_i
in time, and each hole's peak height changes by w (x_R - x_L), w = v_L v_R/(v_L + v_R).
Minimising the highest hole inside a trust box is therefore a system of difference
constraints, solved by Bellman-Ford and bisection on the level. Each step is kept only if
the loneliness recomputed from scratch really drops. Then greedy speed swaps (a runner takes
the unused speed and shift that best cover what the others leave) and rigid time shifts of a
random subset (s_k -> s_k - v_k tau; untried idea from the 18..54 authors' notes), each
followed by a short polish. A result counts only if `slr_sbr.certify` passes an exact
rational check at R = 1/56 - 10^-11 and both checkers of `slr.py` accept it.

Probes (each 470 s in the publish test gate; fail by design to show their report):

- **LP1** base n = 54, seed 1, 4 worker processes starting from the 1st-4th best new speeds.
- **LP2** base n = 54, seed 2, 4 workers, the 5th-8th best new speeds, swaps only to speeds
  <= 40 or 7-smooth speeds <= 240 (the pattern seen in the published 41..54 certificates).
- **LP3** base n = 53 plus two runners, seed 3, one process (control).

## Predictions

| id | prediction | probability |
|---|---|---|
| L1 | `test_slr_lp.py` passes and the module is committed | 85% |
| L2 | the polish lowers the loneliness of the published n = 54 certificate (E rises by more than 0.001) | 50% |
| L3 | some probe certifies n = 55 | 10% |
| L4 | best E at n = 55 over LP1-LP3 beats route 5's best (-0.2570) | 70% |
| L5 | best E at n = 55 is at least -0.10 | 35% |
| L6 | LP1 runs with worker processes (report says `mode=pool4`) | 70% |

If L3 comes true: the certificate goes into `certs_lp.json` with a standard-library test that
re-checks it with all three exact checkers, a fresh scoop check (arXiv, web, GitHub, the
1337isnot1337/solved-conjectures repository and its issue #110) is done, and only then is it
reported. If not, the best configurations printed by the probes are the warm starts for the
next probes.
