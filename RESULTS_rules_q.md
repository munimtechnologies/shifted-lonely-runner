# Results: route 19c (PREREG_rules_q.md)

Graded 2026-11-28 about 00:40 UTC from gate probes Q1 (2026-11-27 23:06 UTC) and Q2 (23:15 UTC).
**Confirmed 2026-11-28 about 03:30 UTC** from route 19d's probe R1 (00:42 UTC), which printed
route 19c's final cache state, Q3 included (addendum below). MV2, Munim, Inc. Made with AI agents
working in MV2's name; no human expert has checked it. Text CC BY 4.0.

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
q64g2, q96g2, q72, q81, q95 and q63. We first read this from the counts; the addendum shows
their tokens.

## Addendum: route 19c's final state, printed by route 19d's probe R1

Route 19d's probe R1 (2026-11-28 00:42 UTC, `top_r.q1_lines`) read route 19c's cache after
probe Q3, whose own report had not reached us. Copied exactly:

```
QSTATE FOUND=2 INFEASIBLE=38 UNKNOWN=2 QIT it=95 solve_s=1262 per_it=13.3
QTOK q64:F3/4 q96:F3/4 q64g2:I1/6 q96g2:I2/10 q72:I1/12 q81:I3/49 q95:I3/16 q63:I1/6 q65:I1/10 q64g2p5:U14/480 q96g2p5:U14/496
QBUG none
```

- The six cut-off tokens are all INFEASIBLE (I), as the counts said: q64g2 (n = 62 at N = 64),
  q96g2 (n = 94 at N = 96), q72, q81, q95 and q63.
- No tier is BUG, Q3 included. This is sanity rule S3 of PREREG_rules_r.md: it **holds**.
- Q3 ran 13 more solver calls (82 -> 95 iterations, 849 -> 1262 s), all on the two 5-smooth
  gain-2 tiers, which stayed UNKNOWN (U14/480 and U14/496). Route 19d resumes them as r64g2 and
  r96g2.
- `test_top_r.py` passed in the gate (commit 6ec1c52, release v0.22.0): every clause of every
  touched class was rebuilt for five certified covers (SIMPLE_63 with 3- and 5-smooth menus,
  RULE_Q64, RULE_Q96 and Poliakova's 9 -> 8 rule at N = 96) and none was falsified; two failing
  rules falsified clauses only in classes where `fixed_check` also fails. So the clause generator
  passed the soundness check that route 19c's negatives rest on.

## Grades

| prediction | said | outcome |
|---|---|---|
| Q-R1: tests pass, q64 and q96 FOUND, no BUG | yes, 75% | **Yes.** Both tests passed, both sanity tiers FOUND and certified in Q1, and `QBUG none` after Q3. |
| Q-R2: mean solver time per iteration below 10 s after Q3 | yes, 50% | **No.** 6.8 s after Q1, 10.4 s after Q2, **13.3 s after Q3**. |
| Q-R3: at least 10 of 40 targets decided | yes, 40% | **Yes.** 38 of 40 decided, all INFEASIBLE. |
| Q-R4: q64g2 (n = 62 at N = 64) decided INFEASIBLE | yes, 35% | **Yes** (`q64g2:I1/6`). |
| Q-R5: a certified counterexample for an open n | no, 3% yes | **No.** |

## What it means

1. **Menu size was the bottleneck.** In menu x (routes 19 and 19b) the solver decided none of
   its 37 targets (route 19b: 702 s of solver time over 32 iterations by P2). In menu q (36
   shift choices per speed, 4 for s0 times 9 for beta, instead of 8 times 21 = 168) it decided
   38 of 40, with 849 s of solver time over 82 iterations in all by Q2 (the two undecided
   5-smooth tiers included). Most targets took one iteration of 5 to 25 s, using the classes that
   routes 19 and 19b had already collected.
2. **A negative over the menu of both known gain-1 constructions.** Menu q has shifts s0 in
   {0, 1/4, 1/2, 3/4} and beta in halves of delta on [-2, 2]. Touchable speeds are the 3-smooth
   multiples of 4 up to 2N (and 2N itself if 3-smooth). Added speeds are the odd 3-smooth speeds
   up to 2N + 1. The menu contains Poliakova's 9 -> 8 rule at N = 96 and the n = 63 cover at
   N = 64 (both sanity tiers re-found such rules from scratch). Within it:
   - for every N in 59..95 except 64, no rule of gain 1 at N closes at the slack radius
     r = 128/(128 N + 1) just below 1/N. These are the candidates for n = N - 1, i.e. every open
     n in 58..62 and 64..94;
   - at N = 64 and N = 96, no rule of gain 2 does (n = 62 and n = 94).
3. **Two more certified covers.** The sanity tiers found two rules different from the ones
   already known. At N = 64: remove 4, 8, 32, 36, 96; rephase 12, 24 to 1/2 + delta/2, 48 to
   1/2 - delta/2, 16 to -delta, 64 to +delta, 128 to -delta; add 1 at 1/4 - delta/2 and 3, 9,
   27 at 1/4 (n = 63). At N = 96: remove 8, 32, 144, 192; rephase 12, 24, 36, 48, 96 to
   1/2 - delta/2, 72 to 1/2, 16, 64 to +delta; add 3 at 3/4 - delta/2 and 9, 27 at 3/4
   (n = 95, removing 144 instead of rephasing 96 as Poliakova's rule does). Neither is a new
   case. Both are written out in `top_r.py` (`RULE_Q64`, `RULE_Q96`) and re-checked there.

## Closest prior work (checked 2026-11-28 about 03:25 UTC)

- **Xavier Callens**, [Zenodo 24132291](https://zenodo.org/records/24132291): a narrow menu
  (q = 8, |j| <= 4) INFEASIBLE for n = 39..93 except n = 81 (UNKNOWN), but it also fails his
  own n = 63 positive control, and his wider menus (|j| = 8; bases of multiples of 3, 4, 6;
  q = 4 at N = 40..62) were UNKNOWN.
- **F1Justin's MathLab** ([github.com/F1Justin/MathLab](https://github.com/F1Justin/MathLab),
  MIT): a direct finite-menu SAT search at fixed K with at most K - 1 runners, radius
  64/(64K + 1), reported as infeasible for seven menus at K = 59 (primes up to 5 and up to 7)
  and for two phase menus (denominators 4 and 6, primes 2, 3, 5) at each K = 91..95
  (`papers/runners/frozen-extension.tex`, `snapshot/research/runner/direct_rule_frontier.log`,
  `papers/runners/evidence/replay/finite-menus.log`). K there is our N, so these are the cases
  n = 58 and n = 90..94. No positive control is reported. Our earlier notes described this work
  as a different family; that was wrong, and we correct it here.
- **So what is new in route 19c** is a fixed-N negative across all of N = 59..95 (except 64)
  in a menu that **passes positive controls**: the same menu and solver re-find both known
  gain-1 constructions (n = 63 at N = 64, n = 95 at N = 96) from scratch. Callens's negative at
  these N comes from a menu that misses his own n = 63 cover, so it cannot tell a weak method
  from an empty family; F1Justin's covers only N = 59 and 91..95 and reports no control. Also
  new: the gain-2 negatives at N = 64 and 96 (n = 62 and 94). Our radius 128/(128N + 1) is
  slightly larger than F1Justin's 64/(64N + 1), so covering is easier and INFEASIBLE says a
  little more; the menus differ, so neither result contains the other.

## Limits

- "INFEASIBLE" means no rule in menu q, on the even base 2, ..., 2N, closes at that one slack
  radius. It is not "no counterexample for n". Runners outside the menu, other bases, other
  radii between r and 1/(n + 1), and rules with larger gain at larger N are not covered.
- The proofs rest on CP-SAT's INFEASIBLE answers and on the clause generator
  `top_o.class_clauses_o` producing only necessary conditions. `test_top_r.py` (passed) rebuilds
  every clause for five certified covers and checks that none is falsified. There is no
  independent proof certificate (such as DRAT) yet.
