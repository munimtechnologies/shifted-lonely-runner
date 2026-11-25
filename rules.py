# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Local rules for the shifted Lonely Runner problem, after Poliakova (arXiv:2609.23952).

Base configuration (Poliakova, Sec. 3): the N runners with even speeds 2, 4, ..., 2N and
zero shifts. By Dirichlet's theorem they form a closed delta-cover with delta = 1/(N+1):
for every time t some runner has ||2j t|| <= delta.

A rule is a finite edit of the base: remove some even speeds (R), give some even speeds
a new shift sigma0 + beta*delta (S), and add odd speeds a with shift sigma0 + beta*delta
(A). X = R u S. The gain is g = |R| - |A|.

Local criterion (this file, `local_check`). Let L = max X. Suppose that for every q in X,
every integer k in [0, q) with gcd(k, q/2) = 1, and every z in [-1, 1], some runner of the
edited configuration with speed w <= max(L, largest added speed) covers the point
t = (k + delta z)/q in the following exact sense: with c = w/q and shift sigma0 + beta*delta,

        c*k + sigma0 is an integer   and   |c z + beta| <= 1.

Covering runners may be rephased or added runners, and (if `untouched_upto` is given)
untouched base runners w <= untouched_upto with sigma0 = beta = 0.

Claim. Then for every N with 2N >= max(L, untouched_upto or 0), the edited configuration is
a closed delta-cover with delta = 1/(N+1) using N - g runners, so for n = N - g its
loneliness is <= 1/(n + 1 + g). If g >= 1 this is a counterexample to the shifted Lonely
Runner Conjecture for n runners.

Proof. Fix t. Let q be the smallest base speed with ||q t|| <= delta (it exists because the
base is a delta-cover). If q is not in X it is still present and covers t. Otherwise pick
the integer k with |q t - k| <= delta and put z = (q t - k)/delta, |z| <= 1. If
g = gcd(k, q/2) > 1, the even base speed q/g < q has ||(q/g) t|| = ||k/g + delta z/g||
<= delta, contradicting the choice of q; so gcd(k, q/2) = 1 (k is taken mod q, which does
not change t mod 1). For the covering runner of the hypothesis,
w t + sigma0 + beta delta = (c k + sigma0) + delta (c z + beta), whose distance to the
nearest integer is <= delta |c z + beta| <= delta. All edited speeds are distinct (evens
and odds) and every rephased or untouched covering speed is <= 2N, so it is present. QED.

Everything here is exact (Fractions). `build_config` writes out the full configuration for
a given N so that the global checkers in slr.py can re-verify it independently.
"""
from fractions import Fraction as F
from math import gcd


def responsible_classes(q):
    """k in [0, q) with gcd(k, q/2) = 1 (q even)."""
    h = q // 2
    return [k for k in range(q) if gcd(k, h) == 1]


def _norm_rule(rule):
    removed = sorted(int(w) for w in rule.get("removed", []))
    reph = {int(w): (F(s0) % 1, F(b)) for w, (s0, b) in rule.get("rephased", {}).items()}
    added = {int(a): (F(s0) % 1, F(b)) for a, (s0, b) in rule.get("added", {}).items()}
    return removed, reph, added


def shape_problems(rule):
    removed, reph, added = _norm_rule(rule)
    probs = []
    if len(set(removed)) != len(removed):
        probs.append("duplicate removed speed")
    for w in removed + list(reph):
        if w <= 0 or w % 2:
            probs.append("X speed %d is not a positive even integer" % w)
    for a in added:
        if a <= 0 or a % 2 == 0:
            probs.append("added speed %d is not a positive odd integer" % a)
    if set(removed) & set(reph):
        probs.append("a speed is both removed and rephased")
    for w, (s0, b) in reph.items():
        if s0 == 0 and b == 0:
            probs.append("rephase of %d is the identity" % w)
    return probs


def gain(rule):
    removed, _, added = _norm_rule(rule)
    return len(removed) - len(added)


def largest(rule):
    removed, reph, _ = _norm_rule(rule)
    return max(removed + list(reph))


def covering_runners(rule, untouched_upto=None):
    """(speed, sigma0, beta) of every runner allowed to cover in the local criterion."""
    removed, reph, added = _norm_rule(rule)
    out = [(w, s0, b) for w, (s0, b) in reph.items()]
    out += [(a, s0, b) for a, (s0, b) in added.items()]
    if untouched_upto:
        X = set(removed) | set(reph)
        out += [(w, F(0), F(0)) for w in range(2, untouched_upto + 1, 2) if w not in X]
    return out


def intervals(q, k, runners):
    """Closed z-intervals [(-1-b)/c, (1-b)/c] of the runners matching class k of q."""
    iv = []
    for w, s0, b in runners:
        c = F(w, q)
        if (c * k + s0).denominator == 1:
            iv.append(((-1 - b) / c, (1 - b) / c, w))
    return iv


def closed_cover(iv, lo=F(-1), hi=F(1)):
    """Do the closed intervals cover [lo, hi]? Returns (ok, first uncovered point or None)."""
    iv = sorted((a, b) for a, b, *_ in iv)
    i, m = 0, len(iv)
    best = None
    while i < m and iv[i][0] <= lo:
        if best is None or iv[i][1] > best:
            best = iv[i][1]
        i += 1
    if best is None or best < lo:
        return False, lo
    cur = best
    while cur < hi:
        best = cur
        while i < m and iv[i][0] <= cur:
            if iv[i][1] > best:
                best = iv[i][1]
            i += 1
        if best == cur:
            return False, cur  # points just above cur are uncovered
        cur = best
    return True, None


def local_check(rule, untouched_upto=None):
    """Exact local criterion. Returns (ok, failures) with failures [(q, k, z), ...]."""
    probs = shape_problems(rule)
    if probs:
        return False, probs
    removed, reph, _ = _norm_rule(rule)
    runners = covering_runners(rule, untouched_upto)
    fails = []
    for q in sorted(set(removed) | set(reph)):
        for k in responsible_classes(q):
            ok, z = closed_cover(intervals(q, k, runners))
            if not ok:
                fails.append((q, k, z))
    return not fails, fails


def build_config(rule, N):
    """Full configuration for base size N. Returns (speeds, shifts, delta, n)."""
    removed, reph, added = _norm_rule(rule)
    delta = F(1, N + 1)
    if max(removed + list(reph)) > 2 * N:
        raise ValueError("N too small for this rule")
    rem = set(removed)
    v, s = [], []
    for w in range(2, 2 * N + 1, 2):
        if w in rem:
            continue
        v.append(w)
        if w in reph:
            s0, b = reph[w]
            s.append((s0 + b * delta) % 1)
        else:
            s.append(F(0))
    for a in sorted(added):
        s0, b = added[a]
        v.append(a)
        s.append((s0 + b * delta) % 1)
    return v, s, delta, len(v)


def rule_to_json(rule):
    removed, reph, added = _norm_rule(rule)
    return {"removed": removed,
            "rephased": {str(w): [str(s0), str(b)] for w, (s0, b) in sorted(reph.items())},
            "added": {str(a): [str(s0), str(b)] for a, (s0, b) in sorted(added.items())}}


def rule_from_json(d):
    return {"removed": [int(w) for w in d["removed"]],
            "rephased": {int(w): (F(s0), F(b)) for w, (s0, b) in d["rephased"].items()},
            "added": {int(a): (F(s0), F(b)) for a, (s0, b) in d["added"].items()}}


H = F(1, 2)
Q4 = F(1, 4)

# Poliakova, arXiv:2609.23952, Sec. 4: the 9 -> 8 local rule (gain 1, L = 192).
# Shifts (1+delta)/2 -> (1/2, 1/2); -delta -> (0, -1); 1/4 -> (1/4, 0).
POLIAKOVA_9_8 = {
    "removed": [8, 32, 192],
    "rephased": {12: (H, H), 24: (H, H), 48: (H, H), 96: (H, H), 16: (0, -1), 64: (0, -1)},
    "added": {3: (Q4, 0), 9: (Q4, 0)},
}

# Poliakova, Table 1: the 9 -> 8 variant. (1-delta)/2 -> (1/2, -1/2); delta -> (0, 1).
POLIAKOVA_9_8_VARIANT = {
    "removed": [8, 32, 192],
    "rephased": {12: (H, H), 24: (H, H), 48: (H, -H), 96: (H, -H), 16: (0, -1), 64: (0, 1)},
    "added": {3: (Q4, 0), 9: (Q4, 0)},
}
