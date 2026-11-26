# Pre-registration: route 11, local rules on bases of multiples of 3, 4, 6 and 12

Written 2026-11-26, before any code of this route had run. MV2, Munim, Inc. Made with AI
agents working in MV2's name; no human expert has checked it. Text CC BY 4.0, code Apache-2.0.

## The question

The shifted Lonely Runner Conjecture is known to fail for 5 <= n <= 57 and for n >= 95.
**58 <= n <= 94 is open** (checked 2026-11-26: arXiv listing, GitHub repositories sorted by
update, solved-conjectures pull requests and issue 110). The n >= 95 result is Poliakova's
([arXiv:2609.23952](https://arxiv.org/abs/2609.23952)). It comes from a local rule on the base
of even speeds 2, 4, ..., 2N whose largest touched speed is 192. A rule of gain g >= 1 on the
base of multiples of m, with largest touched speed L and untouched helpers up to L, gives
counterexamples for every n >= ceil(L/m) - g (criterion and proof in `rules_m.py`).

For m = 2 the question has been searched hard. tomdif's `rule3.py` and `rule4.py` found no gain-1
rule at L <= 190 for primes {2, 3} or {2, 3, 5}
([search/NOTES.md](https://github.com/1337isnot1337/solved-conjectures/blob/main/results/shifted-lonely-runner-counterexamples/search/NOTES.md)).
aadrianvv's structured-patch solver proved UNSAT for N = 95, 94 and 72
([issue 110](https://github.com/1337isnot1337/solved-conjectures/issues/110)). We found no
search of bases of multiples of 3, 4, 6 or 12. There the added runners have speeds a/m in the
time scale of the base 1, 2, ..., N (thirds, quarters, sixths), so the gadgets that pay for
removed runners can be different. The scaling lemma in `rules_m.py` shows that m = 6 contains
every rule of m = 2 and m = 3 at the same threshold, and m = 12 contains m = 4 and m = 6.

## Method (`rule_search_c.py`)

- **Pools.** The touched base speeds (removed or rephased) and the added speeds (non-multiples
  of m up to 2L + 1) must be P-smooth, P = {2, 3, 5}. **Every** other multiple of m up to L
  stays as an untouched helper. Route 10 left out the non-smooth helpers, which weakened its
  negative (RESULTS_rules_s.md).
- **Menus.** A: beta in steps of 1/2 on [-2, 2], shift denominators {1, 2, 3, 4, 6}. B: beta in
  steps of 1/4, denominators {1, 2, 3, 4, 6, 8, 12}. (sigma0 is forced by the class it covers.)
- **Counterexample-guided search.** CP-SAT solves the clauses of the classes collected so far,
  minimising the number of touched speeds subject to gain >= 1. The candidate is checked by
  `rules_m.local_check(rule, untouched_upto=L)` (exact). The clauses of up to 16 failed classes
  per base speed are added, and the loop repeats. Every rule of the menu that passes the check
  satisfies all clauses, so **INFEASIBLE on the collected subset proves that the menu has no
  rule**. FOUND means that the exact check passed.
- **Certification.** For a rule with threshold T <= 94, the full configuration for every n from
  T to 94 (N = n + g) must pass both global exact checkers of `slr.py` at R = 2/(2N+1).

Tiers, in order (`ORDER`):

| tag | m | L | threshold if gain 1 | menu | role |
|---|---|---|---|---|---|
| c2chk | 2 | 192 | 95 | A, P = {2,3} | sanity: Poliakova's rule exists here |
| c3A58 | 3 | 177 | 58 | A | search |
| c6A58 | 6 | 354 | 58 | A | search |
| c4A58 | 4 | 236 | 58 | A | search |
| c2neg | 2 | 190 | 94 | A, P = {2,3} | cross-check of tomdif's rule3 negative |
| c3B58, c6B58, c4B58 | 3, 6, 4 | 177, 354, 236 | 58 | B | search |
| c3A94, c6A94, c4A94 | 3, 6, 4 | 285, 570, 380 | 94 | A | search: any rule beats n >= 95 |
| c12A58 | 12 | 708 | 58 | A with denominators of B | search |

Runs: three probes in the publish test gate (540 s each, 6 workers, shared state so later
probes resume where earlier ones stopped). Also the compete job `slr-rules-c-v1` (5 hours,
4 CPUs).

## Sanity checks (if one fails, nothing is graded)

- C1: Poliakova's rule satisfies every clause the encoder makes for its classes (m = 2, and
  scaled by 3 to m = 6). For a broken copy, the classes with a violated clause are exactly
  the classes that `local_check` fails (`test_rules_c.py`).
- C2: for 48 random rules inside the menus (m = 2, 3, 4, 6), the violated-clause classes equal
  the `local_check` failures, in both directions (`test_rules_c.py`).
- C3: the search never reports BUG (a failed class whose clauses were already present), and
  c2chk ends FOUND.

## Predictions

- **C-R1.** Some tier finds a verified rule with threshold <= 58. Prediction: **no**
  (probability about 10%).
- **C-R2.** Some tier with m in {3, 4, 6, 12} finds a verified rule with threshold <= 94, which
  would lower Poliakova's 95. Prediction: **no** (about 20%).
- **C-R3.** c2neg ends INFEASIBLE, agreeing with tomdif's rule3 negative for primes {2, 3}.
  Prediction: **yes** (about 85%). A rule there would itself be a new result (threshold 94), and
  it would be certified before any claim.
- **C-R4.** c3A58, c6A58 and c4A58 are each decided (FOUND or INFEASIBLE) within the three gate
  probes. Prediction: **yes** (about 55%).

## Claims policy

A negative covers only the finite menu named, and is stated that way. A rule is claimed only
for values of n whose full configurations pass both global checkers, and only after a scoop
search on the day of publishing. Before any article, the certificates are re-checked by a third
checker written fresh for that purpose.
