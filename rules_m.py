# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Local rules for the shifted Lonely Runner problem on a base of multiples of m.

This generalises rules.py (which is the case m = 2, Poliakova arXiv:2609.23952, Sec. 3-4).

Base configuration: the N runners with speeds m, 2m, ..., Nm and zero shifts. For every
time t, Dirichlet's theorem applied to m*t gives some j <= N with ||j m t|| <= 1/(N+1), so the
base is a closed delta-cover with delta = 1/(N+1).

A rule (with modulus m) removes some base speeds (R), gives some base speeds a new shift
sigma0 + beta*delta (S), and adds speeds a that are NOT multiples of m with shift
sigma0 + beta*delta (A). X = R u S, L = max X, gain g = |R| - |A|. In the time scale of the
base 1, 2, ..., N the added runners have the rational speeds a/m; m = 2 allows halves only,
m = 4 quarters, m = 6 halves and thirds, and so on.

Local criterion (`local_check`). Suppose that for every q in X, every integer k in [0, q)
with gcd(k, q/m) = 1, and every z in [-1, 1], some runner of the edited configuration with
speed w covers the point t = (k + delta z)/q in the exact sense

        c = w/q,   c*k + sigma0 is an integer,   |c z + beta| <= 1,

where the covering runner is rephased, added, or (if `untouched_upto` = U is given) an
untouched base runner w <= U, w a multiple of m, with sigma0 = beta = 0.

Claim. Then for every N with m*N >= max(L, U), the edited configuration is a closed
delta-cover, delta = 1/(N+1), with N - g runners; so for n = N - g its loneliness is at most
1/(n + 1 + g), and for g >= 1 it is a counterexample to the shifted Lonely Runner Conjecture
for n runners. The rule therefore covers every n >= max(L, U)/m - g.

Proof. Fix t. Let q = m j be the smallest base speed with ||q t|| <= delta. If q is not in X
it is present and covers t. Otherwise let k be the integer nearest to q t and
z = (q t - k)/delta, |z| <= 1. If d = gcd(k, j) > 1, the base speed q/d = m (j/d) < q has
||(q/d) t|| = ||k/d + delta z/d|| <= delta/d <= delta, contradicting the choice of q; so
gcd(k, q/m) = 1 (replacing k by k mod q only changes t by an integer). For the covering runner
of the hypothesis, w t + sigma0 + beta delta = (c k + sigma0) + delta (c z + beta), whose
distance to the nearest integer is at most delta |c z + beta| <= delta. Every rephased or
untouched covering speed is <= max(L, U) <= m N, so it is present; added speeds are not
multiples of m, so all speeds of the edited configuration are distinct. QED.

Scaling. Multiplying m, every speed of X and every added speed by a positive integer u (shifts
unchanged) gives a rule with modulus u m that passes the criterion iff the original does: c is
unchanged, c k + sigma0 mod 1 depends only on k mod q (adding q to k adds w to c k), and
gcd(k, uq/(um)) = gcd(k mod q, q/m). Its threshold max(L, U)/m - g is unchanged too. So a
search over modulus 6 contains, in particular, every rule of modulus 2 and 3 at the same
threshold (and modulus 12 contains moduli 4 and 6).

Everything here is exact (Fractions). `build_config` writes out the full configuration so
that the global checkers in slr.py can re-verify it independently of this criterion.
"""
from fractions import Fraction as F
from math import gcd


def responsible_classes(q, m):
    """k in [0, q) with gcd(k, q/m) = 1 (q a positive multiple of m)."""
    if q <= 0 or q % m:
        raise ValueError("q must be a positive multiple of m")
    j = q // m
    return [k for k in range(q) if gcd(k, j) == 1]


def _norm_rule(rule):
    m = int(rule.get("m", 2))
    removed = sorted(int(w) for w in rule.get("removed", []))
    reph = {int(w): (F(s0) % 1, F(b)) for w, (s0, b) in rule.get("rephased", {}).items()}
    added = {int(a): (F(s0) % 1, F(b)) for a, (s0, b) in rule.get("added", {}).items()}
    return m, removed, reph, added


def shape_problems(rule):
    m, removed, reph, added = _norm_rule(rule)
    probs = []
    if m < 1:
        probs.append("modulus m must be a positive integer")
        return probs
    if len(set(removed)) != len(removed):
        probs.append("duplicate removed speed")
    if not removed and not reph:
        probs.append("rule touches no base speed")
    for w in removed + list(reph):
        if w <= 0 or w % m:
            probs.append("X speed %d is not a positive multiple of m = %d" % (w, m))
    for a in added:
        if a <= 0 or a % m == 0:
            probs.append("added speed %d is not a positive non-multiple of m = %d" % (a, m))
    if set(removed) & set(reph):
        probs.append("a speed is both removed and rephased")
    for w, (s0, b) in reph.items():
        if s0 == 0 and b == 0:
            probs.append("rephase of %d is the identity" % w)
    return probs


def modulus(rule):
    return _norm_rule(rule)[0]


def gain(rule):
    _, removed, _, added = _norm_rule(rule)
    return len(removed) - len(added)


def largest(rule):
    _, removed, reph, _ = _norm_rule(rule)
    return max(removed + list(reph))


def threshold(rule, untouched_upto=None):
    """Smallest n covered by the claim: ceil(max(L, U)/m) - g."""
    m = modulus(rule)
    need = max(largest(rule), untouched_upto or 0)
    return -(-need // m) - gain(rule)


def covering_runners(rule, untouched_upto=None):
    """(speed, sigma0, beta) of every runner allowed to cover in the local criterion."""
    m, removed, reph, added = _norm_rule(rule)
    out = [(w, s0, b) for w, (s0, b) in reph.items()]
    out += [(a, s0, b) for a, (s0, b) in added.items()]
    if untouched_upto:
        X = set(removed) | set(reph)
        out += [(w, F(0), F(0)) for w in range(m, untouched_upto + 1, m) if w not in X]
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
    i, n = 0, len(iv)
    best = None
    while i < n and iv[i][0] <= lo:
        if best is None or iv[i][1] > best:
            best = iv[i][1]
        i += 1
    if best is None or best < lo:
        return False, lo
    cur = best
    while cur < hi:
        best = cur
        while i < n and iv[i][0] <= cur:
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
    m, removed, reph, _ = _norm_rule(rule)
    runners = covering_runners(rule, untouched_upto)
    fails = []
    for q in sorted(set(removed) | set(reph)):
        for k in responsible_classes(q, m):
            ok, z = closed_cover(intervals(q, k, runners))
            if not ok:
                fails.append((q, k, z))
    return not fails, fails


def build_config(rule, N):
    """Full configuration for base size N. Returns (speeds, shifts, delta, n)."""
    m, removed, reph, added = _norm_rule(rule)
    delta = F(1, N + 1)
    if max(removed + list(reph)) > m * N:
        raise ValueError("N too small for this rule")
    rem = set(removed)
    v, s = [], []
    for w in range(m, m * N + 1, m):
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


def scale(rule, u):
    """The rule with modulus u*m, every speed multiplied by u, shifts unchanged."""
    m, removed, reph, added = _norm_rule(rule)
    return {"m": u * m,
            "removed": [u * w for w in removed],
            "rephased": {u * w: sb for w, sb in reph.items()},
            "added": {u * a: sb for a, sb in added.items()}}


def rule_to_json(rule):
    m, removed, reph, added = _norm_rule(rule)
    return {"m": m, "removed": removed,
            "rephased": {str(w): [str(s0), str(b)] for w, (s0, b) in sorted(reph.items())},
            "added": {str(a): [str(s0), str(b)] for a, (s0, b) in sorted(added.items())}}


def rule_from_json(d):
    return {"m": int(d.get("m", 2)),
            "removed": [int(w) for w in d["removed"]],
            "rephased": {int(w): (F(s0), F(b)) for w, (s0, b) in d["rephased"].items()},
            "added": {int(a): (F(s0), F(b)) for a, (s0, b) in d["added"].items()}}


H = F(1, 2)
Q4 = F(1, 4)

# Poliakova, arXiv:2609.23952, Sec. 4: the 9 -> 8 local rule (modulus 2, gain 1, L = 192).
POLIAKOVA_9_8 = {
    "m": 2,
    "removed": [8, 32, 192],
    "rephased": {12: (H, H), 24: (H, H), 48: (H, H), 96: (H, H), 16: (0, -1), 64: (0, -1)},
    "added": {3: (Q4, 0), 9: (Q4, 0)},
}

# A modulus-4 example worked by hand (gain -1, so not a counterexample; it tests the
# arithmetic of moduli above 2). Base 4, 8, ...; remove 8; add 2 and 6 at shift 3/4.
# Classes of q = 8 (gcd(k, 2) = 1): k = 1, 3, 5, 7. Runner 2: c = 1/4, k/4 + 3/4 is an
# integer for k = 1, 5, interval [-4, 4]. Runner 6: c = 3/4, 3k/4 + 3/4 is an integer for
# k = 3, 7, interval [-4/3, 4/3]. So every class is covered on all of [-1, 1].
TOY_M4 = {
    "m": 4,
    "removed": [8],
    "rephased": {},
    "added": {2: (F(3, 4), 0), 6: (F(3, 4), 0)},
}
