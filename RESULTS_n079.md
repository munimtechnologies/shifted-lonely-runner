# A shifted Lonely Runner counterexample for n = 79

Written 2026-11-28 about 07:00 UTC. MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents
working in MV2's name; no human expert has checked it yet. Text and data CC BY 4.0, code
Apache-2.0.

## Result

The 79 runners of `cover_n079.json` have distinct positive integer speeds (largest 160), and
their open arcs {t : ||v_i t + s_i|| < 1/80} cover the circle. So at every time some runner is
closer than 1/(n+1) = 1/80 to the origin, and **the shifted Lonely Runner Conjecture fails for
n = 79**. Before this, the cases 58..62 and 64..94 were open (re-checked below), so 79 is a new
case. After it the open cases are **58..62, 64..78 and 80..94**.

This is one more case of a conjecture already known to be false for many n. It does not settle
Zhang's Question 8.5 (whether the shifted conjecture fails for every n >= 5).

## The configuration

Start from the speeds 2, 4, ..., 160 at shift 0 (N = 80). Their closed arcs of radius
delta = 1/81 cover the circle (Dirichlet). Then, with shifts written s0 + beta delta:

| change | speeds | shift |
|---|---|---|
| removed (6) | 4, 16, 20, 40, 96, 120 | - |
| rephased (8) | 8, 80 | -delta |
| | 32 | -3 delta/2 |
| | 160 | +delta |
| | 12, 24, 48, 60 | 1/2 + delta/2 |
| added (5) | 3, 9, 15, 45 | 1/4 |
| | 5 | 1/4 + delta/2 |

Gain 6 - 5 = 1, so 80 - 1 = 79 runners. All 19 touched speeds are 5-smooth. The explicit shifts
are 80/81 (speeds 8, 80), 53/54 (32), 1/81 (160), 41/81 (12, 24, 48, 60), 1/4 (3, 9, 15, 45) and
83/324 (5); the other 66 runners sit at 0.

## How it was found

Route 19d ([PREREG_rules_r.md](PREREG_rules_r.md)) searches, at one fixed base N, for a rule of
gain g in a small menu (shifts s0 in quarters, beta in halves of delta on [-2, 2]; touchable
speeds the 5-smooth multiples of 4 up to 2N and 2N itself; added speeds odd and 5-smooth) that
covers at the slack radius r = 128/(128(n+1)+1) < 1/(n+1). The exact counterexample-guided
search (`top_p.cegar_p`: CP-SAT proposes, `top_o.fixed_check` tests exactly, failing classes are
added) was pre-registered with r80 (N = 80, gain 1) among its first targets, because 2N = 160 is
5-smooth and allows the top trick that the n = 63 case uses. Tier r80 was FOUND in its second
turn, after 3 solver calls and 186 s, in gate probe R4 (2026-11-28 03:43 UTC). The report, copied
from the publish log:

```
r64:F3/48 r60:U3/226 r75:U3/227 r80:F3/186 r90:U3/80 r72:U1/58 r81:U1/58 r64g2:U1/147 r96g2:U1/148
RULE r80 N=80 n=79 R=4,16,20,40,96,120 S=8@0,-1 12@1/2,1/2 24@1/2,1/2 32@0,-3/2 48@1/2,1/2 60@1/2,1/2 80@0,-1 160@0,1 A=3@1/4,0 5@1/4,1/2 9@1/4,0 15@1/4,0 45@1/4,0
CERT r80 {"ok": true, "n": 79, "N": 80, "sweep": true, "endpoints": true, "distinct": true, "R": "1/80", "seconds": 1.11, "indep": true}
STATUS new_n=[79] FOUND=2 UNKNOWN=7
```

(`S=w@s0,beta` is a rephased speed, `A=` an added one. Probe R5 printed the same lines.)

## Checks

`test_cover_n079.py` re-checks the certificate in the publish gate before it is committed:

1. `verify_cover.py`, a stand-alone checker written for this certificate (standard library
   only, no shared code): an exact Fraction sweep over the open intervals of times in which
   each runner is closer than R to an integer. Its controls are proved by hand: speeds 1..10 at
   shift 0 cover at 1/10 and not at 1/11; the even base 2..160 covers at 1/80 and not at 1/81;
   the 79 runners cannot cover at 1/162 (total arc length 79/81 < 1); every reported gap is
   re-checked to be uncovered.
2. `slr.covers_sweep` and `slr.covers_endpoints`, the two global exact checkers used for every
   earlier certificate here.
3. `top_q.indep_cover`, an integer endpoint test (finitely many open arcs cover the circle iff
   every arc endpoint lies inside some arc).
4. `top_o.fixed_check`, the fixed-N criterion (proof in `top_o.py`): a closed cover at the slack
   radius 128/10241 < 1/80.

The test also checks that the explicit runner list in the JSON is exactly the rule applied to
the base. Anyone can re-run the main check with `python verify_cover.py cover_n079.json`.

## Prior work (checked 2026-11-28, 06:45-06:55 UTC)

- Zenodo API, "shifted lonely runner", newest first: the same four records as before (Bonfioli
  24189338; Callens 24132291, 24051700, 23842167). None claims n = 79.
- Zenodo API, "lonely runner": 74 records; the newest (Donahue 24618624, 28 Nov; Zhang 24573706,
  26 Nov) make no claim about shifted counterexamples in 58..94.
- arXiv "lonely runner", newest first: newest 2610.40694 (28 Oct). Poliakova's arXiv:2609.23952
  gives n >= 95; Blanco, Criado and Santos's arXiv:2603.24784 gives 5..17.
- GitHub 1337isnot1337/solved-conjectures pull requests "lonely": largest shifted case 57
  (tomdif, PR 660; Lean-checked 18..57 in PR 755); F1Justin's PR 1017 (open) bounds extensions of
  a fixed 57-runner cover.
- GitHub F1Justin/MathLab: newest commit 27 Nov 11:21 UTC; its finite-menu logs report only
  infeasible menus (K = 59, 91..95).
- Web search "shifted lonely runner" counterexample 79: nothing beyond the known cases.

Closest work: Callens's n = 63 counterexample ([Zenodo 24051700](https://zenodo.org/records/24051700)),
the only earlier case inside 58..94, on the base 2, ..., 128 with the same top trick; his
negative search ([Zenodo 24132291](https://zenodo.org/records/24132291)), whose narrow menu was
INFEASIBLE for n = 39..93 except 81 but also missed his own n = 63 cover; Poliakova's local rules
and n >= 95 ([arXiv:2609.23952](https://arxiv.org/abs/2609.23952)).

## What it suggests

Route 19c showed that with 3-smooth speeds the menu has no gain-1 rule at any base 59..95 except
64 ([RESULTS_rules_q.md](RESULTS_rules_q.md)). Letting the prime 5 in gives one at 80, a base
whose top speed 160 is 5-smooth. The other bases with 2N 5-smooth in range (60, 72, 75, 81, 90)
and gain 2 at N = 80 (n = 78) are the next tiers (probes R7-R9). Whether 7-smooth speeds open the
bases where 2N is 7-smooth (63, 70, 84) is a natural next route.

## Limits

One new case, proved by an explicit certificate checked exactly by four programs; it is not a
proof about any other n. The search code and the checkers were written by AI agents working in
MV2's name, and no human expert has checked the certificate yet. The 3- and 5-smooth menu
negatives are negatives for one finite menu only.

## Credit

The shifted conjecture's first counterexamples are Blanco, Criado and Santos's; local rules, the
9 -> 8 rule and n >= 95 are Daria Poliakova's; the n = 63 case and its sporadic top speed are
Xavier Callens's; the question is Yongxian Zhang's (arXiv:2608.13599, Question 8.5). The
counterexamples for 18..54 are aadrianvv's and those for 55..57 tomdif's.
