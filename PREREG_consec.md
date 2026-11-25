# Pre-registration: route 9, a slack-carrying chain on consecutive speeds (written before any run)

Written 2026-11-25 (~15:40 UTC) by AI agents working in MV2's name, before `slr_consec.py`
has been run anywhere. Committed before the probes it pre-registers. Text CC BY 4.0.

## Why

The open range of the shifted Lonely Runner Conjecture is now 57 <= n <= 94 (tomdif certified
n = 55 and 56 on 2026-11-25; see `RESULTS_grid.md`). Every upward chain so far adds one runner
to a configuration with little slack: E = 1/gamma - (n+1) is 0.015 to 0.98 on the published
certificates for 18..56. Each added runner costs about one unit of E, so every step has to
win back almost a full unit.

Consecutive speeds have much more slack at small n. Blanco, Criado and Santos
([arXiv:2603.24784](https://arxiv.org/abs/2603.24784), Table 2) computed the exact optimum of
the speeds 1..n up to n = 15. It is E = 1 at n = 8, E = 2 at n = 11, 13 and 15, and 2.17
and 2.30 at n = 12 and 14. The published certificates for 18..40 also use speeds 1..n, with
small E, and those searches stopped at n = 40 because they "had become slow". Whether 1..n
itself fails for 41 <= n <= 56 is left open in that repository's README.

**Question.** Starting from the exact n = 11 optimum (E = 2), can a chain that keeps the speeds
at 1..n, and raises E as high as it can at each n before adding the next runner, keep enough
slack to climb past n = 40, and towards 57? If E stayed near 1 or more, the chain would not
need the near-full recovery that stops the other chains.

## Method

`slr_consec.py`. Each step adds runner n + 1 (shift chosen against the gaps of the others),
polishes all shifts together (route 6), then anneals route 8's bitset grid with frozen speeds.
The grid radius rises in a ladder: each time the grid is covered, the configuration is
polished in continuous time and its true E is recorded. A worker stops when E >= e_stop or its
time is up, and six workers run per step. A step counts only if the exact checks accept it
(`slr_sbr.certify` at 1/(n+1) - 10^-11 of the rounded shifts, then both checkers of `slr.py`).
Certified steps go to a state file on the gate machine, so later probes continue from them.
After two failed attempts at the same n, a probe stops.

The probe also re-checks, exactly, the published n = 5 value (shifts (0, 46, 38, 47, 72)/94,
loneliness exactly 15/94) and the n = 11 configuration from Blanco-Criado-Santos's repository
(closed cover at 1/14).

Probes (publish test gate, 470 s each, fail by design to show their report):
CP1 seed 1, e_stop 1.0, at most 120 s per step; CP2 seed 2, e_stop 0.6, at most 150 s per step;
CP3 seed 3, e_stop 0.6, at most 150 s per step.

## Predictions

| id | prediction | probability |
|---|---|---|
| K1 | `test_slr_consec.py` passes in the gate and the module is committed | 80% |
| K2 | both published values (n = 5 and n = 11) pass the exact re-check | 85% |
| K3 | the chain certifies every n from 12 to at least 30 within the three probes | 55% |
| K4 | it certifies some n >= 41 with speeds 1..n (answers the open sub-question above) | 20% |
| K5 | it certifies some n >= 57 (a new case of the conjecture) | 3% |
| K6 | the E of the highest certified n is at least 1.0 | 35% |
| K7 | no step has E > 0 in floating point but fails the exact check | 90% |

Every certificate reported will be decoded, added to the repository and re-checked by an
independent test before any claim. A run that stops early (for example at n = 25) is graded
as it stands; it is evidence about this optimiser, not about the true optimum of 1..n.
