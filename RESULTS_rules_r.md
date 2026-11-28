# Results so far: route 19d (PREREG_rules_r.md) -- interim, not graded

Written 2026-11-28 about 03:35 UTC from gate probes R1 (00:42 UTC) and R2 (00:51 UTC). Probe R3's
report did not reach us. Route 19d is still running: this file records what has been seen and one
change to how its probes run. MV2, Munim, Inc. Made with AI agents working in MV2's name; no human
expert has checked it. Text CC BY 4.0.

## What ran

`test_top_r.py` passed in the gate (commit 6ec1c52, release v0.22.0), so **S1 holds**. The probes
ran `top_r.probe_r(budget=520)` against one cache. The ends of their reports, copied exactly
(route 19c's lines, which they also printed, are in RESULTS_rules_q.md):

```
R1 (end):
r64:F3/48 r64g2:U1/147 r96g2:U1/148 r60:U2/58 r75:U1/58 r80:U1/43 r90:- r72:- r81:-
r59:- r61:- ... (all others -)
RIT iterations=9 solve_s=473 per_it=52.6
SANE r64 R=8,32,72,96 S=12@1/2,-1/2 16@0,1 24@1/2,-1/2 36@1/2,-1/2 48@1/2,1/2 64@0,-1 128@0,1 A=3@3/4,-1/2 9@3/4,0 27@3/4,0
STATUS new_n=- -=33 FOUND=1 UNKNOWN=5

R2 (end):
r64:F3/48 r64g2:U1/147 r96g2:U1/148 r60:U2/58 r75:U1/58 r80:U1/43 r90:U2/58 r72:U1/58 r81:U1/58
r59:U2/57 r61:U3/58 r62:U3/57 r63:U2/57 r65:U2/58 r66:U2/38 r67:- r68:- r69:-
... (all others -)
RIT iterations=27 solve_s=921 per_it=34.1
SANE r64 (same rule)
STATUS new_n=- -=24 FOUND=1 UNKNOWN=14
```

## What has been seen

- **S2 so far: holds.** The sanity tier r64 (N = 64, gain 1, 5-smooth menu, from scratch) was
  FOUND in its first turn, after 3 solver calls and 48 s, and all three global exact checkers
  accepted it at R = 1/64. No tier is BUG through R2. **R-R2 (r64 FOUND within two turns): Yes.**
- **A third certified n = 63 cover** (not a new case; n = 63 is Callens's). On the base
  2, 4, ..., 128 at shift 0 (delta = 1/65): remove 8, 32, 72, 96; rephase 12, 24, 36 to
  1/2 - delta/2, 48 to 1/2 + delta/2, 16 and 128 to +delta, 64 to -delta; add 3 at
  3/4 - delta/2 and 9, 27 at 3/4. It touches 14 speeds (4 removed, 7 rephased, 3 added). All of
  its speeds are 3-smooth, even though the tier allowed 5. It is written out as `RULE_R64` in
  `test_cover_r64.py`, which re-checks it with `fixed_check`, `top_q.full_cert` (three global
  exact checkers) and the clause-soundness test.
- **No target decided yet.** 14 of 38 targets had at least one turn by R2, all UNKNOWN.

## Why no target was decided: a cut-off solver call adds nothing

In route 19d's search (`top_p.cegar_p`) a solver call that runs out of time returns no candidate,
so the turn adds no new classes; the next turn rebuilds the same model and starts again. Tokens
count every call, the cut-off one included. So `r64g2:U1/147` and `r75:U1/58` are turns whose only
call was cut off, and those tiers made no progress at all. With 5-smooth speeds a call often
takes longer than the 60 s per-turn cap of PREREG_rules_r.md (mean 34 s per call by R2, and the
gain-2 calls ran past 140 s). With that cap many tiers could stay UNKNOWN for ever.

**Change from 2026-11-28 (probes R4-R6), procedural only.** The probes set the per-turn cap to
170 s for gain-1 tiers and 250 s for the two gain-2 tiers, and run only the eight first targets
of the pre-registration (r60, r75, r80, r90, r72, r81, then r64g2 and r96g2; the order puts the
cheaper gain-1 tiers first). The other 30 targets keep their state and are taken up after these.
This changes how long a solver call may run and which tiers go first. It does not change any
tier, menu, radius, clause or checker, so FOUND and INFEASIBLE mean exactly what the
pre-registration says. The predictions R-R3 (at least 20 of 38 decided within R1-R6) and R-R4
are graded as written.

## Not yet graded

R-R1 (S1-S3 hold: S1 and S3 hold, S2 holds so far), R-R3, R-R4 and R-R5 are graded in the final
RESULTS_rules_r.md, after every tier is decided or the route is closed.
