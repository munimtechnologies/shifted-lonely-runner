# Pre-registration: route 19, exact rules at one N with the slack radius

Written 2026-11-27 (about 20:05 UTC), before any code of this route had run. MV2, Munim, Inc.
Made with AI agents working in MV2's name; no human expert has checked it. Text CC BY 4.0, code
Apache-2.0.

## Where the problem stands

The shifted Lonely Runner Conjecture fails for 5 <= n <= 57 (Blanco, Criado and Santos;
aadrianvv; tomdif; Callens; Lean-checked in 1337isnot1337/solved-conjectures PR 755), for n = 63
(Xavier Callens, [Zenodo 24051700](https://doi.org/10.5281/zenodo.24051700), unrefereed) and
for n >= 95 (Poliakova, [arXiv:2609.23952](https://arxiv.org/abs/2609.23952)). **Open: 58..62
and 64..94.** Re-checked 27 November about 19:45 UTC: the Zenodo API ("shifted lonely runner":
the same four records, Bonfioli 24189338 and Callens 24132291, 24051700, 23842167; "lonely
runner", newest first: nothing new on the shifted conjecture), arXiv's newest lonely-runner
listings (newest 2610.40694, 28 October) and the solved-conjectures pull requests (newest
F1Justin's PR 1017, open; nothing claims n >= 58). A web search for any improvement of
Poliakova's linear constant (E_n >= floor(n/287)) found none.

## Why this route

Routes 15-18 searched near Callens's and Poliakova's covers and all stopped at configurations
that touch exactly, blocked by pairs of speeds summing to 2(n + 1) (RESULTS_rules_n.md). We now
read Callens's cover as a rule and see why it works.

**Callens's cover is a Poliakova-type rule at N = 64 plus a top trick.** On the base 2, 4, ...,
128 (delta = 1/65) it removes 4, 8, 32, 72, 96, 108, rephases 12, 24, 36 by (1 + delta)/2, 48
by (1 - delta)/2, 16 and 128 by -delta and 64 by +delta, and adds 1, 3, 9, 27, 81 at shifts
3/4 + (small) delta. In Poliakova's terms (her locality proof): the odd runners w and 3w at
about 3/4 cover all the times for which 4w is responsible, so 4, 12, 36 and 108 are free; 4 and
108 are removed; 36 at 1/2 covers 72 (removed); the chain 12, 24, 48 at about 1/2 covers 96
(removed) and supplies the 3q/2 helpers of the power-of-two chain 8 (removed), 16, 32
(removed), 64, 128. The last link is new: 64 at +delta leaves its times with z > 0 to 128 at
-delta, and 128 = 2N leaves its own times with z < 0 open. There are no larger speeds to close
them. They are closed by the **slack**: for t in [1/130, 1/128], speed 2 is within
delta (1 + delta) for t <= 33/4225 and speed 128 at -delta from there on, and they meet exactly
at radius 66/4225 = delta (1 + delta) < 1/64. In general the top speed 2N at -delta, with N
even, is closed by the untouched speed 2 J0 (J0 the inverse of the class mod N) at radius
delta (1 + delta); test_top_o.py checks the smallest case (N = 4) by hand.

Poliakova's rules must work for every N, so they cannot use this. A rule for one N can. A count
of Poliakova's gadgets (halving at 1/2, doubling at -delta or +delta, the 3q/2 helper, the
odd pairs w, 3w), not a proof, suggests that gain-1 rules built only from them with a single
top fit N = 64 and N >= 96 but not 65..95. So the search must allow everything at a fixed N.

## Method (`top_o.py`)

- **Exact fixed-N criterion** (`fixed_check`; statement and proof in the module docstring): for
  every touched base speed q, every class k (gcd(k, q/2) = 1) and every z in [-1, 1], some
  runner and some integer J satisfy |(x - J)(N + 1) + c z + beta| <= rho, with c = w/q,
  x = c k + s0. It counts every runner, untouched or not, and every lift J (near misses
  included), at the slack radius r = rho delta = 128/(128(n + 1) + 1) < 1/(n + 1), n = N - g.
  It is exactly a closed-cover test at r. Every rule it accepts is re-checked by both global
  exact checkers of slr.py at R = 1/(n + 1) (`certify`).
- **Search** (`cegar_o`): CP-SAT CEGAR as in route 11 (rule_search_c.build_and_solve): clauses
  per class built from every runner and lift, a candidate checked exactly, failing classes
  added. Menu: touchable speeds are the 3-smooth multiples of 4 up to 2N, and 2N itself if
  3-smooth. All other even speeds stay untouched but count as helpers. Added speeds are the
  3-smooth odd speeds up to 2N + 1. Shifts are s0 in {0, 1/6, 1/4, 1/3, 1/2, 2/3, 3/4, 5/6} plus
  beta delta with beta in eighths on [-1, 1] or halves on [-2, 2] (menu x; Callens's rule is
  in it) or halves only (menu h). INFEASIBLE is a proof for that finite menu only.
- **Tiers.** Sanity: f96h (N = 96, g = 1, menu h; Poliakova's rule is in it) and f64x (N = 64,
  g = 1, menu x; Callens's rule is in it). Calibration: h64 (N = 64, menu h: are halves
  enough?). Targets: x64g2 (N = 64, g = 2: n = 62) and xN for every N in 59..95 except 64,
  g = 1 (n = N - 1: 58..62 and 64..94), x72 and x81 first (2N = 144 and 162 are 3-smooth).
  Gate probes O1, O2, O3, 520 s each; a tier gets 45 s per turn (sanity 90-150 s), fewest turns
  first, and undecided tiers resume from their collected classes (cache %TEMP%/mv2-slr-o1).
- **Report:** a `CHK` line (cal: Callens passes at r; cal1: fails at rho = 1; cal66: passes at
  exactly 66/4225; calcert: both global checkers; pol: Poliakova at rho = 1), one token per tier
  (`tag:<F|I|U|B><iterations>/<seconds>`), then SANE, BUG, RULE and CERT lines, STATUS last.

## Sanity rules

- S1: `test_top_o.py` passes in the gate (hand values for the top trick at N = 4; menus and
  pools; Poliakova at rho = 1; Callens passes at r and fails at rho = 1, and both global
  checkers accept it; the clauses of eight classes accept Callens's rule; 60 random small rules
  agree with slr.covers_sweep in both directions).
- S2: CHK shows cal=T cal1=F cal66=T calcert=T pol=T, and no BUG token.

## Predictions

- **O-R1.** S1 and S2 hold. **Yes** (85%).
- **O-R2.** f96h is FOUND within O1-O3. **Yes** (80%).
- **O-R3.** f64x is FOUND within O1-O3 (the search rediscovers a top rule at N = 64). **Yes**
  (45%).
- **O-R4.** h64 is INFEASIBLE (halves are not enough even where a cover exists). **Yes** (55%).
- **O-R5.** At least 10 of the 37 target tiers are decided INFEASIBLE within O1-O3. **Yes**
  (40%).
- **O-R6.** Some target tier is FOUND and certified, i.e. a counterexample for an open n.
  **No** (3% yes).

## Claims policy

A FOUND target is claimed only after a scoop check on the day of publishing (Zenodo API,
solved-conjectures pull requests, arXiv, GitHub, web) and a re-check by a fresh third checker in
a committed test. INFEASIBLE is reported as "no rule in this finite menu", never as "no
counterexample for n". Credit: the n = 63 cover and its shifts are Callens's (CC BY 4.0); local
rules, their locality proof, the 9 -> 8 rule and E_n are Poliakova's; the CEGAR encoding is
route 11's; bounding extensions of a fixed cover is F1Justin's idea (PR 850, PR 1017).
