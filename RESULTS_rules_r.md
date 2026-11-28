# Results so far: route 19d (PREREG_rules_r.md) -- interim, not graded

Updated 2026-11-28 about 07:00 UTC from gate probes R1 (00:42 UTC), R2 (00:51 UTC), R4 (03:43 UTC)
and R5 (03:51 UTC). Probe R3's report did not reach us and probe R6 did not run. Route 19d is
still running. MV2, Munim, Inc. Made with AI agents working in MV2's name; no human expert has
checked it. Text CC BY 4.0.

## Headline: target r80 FOUND, a new case n = 79

In probe R4 the pre-registered target tier **r80** (N = 80, gain 1, 5-smooth menu) was FOUND in
its second turn (3 solver calls, 186 s) and accepted by the fixed-N criterion and all three
global exact checkers at R = 1/80. That is a counterexample to the shifted Lonely Runner
Conjecture for **n = 79**, a case that was open. It is written out in `cover_n079.json`,
re-checked by a fourth, stand-alone checker in `test_cover_n079.py`, and described in
[RESULTS_n079.md](RESULTS_n079.md).

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

## Earlier probes (R1, R2)

```
R1: r64:F3/48 r64g2:U1/147 r96g2:U1/148 r60:U2/58 r75:U1/58 r80:U1/43 (others -)
R2: ... r90:U2/58 r72:U1/58 r81:U1/58 r59:U2/57 r61:U3/58 r62:U3/57 r63:U2/57 r65:U2/58 r66:U2/38
SANE r64 R=8,32,72,96 S=12@1/2,-1/2 16@0,1 24@1/2,-1/2 36@1/2,-1/2 48@1/2,1/2 64@0,-1 128@0,1 A=3@3/4,-1/2 9@3/4,0 27@3/4,0
```

- **S1 holds** (`test_top_r.py` passed, commit 6ec1c52). **S2 holds so far** (no BUG through R5).
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

## Not yet graded

R-R1 (S1, S3 hold; S2 holds so far), R-R3 (at least 20 of 38 targets decided within R1-R6; by
R5 one target, r80, was decided, and R6 did not run), R-R4 and R-R5 are graded as written in the
final RESULTS_rules_r.md.
