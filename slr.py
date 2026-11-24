# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Shifted Lonely Runner: exact certificate checkers and a heuristic shift search.

Conventions follow Blanco, Criado and Santos (arXiv:2603.24784): n moving runners with
distinct positive integer speeds v_1..v_n and starting positions (shifts) s_1..s_n;

    gamma(v; s) = sup_t min_i ||s_i + v_i t||,   gamma_sh(v) = min_s gamma(v; s),

where ||x|| is the distance from x to the nearest integer. The shifted Lonely Runner
Conjecture (sLRC) says gamma_sh(v) >= 1/(n+1) for every v with distinct entries.

Certificate. If the OPEN arcs A_i = {t in R/Z : ||v_i t + s_i|| < R} cover the circle,
then (the circle being compact and t -> min_i ||v_i t + s_i|| continuous) gamma(v; s) < R.
With R <= 1/(n+1) this is a counterexample to the sLRC for that n. Two exact checkers
are given, written independently of each other:

  covers_sweep      Fractions; sorts lifts of the arcs and sweeps [0, 1].
  covers_endpoints  integers; uses the fact that finitely many open arcs (each shorter
                    than the circle) cover the circle iff every arc endpoint lies
                    strictly inside some arc.

The search (search_cover / solve_levels) is a float heuristic. It proves nothing by
itself: every result it reports is re-checked by both exact checkers.
"""
import bisect
import math
import random
import time
from fractions import Fraction

Q_BITS = 48
Q = 1 << Q_BITS  # shifts are stored as integers P with s = P / Q


def _frac(x):
    return x if isinstance(x, Fraction) else Fraction(x)


# ---------------------------------------------------------------- exact checker A

def covers_sweep(v, s, R):
    """Exact check A. v: positive ints; s: rationals; R: rational in (0, 1/2).

    Returns (True, None) if the open arcs {t : ||v_i t + s_i|| < R} cover R/Z,
    else (False, x) with x in [0, 1] an uncovered point.
    """
    R = _frac(R)
    if not (0 < R < Fraction(1, 2)):
        raise ValueError("R must lie in (0, 1/2)")
    iv = []
    for vi, si in zip(v, s):
        si = _frac(si) % 1
        # every arc of runner i meeting [0, 1] has a lift with a in [-1, vi + 1]
        for a in range(-1, vi + 2):
            iv.append(((a - si - R) / vi, (a - si + R) / vi))
    iv.sort()
    cur = Fraction(0)  # invariant: [0, cur) is covered
    best = None
    idx = 0
    m = len(iv)
    while cur <= 1:
        while idx < m and iv[idx][0] < cur:
            if best is None or iv[idx][1] > best:
                best = iv[idx][1]
            idx += 1
        if best is None or best <= cur:
            return False, cur
        cur = best
    return True, None


# ---------------------------------------------------------------- exact checker B

def covers_endpoints(v, s, R):
    """Exact check B (integer arithmetic, endpoint criterion). Same contract as A."""
    R = _frac(R)
    if not (0 < R < Fraction(1, 2)):
        raise ValueError("R must lie in (0, 1/2)")
    s = [_frac(x) % 1 for x in s]
    D = R.denominator
    for x in s:
        D = D * x.denominator // math.gcd(D, x.denominator)
    S = [x.numerator * (D // x.denominator) for x in s]
    Rn = R.numerator * (D // R.denominator)  # R = Rn / D
    n = len(v)
    for i in range(n):
        vi = v[i]
        Di = vi * D
        lim = Rn * vi
        for a in range(vi):
            for sign in (-1, 1):
                X = a * D - S[i] + sign * Rn  # endpoint x = X / Di
                inside = False
                for j in range(n):
                    r0 = (v[j] * X + S[j] * vi) % Di  # (v_j x + s_j) * Di mod Di
                    if r0 < lim or Di - r0 < lim:  # ||v_j x + s_j|| < R
                        inside = True
                        break
                if not inside:
                    return False, Fraction(X, Di) % 1
    return True, None


def gamma_upper_ok(v, s, R):
    """True iff both exact checkers certify gamma(v; s) < R."""
    a, _ = covers_sweep(v, s, R)
    b, _ = covers_endpoints(v, s, R)
    return a and b, (a, b)


# ---------------------------------------------------------------- float search

def _norm_arcs(v, s, r):
    out = []
    w = 2.0 * r / v
    for a in range(v):
        lo = ((a - s - r) / v) % 1.0
        hi = lo + w
        if hi <= 1.0:
            out.append((lo, hi))
        else:
            out.append((lo, 1.0))
            out.append((0.0, hi - 1.0))
    return out


def _gaps(arcs):
    gaps = []
    cur = 0.0
    for lo, hi in sorted(arcs):
        if lo > cur:
            gaps.append((cur, lo))
        if hi > cur:
            cur = hi
    if cur < 1.0:
        gaps.append((cur, 1.0))
    return gaps


def _unc_measure(arcs_by_runner):
    allarcs = []
    for A in arcs_by_runner:
        allarcs.extend(A)
    return sum(b - a for a, b in _gaps(allarcs))


def _best_shift(vi, gaps, r, rng):
    """Shift for a runner of speed vi that covers the largest measure of `gaps`.

    In y = vi * t mod 1 the runner covers the window (c - r, c + r), c = -s. Returns
    (s, covered measure in y-units); the covered t-measure is that divided by vi.
    """
    base = 0
    ev = []
    for a, b in gaps:
        L = vi * (b - a)
        full = math.floor(L)
        rem = L - full
        base += full
        if rem <= 0.0:
            continue
        st = (vi * a) % 1.0
        en = st + rem
        if en <= 1.0:
            ev.append((st, 1))
            ev.append((en, -1))
        else:
            ev.append((st, 1))
            ev.append((1.0, -1))
            ev.append((0.0, 1))
            ev.append((en - 1.0, -1))
    if not ev and base == 0:
        return rng.random(), 0.0
    ev.sort()
    B = [0.0]
    M = []
    cnt = base
    for x, d in ev:
        if x > B[-1]:
            M.append(cnt)
            B.append(x)
        cnt += d
    if B[-1] < 1.0:
        M.append(cnt)
        B.append(1.0)
    cum = [0.0]
    for j in range(len(M)):
        cum.append(cum[-1] + M[j] * (B[j + 1] - B[j]))
    total = cum[-1]
    nm = len(M)

    def F(x):
        k = math.floor(x)
        f = x - k
        j = bisect.bisect_right(B, f) - 1
        if j >= nm:
            j = nm - 1
        if j < 0:
            j = 0
        return k * total + cum[j] + M[j] * (f - B[j])

    best = -1.0
    cands = []
    for b in B:
        for c in (b - r, b + r):
            val = F(c + r) - F(c - r)
            if val > best + 1e-15:
                best = val
                cands = [c]
            elif val >= best - 1e-15:
                cands.append(c)
    c = rng.choice(cands)
    return (-c) % 1.0, best


def search_cover(v, r, s0, deadline, rng, tol=1e-13):
    """Iterated local search for shifts whose open arcs of radius r cover the circle.

    Returns (shifts, uncovered measure); uncovered measure 0.0 means success (float).
    """
    n = len(v)
    s = [x % 1.0 for x in s0]
    arcs = [_norm_arcs(v[i], s[i], r) for i in range(n)]
    unc = _unc_measure(arcs)
    if unc < tol:
        return s, 0.0
    best_unc, best_s = unc, list(s)
    stall = 0
    while time.time() < deadline:
        before = unc
        order = list(range(n))
        rng.shuffle(order)
        for i in order:
            others = []
            for j in range(n):
                if j != i:
                    others.extend(arcs[j])
            g = _gaps(others)
            if not g:
                break
            gm = sum(b - a for a, b in g)
            sh, ov = _best_shift(v[i], g, r, rng)
            s[i] = sh
            arcs[i] = _norm_arcs(v[i], sh, r)
            if gm - ov / v[i] < tol:
                break
        unc = _unc_measure(arcs)
        if unc < tol:
            return s, 0.0
        if unc < best_unc * (1.0 - 1e-9):
            best_unc, best_s = unc, list(s)
            stall = 0
        elif unc > before * (1.0 - 1e-6):
            stall += 1
        if stall >= 2:
            s = list(best_s)
            k = max(1, int(round(n * rng.uniform(0.02, 0.12))))
            for i in rng.sample(range(n), k):
                s[i] = rng.random()
            arcs = [_norm_arcs(v[i], s[i], r) for i in range(n)]
            unc = _unc_measure(arcs)
            stall = 0
    return best_s, best_unc


def quantize(shifts):
    """Float shifts -> integers P (s = P / 2^48), reduced mod 2^48."""
    return [int(round(x * Q)) % Q for x in shifts]


def solve_levels(v, levels, t_first, t_level, rng, hard_deadline=None,
                 improve_cap=None, s_init=None):
    """Certify gamma(v; s) < 1/(n+1+e) for e in `levels` (increasing), warm-starting
    each level from the previous solution. Stops at the first level not reached.

    Returns a list of records, one per certified level, each verified by both exact
    checkers, plus a status string.
    """
    n = len(v)
    s = list(s_init) if s_init else [rng.random() for _ in v]
    recs = []
    t_start_improve = None
    status = "none"
    for idx, e in enumerate(levels):
        e = _frac(e)
        R = Fraction(1) / (n + 1 + e)
        r_s = float(R) * (1.0 - 1e-6)
        now = time.time()
        if idx == 0:
            dl = now + t_first
        else:
            if t_start_improve is None:
                t_start_improve = now
            dl = now + t_level
            if improve_cap is not None:
                dl = min(dl, t_start_improve + improve_cap)
        if hard_deadline is not None:
            dl = min(dl, hard_deadline)
        if dl <= now:
            break
        t0 = time.time()
        s_new, unc = search_cover(v, r_s, s, dl, rng)
        if unc != 0.0:
            status = "search-stopped" if recs else "not-found"
            break
        P = quantize(s_new)
        sq = [Fraction(p, Q) for p in P]
        ok, (a, b) = gamma_upper_ok(v, sq, R)
        rec = {"e": str(e), "R": str(R), "P": P, "checkA": a, "checkB": b,
               "seconds": round(time.time() - t0, 2)}
        if not ok:
            rec["note"] = "float search reported a cover that exact checking rejected"
            recs.append(rec)
            status = "exact-rejected"
            break
        recs.append(rec)
        status = "certified"
        s = s_new
    return recs, status
