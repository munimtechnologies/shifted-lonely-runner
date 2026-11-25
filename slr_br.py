# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Best-response search for shifted Lonely Runner counterexamples (standard library only).

Shifted Lonely Runner Conjecture (sLRC): for distinct positive integer speeds v_1..v_n and any
shifts s_i, some time t has ||v_i t + s_i|| >= 1/(n+1) for every i. A counterexample is a choice
of shifts such that the closed "bad" sets

        B_i(r) = { t in R/Z : ||v_i t + s_i|| <= r }

cover the whole circle for some radius r < 1/(n+1): then max_t min_i ||v_i t + s_i|| <= r.

Known: sLRC holds for n <= 4 (Alcantara-Criado-Santos, arXiv:2506.13379); fails for 5 <= n <= 17
(Blanco-Criado-Santos, arXiv:2603.24784, speeds 1..n) and for every n >= 95 (Poliakova,
arXiv:2609.23952). Counterexamples for 18 <= n <= 94 are missing (Poliakova, last section).

This module:
  * `exact_cover` decides, in exact rational arithmetic, whether the closed bad sets cover the
    circle. It is the only thing a certificate depends on.
  * `find_cover` is a heuristic float search: best-response dynamics (each runner in turn moves
    to the shift that covers the largest measure of what the others leave uncovered; the optimum
    is found exactly among the breakpoints of a piecewise-linear function) with radius
    continuation (start at 1.25 r_target, shrink 2% after each cover) and random kicks.
    It is deterministic for a given seed. Whatever it returns is re-checked by `exact_cover`
    on the exact binary values of the float shifts.
"""
import bisect
import math
import random
import time
from fractions import Fraction as F

EPS_GAP = 1e-12


# ---------------------------------------------------------------- exact certificate check
def exact_intervals(v, s, r):
    """Closed t-intervals inside [0, 1] where ||v t + s|| <= r (v > 0 integer, s, r Fractions)."""
    out = []
    for m in range(-1, v + 3):
        a = (m - s - r) / v
        b = (m - s + r) / v
        if b < 0 or a > 1:
            continue
        out.append((a if a > 0 else F(0), b if b < 1 else F(1)))
    return out


def exact_cover(speeds, shifts, r):
    """True iff the closed bad sets of radius r cover [0, 1] (hence the circle). Exact."""
    r = F(r)
    iv = []
    for v, s in zip(speeds, shifts):
        iv.extend(exact_intervals(int(v), F(s) % 1, r))
    iv.sort()
    cur = F(0)
    for a, b in iv:
        if a > cur:
            return False
        if b > cur:
            cur = b
    return cur >= 1


def loneliness_bound(n):
    """The sLRC bound 1/(n+1)."""
    return F(1, n + 1)


# ---------------------------------------------------------------- float search
def float_intervals(v, s, r, out):
    for m in range(-1, v + 3):
        a = (m - s - r) / v
        b = (m - s + r) / v
        if b < 0.0 or a > 1.0:
            continue
        out.append((a if a > 0.0 else 0.0, b if b < 1.0 else 1.0))


def gaps_of(iv):
    """Uncovered sub-intervals of [0, 1] (longer than EPS_GAP) left by the intervals iv."""
    iv.sort()
    cur = 0.0
    g = []
    for a, b in iv:
        if a > cur + EPS_GAP:
            g.append((cur, a))
        if b > cur:
            cur = b
    if cur < 1.0 - EPS_GAP:
        g.append((cur, 1.0))
    return g


def total_gaps(speeds, shifts, r):
    iv = []
    for v, s in zip(speeds, shifts):
        float_intervals(v, s, r, iv)
    return gaps_of(iv)


def best_shift(v, gaps, r, rng):
    """Shift s for a speed-v runner maximising the measure of `gaps` inside its bad set.

    With y = v t mod 1, the runner covers t iff y lies in the window [c - r, c + r], c = -s.
    g(y) = number of preimages in `gaps` (piecewise constant); the covered measure is the
    window integral of g divided by v, a piecewise-linear function of c whose maximum is at
    a c with c - r or c + r on a breakpoint of g.
    """
    base = 0
    ev = []
    for a, b in gaps:
        A = v * a
        L = v * (b - a)
        full = math.floor(L)
        rem = L - full
        base += full
        if rem > 0.0:
            st = A - math.floor(A)
            en = st + rem
            if en <= 1.0:
                ev.append((st, 1))
                ev.append((en, -1))
            else:
                ev.append((st, 1))
                ev.append((1.0, -1))
                ev.append((0.0, 1))
                ev.append((en - 1.0, -1))
    ev.sort()
    xs = [0.0]
    gs = [0.0]
    level = base
    cx = 0.0
    for p, d in ev:
        if p > cx:
            gs.append(gs[-1] + level * (p - cx))
            xs.append(p)
            cx = p
        level += d
    if cx < 1.0:
        gs.append(gs[-1] + level * (1.0 - cx))
        xs.append(1.0)
    gtot = gs[-1]
    nseg = len(xs) - 1
    slopes = [(gs[i + 1] - gs[i]) / (xs[i + 1] - xs[i]) for i in range(nseg)]

    def G(y):
        k = math.floor(y)
        f = y - k
        i = bisect.bisect_right(xs, f) - 1
        if i >= nseg:
            i = nseg - 1
        if i < 0:
            i = 0
        return k * gtot + gs[i] + slopes[i] * (f - xs[i])

    best = -1.0
    cands = []
    for x in xs:
        for c in (x - r, x + r):
            val = G(c + r) - G(c - r)
            if val > best + 1e-15:
                best = val
                cands = [c]
            elif val >= best - 1e-15:
                cands.append(c)
    c = cands[rng.randrange(len(cands))]
    return (-c) % 1.0, best / v


def br_sweeps(speeds, shifts, r, rng, sweeps):
    """Best-response sweeps in random order. True as soon as the circle is covered."""
    n = len(speeds)
    for _ in range(sweeps):
        order = list(range(n))
        rng.shuffle(order)
        for k in order:
            iv = []
            for j in range(n):
                if j != k:
                    float_intervals(speeds[j], shifts[j], r, iv)
            g = gaps_of(iv)
            if not g:
                return True
            shifts[k], _ = best_shift(speeds[k], g, r, rng)
        if not total_gaps(speeds, shifts, r):
            return True
    return False


def find_cover(speeds, r_target, seed=1, max_sweeps=4000, seconds=None):
    """Search shifts whose bad sets of radius r_target (float) cover the circle.

    Returns (shifts or None, stats). Deterministic for a given seed (the time limit can only
    stop the search early; it never changes what is found before it).
    """
    rng = random.Random(seed)
    n = len(speeds)
    t0 = time.time()
    r = r_target * 1.25
    step = 0.02
    shifts = [rng.random() for _ in range(n)]
    good_r, good_s = None, None
    best_r = None
    used = 0
    fails = 0
    restarts = 0
    deep = 0
    while used < max_sweeps:
        if seconds is not None and time.time() - t0 > seconds:
            break
        ok = br_sweeps(speeds, shifts, r, rng, 3)
        used += 3
        if ok:
            good_r, good_s = r, shifts[:]
            if best_r is None or r < best_r:
                best_r = r
            if r <= r_target:
                return shifts, {"sweeps": used, "restarts": restarts, "best_r": r,
                                "seconds": round(time.time() - t0, 1)}
            r = max(r_target, r * (1.0 - step))
            fails = 0
            deep = 0
            continue
        fails += 1
        if fails % 4:
            for _ in range(1 + rng.randrange(2)):
                shifts[rng.randrange(n)] = rng.random()
            continue
        if good_s is not None and step > 0.002:
            step /= 2.0
            shifts = good_s[:]
            r = max(r_target, good_r * (1.0 - step))
        elif good_s is not None and deep < 8:
            # stronger kick from the last cover: re-draw three runners
            deep += 1
            shifts = good_s[:]
            for _ in range(3):
                shifts[rng.randrange(n)] = rng.random()
            r = max(r_target, good_r * (1.0 - step))
        else:
            restarts += 1
            shifts = [rng.random() for _ in range(n)]
            r = r_target * 1.25
            step = 0.02
            deep = 0
            good_r, good_s = None, None
        fails = 0
    return None, {"sweeps": used, "restarts": restarts, "best_r": best_r,
                  "seconds": round(time.time() - t0, 1)}


def certify_consecutive(n, seed=1, max_sweeps=4000, seconds=None):
    """Try to certify that speeds 1..n with suitable shifts violate the sLRC.

    Radius used for the exact check: R = 1/(n+1) - 1/10^11 (< 1/(n+1)); the float search runs at
    R - 1e-10 so that float rounding cannot open a gap at R.
    Returns (certificate dict or None, stats).
    """
    speeds = list(range(1, n + 1))
    R = loneliness_bound(n) - F(1, 10 ** 11)
    shifts, stats = find_cover(speeds, float(R) - 1e-10, seed=seed, max_sweeps=max_sweeps,
                               seconds=seconds)
    if best := stats.get("best_r"):
        stats["best_ratio"] = round(best * (n + 1), 6)
    if shifts is None:
        return None, stats
    exact = [F(s) for s in shifts]
    if not exact_cover(speeds, exact, R):
        stats["exact_check"] = False
        return None, stats
    stats["exact_check"] = True
    return {"n": n, "speeds": speeds, "radius": str(R),
            "shifts": [str(s) for s in exact], "shifts_float": [repr(s) for s in shifts]}, stats
