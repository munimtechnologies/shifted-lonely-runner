# Results so far: route 19d (PREREG_rules_r.md) -- interim, not graded

Updated 2026-11-28 about 09:10 UTC from gate probes R1 (00:42 UTC), R2 (00:51 UTC), R4 (03:43 UTC),
R5 (03:51 UTC), R7 (07:00 UTC) and R8 (07:08 UTC). Probe R3's report did not reach us and probes
R6 and R9 did not run. Route 19d is still running. MV2, Munim, Inc. Made with AI agents working in
MV2's name; no human expert has checked it. Text CC BY 4.0.

## Headline: target r80 FOUND, a new case n = 79

In probe R4 the pre-registered target tier **r80** (N = 80, gain 1, 5-smooth menu) was FOUND in
its second turn (3 solver calls, 186 s) and accepted by the fixed-N criterion and all three
global exact checkers at R = 1/80. So the shifted Lonely Runner Conjecture fails for
**n = 79**, a case that was open. It is written out in `cover_n079.json`, re-checked by a
fourth, stand-alone checker in `test_cover_n079.py` (committed in v0.23.0 after the gate
passed), and described in [RESULTS_n079.md](RESULTS_n079.md).

```
R4 (copied from the publish log):
r64:F3/48 r60:U3/226 r75:U3/227 r80:F3/186 r90:U3/80 r72:U1/58 r81:U1/58 r64g2:U1/147 r96g2:U1/148
RIT iterations=19 solve_s=1103 per_it=58.1
RULE r80 N=80 n=79 R=4,16,20,40,96,120 S=8@0,-1 12@1/2,1/2 24@1/2,1/2 32@0,-3/2 48@1/2,1/2 60@1/2,1/2 80@0,-1 160@0,1 A=3@1/4,0 5@1/4,1/2 9@1/4,0 15@1/4,0 45@1/4,0
CERT r80 {"ok": true, "n": 79, "N": 80, "sweep": true, "endpoints": true, "distinct": true, "R": "1/80", "seconds": 1.11, "indep": true}
STATUS new_n=[79] FOUND=2 UNKNOWN=7

R5:
r64:F3/48 r60:U3/226 r75:U3/227 r80:F3/186 r90:U3/80 r72:U2/226 r81:U2/227 r64g2:U2/312 r96g2:U1/148
RIT iterations=22 solve_s=1585 per_it=72.1
(same RULE and CERT lines for r80)
ALL -=15 FOUND=2 UNKNOWN=22
```

(A token `tag:Xi/s` is status, solver calls so far and seconds so far.)

## Probes R7 and R8 (after r80 was FOUND)

```
R7 (copied from the publish log, 2026-11-28 07:00 UTC):
SLACK R=1/80 covers=True gap=None
SLACK R=256/20481 covers=True gap=None
SLACK R=128/10241 covers=True gap=None
SLACK R=1/81 covers=False gap=1/160
DEL78 tried=79 covers_without=-
DEL78 seconds=17.0
r80g2:U3/436 r60:U4/394 r75:U4/314 r90:U3/80 r72:U2/226 r81:U2/227 r64g2:U2/312 r96g2:U2/397
RIT iterations=22 solve_s=2277 per_it=103.5
STATUS new_n=- UNKNOWN=8

R8 (07:08 UTC):
r80g2:U4/686 r60:U4/394 r75:U4/314 r90:U4/248 r72:U3/256 r81:U2/227 r64g2:U2/312 r96g2:U2/397
RIT iterations=25 solve_s=2710 per_it=108.4
STATUS new_n=- UNKNOWN=8
D r80g2 UNKN turns=3 it=4 cls=192 last_it=1 last_solve=246.5 last_sec=250.2
D r60 UNKN turns=3 it=4 cls=140 last_it=1 last_solve=162.5 last_sec=168.2
D r90 UNKN turns=3 it=4 cls=191 last_it=1 last_solve=162.8 last_sec=168.2
```

- **Slack.** The n = 79 cover covers with open arcs of radius 1/80, 256/20481 and 128/10241
  (the fixed-N criterion's closed slack radius), and does not cover at 1/81 (first gap at
  t = 1/160). So the cover is tight to within the fixed-N slack.
- **Deletion (DEL78).** Dropping any one of the 79 runners, with every other shift unchanged,
  leaves a gap at radius 1/79. So no n = 78 case follows from the n = 79 cover by deleting a
  runner. That rules out deletion only with the shifts kept fixed; re-solving the shifts after a
  deletion has not been tried.
- **Still undecided.** r80g2 (n = 78, the one tier added outside the pre-registration), r60, r75,
  r90, r72, r81, r64g2 and r96g2. Most turns ended with a solver call cut off at the cap
  (last_solve 160-250 s against caps of 170 and 250 s), which adds nothing. Route 19e
  (PREREG_rules_t.md) therefore uses a 440 s cap and one tier per probe.

## Earlier probes (R1, R2)

```
R1: r64:F3/48 r64g2:U1/147 r96g2:U1/148 r60:U2/58 r75:U1/58 r80:U1/43 (others -)
R2: ... r90:U2/58 r72:U1/58 r81:U1/58 r59:U2/57 r61:U3/58 r62:U3/57 r63:U2/57 r65:U2/58 r66:U2/38
SANE r64 R=8,32,72,96 S=12@1/2,-1/2 16@0,1 24@1/2,-1/2 36@1/2,-1/2 48@1/2,1/2 64@0,-1 128@0,1 A=3@3/4,-1/2 9@3/4,0 27@3/4,0
```

- **S1 holds** (`test_top_r.py` passed, commit 6ec1c52). **S2 holds so far** (no BUG through R8).
  **R-R2 (r64 FOUND within two turns): Yes.** The sanity tier's cover is `test_cover_r64.py`
  (a third n = 63 cover, not a new case).

## Procedural changes (do not change any tier, menu, radius, clause or checker)

- From R4: per-turn cap 170 s for gain-1 tiers and 250 s for gain-2 tiers, and the first eight
  targets of the pre-registration run first (a cut-off solver call adds nothing, so a 60 s cap
  could leave tiers UNKNOWN for ever).
- From R7 (probe_r7_lib.py): **one tier added outside the pre-registration**, r80g2 (N = 80,
  gain 2, 5-smooth; n = 78), chosen after r80 was FOUND. It is reported separately and is not
  counted in R-R3 or R-R4. R7-R9 run r80g2 first, then r60, r75, r90, r72, r81, r64g2, r96g2.
  They also print whether the n = 79 cover covers with open arcs at 256/20481 (between the
  closed slack radius 128/10241 and 1/80; the fixed-N criterion implies it must).

## Grades (2026-11-28, against the predictions written in PREREG_rules_r.md)

- **R-R1** (S1, S2, S3 hold; predicted Yes): S1 and S3 hold; S2 (no BUG) holds through R8.
  Final grade when the route stops.
- **R-R2** (r64 FOUND within two turns; predicted Yes): **Yes.**
- **R-R3** (at least 20 of the 38 targets decided within R1-R6; predicted Yes, 45%): **No.**
  The window is closed (R6 did not run): one target, r80, was decided. The solver calls in
  this menu take far longer than in the 3-smooth menu of route 19c.
- **R-R4** (every decided target INFEASIBLE; predicted Yes, 85%): **No.** The prediction
  failed: r80 was FOUND.
- **R-R5** (some target FOUND and certified by all three checkers; predicted No, 5% yes):
  **Yes.** r80, n = 79. Our own forecast put this at 5%.
