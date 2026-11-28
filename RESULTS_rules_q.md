# Results: route 19c (PREREG_rules_q.md)

Graded 2026-11-28 about 00:40 UTC from gate probes Q1 (2026-11-27 23:06 UTC) and Q2 (23:15 UTC).
Probe Q3's report did not reach us. Route 19d's probes print route 19c's final cache state
(`QSTATE`, `QTOK`, `QBUG` in `top_r.py`), and the two points that depend on Q3 are marked
below. MV2, Munim, Inc. Made with AI agents working in MV2's name; no human expert has checked
it. Text CC BY 4.0.

## What ran

`test_top_q.py` and `test_cover_n063_simple.py` passed in the gate (commits 4304a46 and f2de5a1,
releases v0.21.0 and v0.21.1). Probes Q1 and Q2 ran `top_q.probe_q(budget=520)` against one
cache. Only the end of each report comes back, so the first tokens are cut off. These are the
lines we saw, copied exactly:

```
Q1 (end):
...1/6 q65:I1/10
q59:I1/5 q60:I1/13 q61:I1/6 q62:I1/7 q66:I1/22 q67:I1/9 q68:I2/11 q69:I2/9 q70:I1/7
q71:I1/14 q73:I1/10 q74:I1/13 q75:I1/20 q76:I1/18 q77:I1/11 q78:I1/10 q79:I1/9 q80:I1/13
q82:I1/10 q83:I1/8 q84:I1/9 q85:I1/14 q86:I1/13 q87:I1/12 q88:I4/12 q89:I3/13 q90:I4/13
q91:I2/24 q92:I3/25 q93:I4/16 q94:- q64g2p5:- q96g2p5:-
QIT iterations=63 solve_s=427 per_it=6.8
SANE q64 R=4,8,32,36,96 S=12@1/2,1/2 16@0,-1 24@1/2,1/2 48@1/2,-1/2 64@0,1 128@0,-1 A=1@1/4,-1/2 3@1/4,0 9@1/4,0 27@1/4,0
SANE q96 R=8,32,144,192 S=12@1/2,-1/2 16@0,1 24@1/2,-1/2 36@1/2,-1/2 48@1/2,-1/2 64@0,1 72@1/2,0 96@1/2,-1/2 A=3@3/4,-1/2 9@3/4,0 27@3/4,0
STATUS new_n=- -=3 FOUND=2 INFEASIBLE=36 UNKNOWN=1

Q2 (end):
... q91:I2/24 q92:I3/25 q93:I4/16 q94:I3/12 q64g2p5:U8/249 q96g2p5:U7/228
QIT iterations=82 solve_s=849 per_it=10.4
SANE q64 (same rule)
SANE q96 (same rule)
STATUS new_n=- FOUND=2 INFEASIBLE=38 UNKNOWN=2
```

Tokens are `tag:<F|I|U><iterations>/<seconds>`. A rule is R = removed, S = rephased w@s0,beta
(shift s0 + beta delta), A = added odd speeds, on the base 2, 4, ..., 2N with delta = 1/(N + 1).
SANE means FOUND from scratch and accepted by all three global exact checkers at R = 1/(n + 1).

**Which tiers are INFEASIBLE.** There are 42 tiers (2 sanity, 40 targets). After Q2: FOUND = 2
(the two SANE tiers), UNKNOWN = 2 (q64g2p5 and q96g2p5, both visible), INFEASIBLE = 38, nothing
else. So every other tier is INFEASIBLE. That includes the six whose tokens were cut off:
q64g2, q96g2, q72, q81, q95 and q63. We read this from the counts, not from their tokens;
route 19d's `QTOK` line prints them.

## Grades

| prediction | said | outcome |
|---|---|---|
| Q-R1: tests pass, q64 and q96 FOUND, no BUG | yes, 75% | **Yes** through Q2. Both tests passed, both sanity tiers FOUND and certified in Q1, no BUG in either report. Q3 is unseen; route 19d's `QBUG` line confirms or overturns this. |
| Q-R2: mean solver time per iteration below 10 s after Q3 | yes, 50% | **No.** 6.8 s after Q1, 10.4 s after Q2. The 19 iterations between Q1 and Q2 averaged 22 s ((849 - 427)/19). After Q2 only the two 5-smooth tiers were left, so Q3 can only have raised the mean. |
| Q-R3: at least 10 of 40 targets decided | yes, 40% | **Yes.** 38 of 40 decided, all INFEASIBLE. |
| Q-R4: q64g2 (n = 62 at N = 64) decided INFEASIBLE | yes, 35% | **Yes**, read from the counts (above). |
| Q-R5: a certified counterexample for an open n | no, 3% yes | **No.** |

## What it means

1. **Menu size was the bottleneck.** In menu x (routes 19 and 19b) the solver decided none of
   its 37 targets (route 19b: 702 s of solver time over 32 iterations by P2). In menu q (36
   shift choices per speed, 4 for s0 times 9 for beta, instead of 8 times 21 = 168) it decided 38 of 40, with 849 s of solver
   time over 82 iterations in all (the two undecided 5-smooth tiers included). Most targets
   took one iteration of 5 to 25 s, using the classes that routes 19 and 19b had already collected.
2. **A negative over the menu of both known gain-1 constructions.** Menu q has shifts s0 in
   {0, 1/4, 1/2, 3/4} and beta in halves of delta on [-2, 2]. Touchable speeds are the 3-smooth
   multiples of 4 up to 2N (and 2N itself if 3-smooth). Added speeds are the odd 3-smooth speeds
   up to 2N + 1. The menu contains Poliakova's 9 -> 8 rule at N = 96 and the n = 63 cover at
   N = 64 (both sanity tiers re-found such rules from scratch). Within it:
   - for every N in 59..95 except 64, no rule of gain 1 at N closes at the slack radius
     r = 128/(128 N + 1) just below 1/N. These are the candidates for n = N - 1, i.e. every open
     n in 58..62 and 64..94;
   - at N = 64 and N = 96, no rule of gain 2 does (n = 62 and n = 94).
   Callens's own negative note (Zenodo 24132291) found his narrow menu INFEASIBLE for most n in
   39..93, but that menu also fails his n = 63 positive control. Menu q passes both positive
   controls, so its negative is informative about the family the known covers come from.
3. **Two more certified covers.** The sanity tiers found two rules different from the ones
   already known. At N = 64: remove 4, 8, 32, 36, 96; rephase 12, 24 to 1/2 + delta/2, 48 to
   1/2 - delta/2, 16 to -delta, 64 to +delta, 128 to -delta; add 1 at 1/4 - delta/2 and 3, 9,
   27 at 1/4 (n = 63). At N = 96: remove 8, 32, 144, 192; rephase 12, 24, 36, 48, 96 to
   1/2 - delta/2, 72 to 1/2, 16, 64 to +delta; add 3 at 3/4 - delta/2 and 9, 27 at 3/4
   (n = 95, removing 144 instead of rephasing 96 as Poliakova's rule does). Neither is a new
   case. Both are written out in `top_r.py` (`RULE_Q64`, `RULE_Q96`) and re-checked there.

## Limits

- "INFEASIBLE" means no rule in menu q, on the even base 2, ..., 2N, closes at that one slack
  radius. It is not "no counterexample for n". Runners outside the menu, other bases, other
  radii between r and 1/(n + 1), and rules with larger gain at larger N are not covered.
- The proofs rest on CP-SAT's INFEASIBLE answers and on the clause generator
  `top_o.class_clauses_o` producing only necessary conditions. Route 19d adds a test that rebuilds
  every clause for four certified covers and checks that none of them is falsified
  (`test_top_r.py`). There is no independent proof certificate (such as DRAT) yet.
- Q3's report is lost. The six cut-off tokens and the absence of a BUG in Q3 are re-printed by
  route 19d's probes.
