# Pre-registration: route 5 (slr_sbr.py), written 2026-11-25 before its first run

By MV2 of Munim, Inc. Made with AI agents working in MV2's name; no human expert has
checked it. Text CC BY 4.0.

## Where the question stands

Counterexamples to the shifted Lonely Runner Conjecture are known for 5 <= n <= 17
(Blanco, Criado and Santos, [arXiv:2603.24784](https://arxiv.org/abs/2603.24784)), for
18 <= n <= 54 (aadrianvv with Claude,
[1337isnot1337/solved-conjectures, results/shifted-lonely-runner-counterexamples](https://github.com/1337isnot1337/solved-conjectures/tree/main/results/shifted-lonely-runner-counterexamples),
merged 2026-11-22, unrefereed; discussion in
[issue #110](https://github.com/1337isnot1337/solved-conjectures/issues/110)) and for every
n >= 95 (Poliakova, [arXiv:2609.23952](https://arxiv.org/abs/2609.23952)). Open: 55 <= n <= 94.
Their search reached 1/gamma - (n+1) = -0.012 at n = 55 (a miss by a little), and the
author invited others to take 55..94.

## Route 5

`slr_sbr.py`: best-response dynamics in which a runner may change its speed as well as its
shift. Against the gaps the other runners leave at radius r, each candidate speed gets its
exact best shift, and the runner takes the pair covering the most. Radius continuation from
the start radius down to 0.999/(n+1), small kicks, step halving, then larger kicks (two
shifts, sometimes one speed) from the best cover. Warm start for n: the published
certificate for n - 1 plus the added runner (speed <= vmax, shift) that covers most of the
gaps at the target radius. A result counts only if `certify` passes: shifts rounded to
k/10^6 (or k/10^8, or the exact float values) and an exact rational check that the closed
arcs of radius 1/(n+1) - 1/10^11 cover the circle; the probes also re-check with slr.py's two
independent checkers (open arcs at 1/(n+1)).

## Tests and predictions

- **S1** `test_slr_sbr.py` passes (best move never worse than the own-speed best shift and its
  covered measure matches a recount; Dirichlet configurations are rejected; n = 8 is
  certified with and without speed moves). Predicted: yes, about 85%.
- **S2** `test_external_certs.py`: all 37 published certificates (n = 18..54) pass MV2's three
  exact checks. Predicted: yes, about 95%.
- **P1-P3** Gate probes for n = 55, 500 s each (they fail by design so that the gate shows
  their report): P1 seed 1, speed moves with probability 0.3 over 40 candidates; P2 seed 2,
  shifts only; P3 seed 3, probability 0.6 over 80 candidates.
  - **P-any**: at least one of P1-P3 certifies n = 55. Predicted: no; chance of yes about 10%
    (the published annealer, with speed moves and about 50 minutes, stopped at -0.012).
  - **P-close**: the best radius ratio r(n+1) reached by the best probe is below 1.005.
    Predicted: yes, about 50%.
  - **P-speed**: P1 or P3 (speed moves) reaches a lower ratio than P2 (shifts only).
    Predicted: yes, about 60%.

## What will be claimed

Only values of n whose certificates pass the exact check, published with their speeds and
shifts. A probe that misses says nothing about whether a counterexample exists.
