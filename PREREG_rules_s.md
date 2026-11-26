# Pre-registration: route 10, a focused local-rule search aimed at n = 58

Written 2026-11-26, before any code of this route had run. MV2, Munim, Inc. Made with AI
agents working in MV2's name; no human expert has checked it. Text CC BY 4.0, code Apache-2.0.

## The question

The shifted Lonely Runner Conjecture is now known to fail for 5 <= n <= 57 and for n >= 95:
Blanco, Criado and Santos ([arXiv:2603.24784](https://arxiv.org/abs/2603.24784)) for 5..17,
aadrianvv for 18..54 and tomdif for 55..57
([1337isnot1337/solved-conjectures](https://github.com/1337isnot1337/solved-conjectures), PRs 243,
646 and 660, unrefereed; Lean-checked in PR 755), and Poliakova
([arXiv:2609.23952](https://arxiv.org/abs/2609.23952)) for n >= 95. **58 <= n <= 94 is open.**
Closing it would show the conjecture fails for every n >= 5, the first part of Zhang's question
([arXiv:2608.13599](https://arxiv.org/abs/2608.13599)).

Poliakova's n >= 95 comes from a single *local uniform rule* (9 -> 8: remove 3 speeds, rephase 6
and add 2 on the base 2, 4, ..., 2N) whose largest touched speed is L = 192, so its threshold is
L/2 - 1 = 95. **A rule of gain >= 1 whose threshold ceil(max(L, U)/m) - g is at most 58 would
settle every n in 58..94 at once.** Here m is the base modulus and U the largest untouched
helper speed (criterion and proof in `rules_m.py`). Routes 2 and 3 (`job_rules.py`,
`job_rules_m.py`) search for such rules, but they climb L from 16 upward over every speed. They
are likely to hit their 3,000,000-literal cap before L reaches 118, and they have not run yet.

## What route 10 does differently

`rule_search_s.py` searches only at the decisive size, L = 59 m (threshold 58 for gain 1). It
restricts the speeds to **smooth numbers**, whose prime factors lie in a small set P. Every
published rule uses only speeds with prime factors in {2, 3, 5} (Poliakova's Table 1). The
local criterion needs the covering runner and the covered runner to have a ratio with a small
denominator, so smooth pools keep the problems small enough for CP-SAT to *decide* them, not
just time out. The criterion, the encoder and the solver model are those of `rules_m.py` and
`rule_search_m.py`, with the speed pools restricted.

Tiers, in this order (`TIERS` in `rule_search_s.py`). The menus are A: beta in steps of 1/2 on
[-2, 2] and shift denominators {1, 2, 3, 4, 6}; B: beta in steps of 1/4 and denominators
{1, 2, 3, 4, 6, 8, 12}; C: beta in steps of 1/4 and denominators {1, 2, 3, 4, 5, 6, 8, 9, 10, 12}.

| tag | m | L | P | menu |
|---|---|---|---|---|
| s5A2 | 2 | 118 | {2,3,5} | A |
| s5B2 | 2 | 118 | {2,3,5} | B |
| s5A6 | 6 | 354 | {2,3,5} | A |
| s7B2 | 2 | 118 | {2,3,5,7} | B |
| s5B6 | 6 | 354 | {2,3,5} | B |
| s7A6 | 6 | 354 | {2,3,5,7} | A |
| allA2 | 2 | 118 | all | A |
| s7B6 | 6 | 354 | {2,3,5,7} | B |
| s5C12 | 12 | 708 | {2,3,5} | C |

Added speeds go up to 2L + 1. The search stops at the first rule that passes
`rules_m.local_check(rule, untouched_upto=L)` (exact, independent of the encoding). Every n from
the rule's threshold to 94 is then certified by building the full configuration
(`rules_m.build_config`, N = n + g). Both global exact checkers of `slr.py` must pass at radius
R = 2/(2N+1), which lies strictly between 1/(N+1) and 1/(n+1).

Runs: three short probes in the publish test gate (OR-Tools is installed into the gate's temp
folder by pip; if that fails, the probe says so). There is also a compete job, `slr-rules-s-v1`,
with four times the time per tier.

## Sanity checks (if any fails, nothing is graded)

- S1: Poliakova's 9 -> 8 rule satisfies every clause the encoder makes for its touched speeds in
  the 3-smooth m = 2 pool. So does its copy scaled by 3 in the 5-smooth m = 6 pool. Dropping the
  added speed 9 breaks exactly the classes (12, 1) and (12, 5) (`test_rules_s.py`).
- S2: Poliakova's rule passes the local criterion, has threshold 95, and its n = 95
  configuration passes both global checkers (`test_rules_s.py`).
- S3: any solver rule that fails `local_check` is reported as an encoding bug and discarded.
- S4: the two global checkers agree on every configuration.

## Predictions

- **R1.** At least one tier finds a verified rule with threshold <= 58. Prediction: **no**
  (probability about 30%). Poliakova's 3/2-ratio structure needs a chain 12, 24, 48, 96 under
  the top speed 192, and we see no shorter way to pay for the two added speeds.
- **R2.** The two m = 2, 5-smooth tiers (s5A2, s5B2) end with CP-SAT status INFEASIBLE. That
  would be a proof that no rule exists in those menus. Prediction: **yes**.
- **R3.** If a rule is found, every n in 58..94 is certified by both checkers. Prediction:
  **yes** (the criterion is proved; a failure would mean a bug, and no claim would be made).

## Claims policy

Only values of n whose configurations pass both global checkers are claimed, and only after a
fresh search on the day of publishing confirms that 58..94 is still open. Before any article,
every certificate is re-checked a third time by a checker written fresh for that purpose. The
certificates are exact finite computations, so they are their own independent check. "INFEASIBLE" or "not found" covers only the
finite menus above, not every possible rule.
