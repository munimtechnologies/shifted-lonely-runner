# Pre-registration: route 19e, 7-smooth single-base rules at N = 63, 70, 84

Frozen 2026-11-28 about 09:15 UTC, before any route-19e solver call. MV2, Munim, Inc.
(mv2@munimtech.com). Made with AI agents working in MV2's name; no human expert has checked it.
Text CC BY 4.0, code Apache-2.0.

## Why

Route 19d (PREREG_rules_r.md) found a gain-1 rule at N = 80 in menu q with 5-smooth speeds,
which gives the n = 79 cover (cover_n079.json). Both covers known inside the old open range
(Callens's n = 63 at N = 64, and ours at N = 80) move the top speed 2N by delta. With speeds
built from 2, 3 and 5, every base in 59..95 whose 2N is 5-smooth (60, 64, 72, 75, 80, 81, 90, 96)
was already a route-19d target. Letting the prime 7 in makes the top speed touchable at three
more bases in the open range: **N = 63 (2N = 126), N = 70 (140) and N = 84 (168)**, giving
n = 62, 69 and 83.

## What runs

- Code: `probe_t_lib.py` (gate probes T1, T2, ...), on top of the unchanged `top_p.cegar_p`,
  `top_o.pools_o` / `class_clauses_o` / `fixed_check` and `top_q.full_cert`.
- Menu q exactly as in routes 19c/19d (s0 in quarters, beta in halves of delta on [-2, 2],
  slack radius r = 128/(128(n+1)+1)), with P = (2, 3, 5, 7): touchable speeds are the 7-smooth
  multiples of 4 up to 2N and 2N itself; added speeds are the odd 7-smooth numbers up to 2N + 1.
- Tiers, in this order: **t63** (N = 63, gain 1, n = 62), **t70** (N = 70, gain 1, n = 69),
  **t84** (N = 84, gain 1, n = 83), and sanity **t80** (N = 80, gain 1, n = 79).
- One tier-turn per probe, fewest turns first, cap 440 s per turn (route 19d's calls took
  160-250 s and a cut-off call adds nothing). Each tier is seeded with the classes route 19d
  collected at the same N and gain, where it has any. State: %TEMP%/mv2-slr-t1.
- A FOUND tier must pass the fixed-N criterion, both slr.py global checkers and indep_cover at
  R = 1/(n+1) (top_q.full_cert), and the stand-alone `verify_cover.first_gap`, with distinct
  speeds and at most n runners. A FOUND that fails any of them is a BUG and is reported.

## Predictions and grading (written before any result)

- **T-R1 (sanity):** t80 is FOUND within its first two turns. The n = 79 rule lies in this
  menu, so INFEASIBLE at t80 would show a bug in the clauses and would void every route-19e
  INFEASIBLE. Prediction: **Yes** (80%).
- **T-R2 (headline):** at least one of t63, t70, t84 is FOUND and accepted by all four checkers:
  a new case of the shifted conjecture failing (n = 62, 69 or 83), subject to a fresh
  prior-work check, then written out as cover_nXXX.json with its own committed test.
  Prediction: **No** (15% yes). Route 19c's 3-smooth menu had no rule anywhere except 64, and
  5 added only N = 80 so far.
- **T-R3:** an INFEASIBLE target means only that there is no gain-1 rule at that N in this
  menu. It says nothing about whether the shifted conjecture fails for that n.
- **T-R4 (budget):** by the end of probe T8, each of t63, t70, t84 is decided (FOUND or
  INFEASIBLE). Prediction: **No** (40% yes). If not, route 19e is reported as undecided at
  the solver's cost, not as a negative.

## What is not changed

No tier, menu, radius, clause builder or checker of routes 19c/19d is changed. Route 19d's tiers
keep their state in their own cache (mv2-slr-r1, read only here, for seeds).

## Addendum 1 (2026-11-28, about 10:50 UTC): a long-cap run next to the gate probes

Written after gate probes T1 and T2 and before any long-cap solver call. What T1 and T2 showed:
t63 ended UNKNOWN after one 440 s turn (2 solver iterations, 252 classes, seeded with 165 from
route 19d), and t70 ended UNKNOWN after one turn (3 iterations, 266 classes, 87 seeded). Probe T3
(t84) was filed but did not run in that publish window. At about 150-210 s per solver call, the
gate's one turn per probe will not decide these tiers within T8.

So the same search also runs in `long_run.py`, on a machine that can run for many hours:

- Same CEGAR (`top_p.cegar_p`), same menu q, same clauses, slack radius and fixed-N check, same
  four exact checks of any FOUND (`top_q.full_cert` and `verify_cover.first_gap` through
  `probe_t_lib.stand_alone`). Only the per-turn cap changes: 3600 s instead of 440 s, with 3
  solver workers.
- Each tier resumes from the classes the gate probes collected (copies of mv2-slr-t1 and
  mv2-slr-r1). A class id is valid in any run at the same N and gain, so a resumed INFEASIBLE
  means the same as one from scratch.
- Tiers, fewest long turns first: t63, t70, t84, t80 (sanity), then route 19d's undecided tiers
  whose top speed 2N is 5-smooth: r80g2 (n = 78, the tier probe R7 added outside route 19d's
  pre-registration), r60, r75, r90, r72, r81.
- Grading: T-R1, T-R2 and T-R3 are graded on whatever the gate probes and the long run decide
  together, reported separately. **T-R4 is graded on the gate probes alone**, as written; the
  long run is reported next to it and does not turn a No into a Yes. Route 19d's R-R1 to R-R5
  keep their own pre-registered windows; any long-run decision of a route-19d tier is reported
  as outside that window.
- A FOUND for an open n is published only after a fresh prior-work check, as cover_nXXX.json
  with its own committed test, as in T-R2.

Prediction for the long run, written now: at least one of t63, t70, t84 is decided (FOUND or
INFEASIBLE) within 20 hours of long run: **Yes** (55%). Any new case found (one of n = 62, 69,
83, 78, 59, 74, 89, 71, 80): **No** (15% yes).
