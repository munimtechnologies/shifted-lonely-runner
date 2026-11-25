# Pre-registration: job slr-rules-v1 (written 2026-11-25, before it runs)

By MV2 of Munim, Inc. Made with AI agents working in MV2's name; no human expert has
checked it. Text CC BY 4.0.

## Question

Poliakova (arXiv:2609.23952) disproves the shifted Lonely Runner Conjecture (sLRC) for
every n >= 95 with one "9 -> 8" local rule: start from the even speeds 2, 4, ..., 2N (a
closed cover at radius 1/(N+1)), remove 3 speeds, rephase 6 and add 2 odd speeds so that
N - 1 runners still cover. The rule touches speeds up to L = 192, so it needs N >= 96, i.e.
n >= L/2 - 1 = 95. Blanco, Criado and Santos (arXiv:2603.24784) cover 5 <= n <= 17. The gap
is 18 <= n <= 94.

**Is there a gain-1 rule with a much smaller largest speed L?** A rule with L <= 38 would
settle every n in 18..94 at once, and with the earlier results show the sLRC fails for
every n >= 5 (Zhang, arXiv:2608.13599, Question 9.4, first part). Any L < 192 shrinks the
gap to 18 <= n < L/2 - g.

## Method (code in this repository)

- `rules.py` states and proves an exact local criterion (a mild extension of Poliakova's
  locality: untouched even speeds <= L may also cover). If a rule passes `local_check`, then
  for every N >= L/2 the edited configuration is a closed cover at radius 1/(N+1) with
  N - g runners, so for n = N - g its loneliness is <= 1/(n+1+g) < 1/(n+1) when g >= 1.
- `rule_search.py` encodes the criterion for all even speeds <= L and odd speeds <= 2L+1
  over a finite menu of shifts (sigma0 with small denominator, tilt beta in steps of 1/2 or
  1/4 within [-2, 2]) as a CP-SAT problem with gain >= 1, maximising gain.
- `job_rules.py` tries L = 16, 20, 24, 28, 32, 36, 38, 40, 44, 48, 56, 64, 80, 96, 128 in
  order, menus A (halves; sigma0 denominators 1, 2, 3, 4, 6; 300 s) and B (quarters;
  denominators up to 12; 600 s), and stops at the first rule that passes `local_check`.
  It then builds the full configuration for every n from L/2 - g to 94 and re-checks each
  with BOTH global exact checkers of `slr.py` at radius R = 2/(2N+1), which lies strictly
  between 1/(N+1) and 1/(n+1).

## Sanity checks (if any fails, nothing below is graded)

- **S0** Poliakova's 9 -> 8 rule and its Table 1 variant pass `local_check` with no help from
  untouched runners.
- **S0b** Encoding completeness: the 9 -> 8 rule satisfies every clause the encoder builds
  for its touched speeds, in menus A and B.
- **S1** Every rule the solver returns is re-checked by `local_check`; a solver rule that
  fails it is an encoding bug, is reported, and is not used.
- **S2** The two global checkers agree on every certificate.

## Predictions

- **P1** A verified gain >= 1 rule with L <= 96 is found (at most half of 192). Predicted: yes.
- **P2** A verified rule with L <= 38 is found, closing 18..94 by itself. Predicted: no.
- **P3** Every certificate in the rule's range passes both global checkers. Predicted: yes
  (it follows from the theorem in `rules.py`; a failure means a bug in proof or code, and
  then no rule-based claim is made).

## What will be claimed

Only n with a certificate that passes both global checkers. A "not found" at some L is a
statement about this finite menu and time limit, not a proof that no rule exists. If n
remain in 18..94, they are left to the direct search `slr-gap-v1` (PREREG.md) or a later
version of this job.
