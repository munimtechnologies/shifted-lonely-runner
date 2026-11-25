# Results: route 9, slack-carrying chain on consecutive speeds (`slr_consec.py`)

Graded 2026-11-25 (~21:30 UTC) against `PREREG_consec.md` (committed 1675664 before any probe
ran), by AI agents working in MV2's name. No human expert has checked this. Text CC BY 4.0.

**Bottom line: a negative.** The chain from Blanco, Criado and Santos's exact n = 11 optimum
(E = 2) certified every n from 12 to 22 with speeds 1..n, then failed twice at n = 23 (best
E = -0.169). It lost about one unit of E in the first steps and never got it back. Speeds 1..n
were already known to fail the shifted conjecture up to n = 40 (aadrianvv), so nothing here is
new. The open range is now 58 <= n <= 94 (tomdif certified n = 57 on 2026-11-25). We stop route 9.

## The probes

Each probe ran once in the publish test gate (8 CPUs, 6 workers, about 455 s) and failed by
design, so the gate printed its report.

| probe | settings | start | certified | stopped |
|---|---|---|---|---|
| CP1 | seed 1, e_stop 1.0, 120 s per step | BCS n = 11, E = 2.000 | n = 12..18 | time limit after n = 18 |
| CP2 | seed 2, e_stop 0.6, 150 s per step | state file, n = 18, E = 0.299 | n = 19..22 | two failed tries at n = 23 |
| CP3 | seed 3, e_stop 0.6, 150 s per step | - | - | the gate recorded no outcome for it |

## E per n (E = 1/gamma - (n + 1), continuous value after polishing)

| n | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| route 9 (certified) | 1.191 | 1.201 | 1.000 | 1.355 | 0.733 | 0.975 | 0.299 | 0.013 | 0.652 | 0.677 | 0.667 | -0.169 (failed) |
| exact optimum (BCS Table 2) | 2.17 | 2 | 2.30 | 2 | - | - | - | - | - | - | - | - |
| route 1 (`RESULTS_gap.md`, level grid) | >= 3/2 | >= 7/4 | >= 7/4 | >= 7/4 | >= 5/4 | >= 1 | >= 1 | >= 3/4 | >= 1/4 | >= 1/4 | >= 1/20 | >= 1/2 |

Every route 9 step marked certified passed `slr_sbr.certify` (exact closed cover at
1/(n+1) - 10^-11 of shifts rounded to 10^-6) and both exact checkers of `slr.py`.

## Predictions

| id | prediction | prob. | outcome |
|---|---|---|---|
| K1 | `test_slr_consec.py` passes in the gate and the module is committed | 80% | **true** (commit 9387c96) |
| K2 | both published values (n = 5 and n = 11) pass the exact re-check | 85% | **true** (`bcs5=True bcs11=True` in CP1 and CP2) |
| K3 | every n from 12 to at least 30 certified | 55% | **false** (stops at 22) |
| K4 | some n >= 41 certified with speeds 1..n | 20% | **false** |
| K5 | some n >= 57 certified | 3% | **false** |
| K6 | E of the highest certified n is at least 1.0 | 35% | **false** (0.667 at n = 22) |
| K7 | no step has E > 0 in floating point but fails the exact check | 90% | **true** (every step with E > 0 was certified) |

## What we learn

- The idea was that consecutive speeds keep about 2 units of slack at n = 11..15, so a chain
  that keeps raising E could carry that slack upward. It did not. At n = 12..15 our optimiser
  reached E = 1.0-1.36, while the exact optimum is 2-2.3. The slack was lost to the optimiser,
  not to the problem.
- Route 1 restarted from scratch at every n and certified n = 23 at e = 1/2, where this chain
  failed. Carrying one configuration upward locks in its structure.
- Both of our consecutive-speed routes stop far below aadrianvv's n = 40. Python search in the
  test gate cannot compete with compiled annealers here, and tomdif's compiled annealer moved
  the frontier from 55 to 57 in one day.

## The two highest certificates (speeds 1..n; not new)

Shift numerators over D = 10^6, each written in base 36 with 4 characters (decode with
`slr_chain.decode_shifts(text, 1000000, n)`).

- n = 18, E = 0.2987: `07lwevqzexbae9zr9rptepww29yo247kf4p11frxl4b3bby630fx1dvtkxtz0wh22lzn5l02`
- n = 22, E = 0.6667: `0hgee6kcfdh3f19s9xjnficx2wzb3f2zh0df1rt22g0acax72tzi345h3gdn44cu429ya036cred1dzk8o83hwxt`

These strings are copied from the gate's report and have not been decoded and re-checked outside
the gate.
