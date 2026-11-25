# Pre-registration: job slr-rules-m-v1 (written 2026-11-25, before it runs)

By MV2 of Munim, Inc. Made with AI agents working in MV2's name; no human expert has
checked it. Text CC BY 4.0.

## Question

Poliakova (arXiv:2609.23952) disproves the shifted Lonely Runner Conjecture (sLRC) for every
n >= 95 with one local rule on the base 2, 4, ..., 2N; Blanco, Criado and Santos
(arXiv:2603.24784) cover 5 <= n <= 17. Job slr-rules-v1 (PREREG_rules.md, still queued)
searches for smaller rules of exactly her kind (base of even speeds, added odd speeds).

This job asks the same question on a **base of multiples of m**: m, 2m, ..., Nm. In the time
scale of the base 1, ..., N, Poliakova's added runners have half-integer speeds; with m = 6
they may also have speeds in thirds, with m = 4 quarters, with m = 12 both. `rules_m.py`
states and proves the criterion: a rule of modulus m with gain g >= 1 that touches base
speeds up to L (and uses untouched base speeds up to L as helpers) is a counterexample for
every n >= L/m - g. By the scaling remark proved there, the modulus-6 search contains every
modulus-2 and modulus-3 rule with the same threshold, and modulus 12 contains moduli 4 and 6.

**Is there a gain-1 rule with rho = L/m <= 19?** It would give counterexamples for every
n >= 18 and, with the earlier results, show that the sLRC fails for every n >= 5 (the first
part of Zhang's Question 9.4, arXiv:2608.13599). Poliakova's rule has rho = 96.

## Method

- `rules_m.py`: criterion with proof, Poliakova's rule (modulus 2), a hand-made modulus-4
  example, scaling, full-configuration builder.
- `rule_search_m.py`: the CP-SAT encoding of rule_search.py for modulus m: base speeds
  m..L, added speeds 1..L+1 not divisible by m; sigma0 forced by the class it covers with
  denominator in a menu; beta in a menu; gain >= 1; objective 64*gain - touched speeds.
- `job_rules_m.py`: plan (rho, m) = (19, 6), (19, 4), (19, 12), (24, 6), (24, 4), (32, 6),
  (32, 4), in this order; for each, menu A (beta in steps of 1/2 in [-2, 2]; sigma0
  denominators 1, 2, 3, 4, 6; 600 s) then menu B (steps of 1/4; denominators up to 12;
  900 s). Problems above 3,000,000 clause literals are skipped and reported "too-big". It
  stops at the first solver rule that passes `rules_m.local_check(untouched_upto=L)`, then
  builds the full configuration for every n from the rule's threshold to 94 and checks each
  with BOTH global exact checkers of `slr.py` at radius R = 2/(2N+1), which lies strictly
  between 1/(N+1) and 1/(n+1).

## Sanity checks (if any fails, nothing below is graded)

- **S0** Poliakova's rule passes `local_check` at modulus 2 and rescaled to moduli 4 and 6;
  the hand-made modulus-4 example passes and its broken version fails.
- **S0b** Encoding completeness: the modulus-6 Poliakova rule satisfies every clause the
  encoder builds for its touched speeds 24, 36, 48, in menus A and B.
- **S1** Every solver rule is re-checked by `local_check`; a solver rule that fails it is an
  encoding bug, is reported, and is not used.
- **S2** The two global checkers agree on every certificate.

## Predictions

- **P1m** A verified gain >= 1 rule with rho <= 19 is found (closes 18..94 by itself).
  Predicted: **no** (we put it near 30%; a hand analysis of rules built only from
  "half-lap" and "tilt" rephasings suggests the 3/2-ratio structure of Poliakova's rule is
  hard to compress).
- **P2m** A verified gain >= 1 rule with rho <= 32 is found (would shrink the gap to
  18 <= n < 32 - g). Predicted: **no** (near 40%).
- **P3m** Every certificate in the rule's range passes both global checkers. Predicted:
  **yes** (it follows from the theorem in `rules_m.py`; a failure means a bug in proof or
  code, and then no rule-based claim is made).

## What will be claimed

Only n with a certificate that passes both global checkers. "Not found" for some (rho, m)
is a statement about this finite menu and time limit, not a proof that no rule exists.
Whatever this job and slr-rules-v1 leave open in 18..94 stays with the direct search
slr-gap-v1 (PREREG.md).
