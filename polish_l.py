# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 17 (PREREG_rules_l.md): exact margins for near-covers, and one added runner.

Route 16 (descent_k.py) drove every target tier to an uncovered measure near 1e-9 at the shrunk
radius R (1 - 1e-7), with 10 to 50 tiny gaps, and stopped there. A measure that small says the
configuration is close to TOUCHING (arcs meeting end to end); it does not say whether the shifts
can be re-tuned so that every touching pair overlaps. This module answers that exactly for a
fixed combinatorial type.

Chain. Arcs are lifted to the real line: runner i, lift k covers the open interval
((k - s_i - R) / v_i, (k - s_i + R) / v_i). A cyclic chain I_1, ..., I_m, I_{m+1} = I_1 + 1 in
which every consecutive pair of open intervals intersects covers the circle (the union of the
chain is connected and contains a whole period). With x_i = s_i / v_i, both overlaps of a pair
(A, B) are affine in x with unit coefficients:

    end_A - start_B = c1 - x_A + x_B,   c1 = (k_A + R) / v_A - (k_B - R) / v_B,
    end_B - start_A = c2 - x_B + x_A,   c2 = (k_B + R) / v_B - (k_A - R) / v_A.

Requiring both to be >= eps is a system of difference constraints (edges B -> A of weight
c1 - eps and A -> B of weight c2 - eps over runner nodes). It is feasible iff no cycle has
negative weight, so the LARGEST margin eps any choice of shifts gives this chain is exactly the
minimum cycle mean lambda of the graph with weights c (Karp's algorithm, done here in exact
integer arithmetic). lambda > 0: shifts with margin lambda / 2 exist; they are computed
(Bellman-Ford), rounded, and re-checked by both exact checkers of slr.py. lambda <= 0: no shifts
make this chain a cover; the critical cycle names the runners that block it.

One added runner (exact and complete for fixed shifts). For a fixed configuration whose open
arcs leave closed gaps [a_g, b_g], a new runner of speed w and shift s covers gap g iff
s mod 1 lies in the open arc of centre -w (a_g + b_g) / 2 and half-width h_g = R - w (b_g - a_g)/2.
So w works iff every h_g > 0 and these arcs share a point; w >= 2R / max_g(b_g - a_g) never works.
add_one_exact decides every w below that bound with Fractions (a float pre-filter with widened
arcs only skips speeds that cannot work).

Nothing here proves a negative about the conjecture: lambda <= 0 rules out one chain only, and
add_one_exact speaks only about the given fixed shifts.
"""
import math
import multiprocessing
import os
import random
import tempfile
import time
from fractions import Fraction as F

import descent_j as dj
import descent_k as dk
import rule_search_s as rs
import slr

TIERS_L = ["cC63", "kC62", "kC61", "kC64", "kP94"]  # route 16's tiers, same meaning
# Route 15's sanity tier sC63 certified (both exact checkers) Callens's speeds with these shift
# moves, in steps of 1/520, applied to the transcription dj.c63(): speed -> move.
C63_MOVES = {104: -1, 120: -1, 1: 4, 81: 1}
SLICE_L = 40.0  # seconds of route-16 search between two polishes
WIDEN = 1e-12   # float pre-filter widening of every arc (never hides a working speed)


def c63_certified():
    """(speeds, Fraction shifts) of the n = 63 cover route 15 certified at radius 1/64."""
    v, S, D = dj.c63()
    return list(v), [F((a + C63_MOVES.get(w, 0)) % D, D) for w, a in zip(v, S)]


# ---------------------------------------------------------------- exact gaps, one added runner

def exact_gaps(v, s, R):
    """Closed uncovered set of the open arcs {t : ||v_i t + s_i|| < R} as a list of Fraction
    pairs (a, b), a <= b (a == b is an isolated uncovered point), inside the period
    [t0, t0 + 1) where t0 = -s_0 / v_0 is the centre of an arc (so covered)."""
    R = F(R)
    s = [F(x) % 1 for x in s]
    t0 = -s[0] / v[0]
    iv = []
    for vi, si in zip(v, s):
        kmin = math.floor(vi * t0 + si - R) - 1
        kmax = math.ceil(vi * (t0 + 1) + si + R) + 1
        for k in range(kmin, kmax + 1):
            a = (k - si - R) / vi
            b = (k - si + R) / vi
            if b > t0 - 1 and a < t0 + 2:
                iv.append((a, b))
    iv.sort()
    m = len(iv)
    gaps = []
    cur = t0
    idx = 0
    end = t0 + 1
    while True:
        while idx < m and iv[idx][0] < cur:
            if iv[idx][1] > cur:
                cur = iv[idx][1]
            idx += 1
        if cur >= end:
            break
        if idx >= m:
            gaps.append((cur, end))
            break
        a = iv[idx][0]
        gaps.append((cur, a))
        cur = a
        while idx < m and iv[idx][0] == cur:
            if iv[idx][1] > cur:
                cur = iv[idx][1]
            idx += 1
    return gaps


def _arcs_for(w, gaps, R):
    """Exact (l, length) of the open shift arc of each gap for speed w, or None if some gap
    is too long (h_g <= 0)."""
    out = []
    for a, b in gaps:
        h = R - w * (b - a) / 2
        if h <= 0:
            return None
        c = -w * (a + b) / 2
        out.append(((c - h) % 1, 2 * h))
    return out


def _float_max_count(w, gf, Rf):
    """Largest number of gaps one shift of speed w can cover (floats, arcs widened by WIDEN,
    so it never under-counts)."""
    base = 0
    ev = []
    for a, b in gf:
        h = Rf - w * (b - a) / 2.0
        if h <= -WIDEN:
            continue
        L = 2.0 * h + 2.0 * WIDEN
        l = (-w * (a + b) / 2.0 - h - WIDEN) % 1.0
        if l + L > 1.0:
            base += 1
            ev.append((l + L - 1.0, -1))
            ev.append((l, 1))
        else:
            ev.append((l, 1))
            ev.append((l + L, -1))
    ev.sort()
    best = cnt = base
    for _x, d in ev:
        cnt += d
        if cnt > best:
            best = cnt
    return best


def _exact_point(arcs):
    """A Fraction in every open arc (l, l + L) mod 1, or None if they share no point."""
    G = len(arcs)
    base = 0
    ev = []
    for l, L in arcs:
        e = l + L
        if e > 1:
            base += 1
            ev.append((e - 1, -1))
            ev.append((l, 1))
        else:
            ev.append((l, 1))
            ev.append((e, -1))
    ev.sort()
    xs = sorted(set(x for x, _d in ev))
    pos = {x: j for j, x in enumerate(xs)}
    delta = [0] * len(xs)
    for x, d in ev:
        delta[pos[x]] += d
    if base == G:
        # every arc wraps, so every start l > 0 and every end e - 1 > 0: (0, xs[0]) is shared
        return xs[0] / 2
    cnt = base
    for j, x in enumerate(xs):
        cnt += delta[j]
        if cnt == G:
            nxt = xs[j + 1] if j + 1 < len(xs) else xs[0] + 1
            return ((x + nxt) / 2) % 1
    return None


def add_one_exact(v, s, R, wcap=4096, deadline=None, focus=(256,)):
    """Decide exactly, for every speed w not in v below the bound 2R / (longest gap), whether
    one runner of speed w can be added to (v, s) so that the open arcs of radius R cover."""
    R = F(R)
    s = [F(x) % 1 for x in s]
    gaps = exact_gaps(v, s, R)
    G = len(gaps)
    out = {"G": G, "feasible": [], "tight": [], "top": [], "focus": {}}
    if G == 0:
        out["covered"] = True
        return out
    lens = [b - a for a, b in gaps]
    Lmax = max(lens)
    out.update(meas=float(sum(lens)), Lmax=float(Lmax), npts=sum(1 for x in lens if x == 0))
    W = (math.ceil(2 * R / Lmax) - 1) if Lmax > 0 else wcap
    out["W"] = W
    have = set(v)
    gf = [(float(a), float(b)) for a, b in gaps]
    Rf = float(R)
    top = []
    done = 0
    for w in range(1, min(W, wcap) + 1):
        if deadline is not None and time.time() > deadline:
            break
        done = w
        if w in have:
            continue
        cnt = _float_max_count(w, gf, Rf)
        top.append((cnt, w))
        if cnt >= G:
            arcs = _arcs_for(w, gaps, R)
            x = _exact_point(arcs) if arcs is not None else None
            if x is None:
                out["tight"].append(w)
                continue
            vv, ss = list(v) + [w], list(s) + [x]
            a, _ = slr.covers_sweep(vv, ss, R)
            b, _ = slr.covers_endpoints(vv, ss, R) if a else (False, None)
            out["feasible"].append({"w": w, "s": str(x), "sweep": a, "endpoints": b})
    for w in focus:
        if w in have:
            continue
        arcs = _arcs_for(w, gaps, R)
        hmin = min(R - w * L / 2 for L in lens)
        out["focus"][w] = {"cnt": _float_max_count(w, gf, Rf), "hmin": float(hmin),
                           "exact": (_exact_point(arcs) is not None) if arcs else False}
    top.sort(reverse=True)
    out["top"] = top[:5]
    out["done"] = done
    out["complete"] = bool(Lmax > 0 and done >= W)
    return out


# ---------------------------------------------------------------- chain and exact margin

def chain_of(v, s, R, tol=1e-6):
    """Greedy cyclic chain [(runner, lift), ...] of arcs covering one period at radius R,
    preferring arcs that overlap the covered part and allowing gaps up to tol otherwise.
    Returns (chain, None) or (None, reason)."""
    Rf = float(R)
    arcs = []
    for i, (vi, si) in enumerate(zip(v, s)):
        si = float(si) % 1.0
        for k in range(-vi - 1, 3 * vi + 2):
            a = (k - si - Rf) / vi
            b = (k - si + Rf) / vi
            if b > -1.0 and a < 2.5:
                arcs.append((a, b, i, k))
    arcs.sort()
    first = None
    for a, b, i, k in arcs:
        if a <= 0.0 < b and (first is None or b > first[1]):
            first = (a, b, i, k)
    if first is None:
        return None, "nothing covers 0"
    t0, cur = first[0], first[1]
    i1, k1 = first[2], first[3]
    close = (i1, k1 + v[i1])
    chain = [(i1, k1)]
    m = len(arcs)
    p1 = p2 = 0
    b1 = b2 = None
    for _guard in range(m + 2):
        while p1 < m and arcs[p1][0] < cur:
            if b1 is None or arcs[p1][1] > b1[1]:
                b1 = arcs[p1]
            p1 += 1
        while p2 < m and arcs[p2][0] <= cur + tol:
            if b2 is None or arcs[p2][1] > b2[1]:
                b2 = arcs[p2]
            p2 += 1
        if b1 is not None and b1[1] > cur:
            nxt = b1
        elif b2 is not None and b2[1] > cur:
            nxt = b2
        else:
            return None, "gap at %.6g" % cur
        if (nxt[2], nxt[3]) == close:
            return chain, None
        chain.append((nxt[2], nxt[3]))
        cur = nxt[1]
        if cur > t0 + 1:
            return chain, None
    return None, "no closure"


def _lcm(a, b):
    return a * b // math.gcd(a, b)


def chain_edges(v, chain, R):
    """Exact difference-constraint graph of a chain: {(u, w): c} meaning x_w <= x_u + c - eps."""
    R = F(R)
    i1, k1 = chain[0]
    seq = list(chain) + [(i1, k1 + v[i1])]
    edges = {}

    def add(u, w, c):
        if (u, w) not in edges or c < edges[(u, w)]:
            edges[(u, w)] = c

    for (ia, ka), (ib, kb) in zip(seq, seq[1:]):
        va, vb = v[ia], v[ib]
        c1 = (ka + R) / va - (kb - R) / vb
        c2 = (kb + R) / vb - (ka - R) / va
        add(ib, ia, c1)
        add(ia, ib, c2)
    return edges


def karp(nodes, edges):
    """Exact minimum cycle mean of a digraph whose nodes all have an incoming edge.
    edges: {(u, w): Fraction}. Returns (lam, cycle nodes, cycle mean), lam a Fraction."""
    L = 1
    for c in edges.values():
        L = _lcm(L, F(c).denominator)
    idx = {u: j for j, u in enumerate(nodes)}
    N = len(nodes)
    inc = [[] for _ in range(N)]
    for (u, w), c in edges.items():
        c = F(c)
        inc[idx[w]].append((idx[u], c.numerator * (L // c.denominator)))
    D = [[0] * N]
    P = [[-1] * N]
    for _k in range(1, N + 1):
        prev = D[-1]
        row = [None] * N
        pr = [-1] * N
        for w in range(N):
            best = None
            bu = -1
            for u, c in inc[w]:
                pu = prev[u]
                if pu is None:
                    continue
                val = pu + c
                if best is None or val < best:
                    best, bu = val, u
            row[w] = best
            pr[w] = bu
        D.append(row)
        P.append(pr)
    lam = None  # as (p, q), q > 0, value p / (q L)
    arg = -1
    for w in range(N):
        if D[N][w] is None:
            continue
        mx = None
        for k in range(N):
            if D[k][w] is None:
                continue
            p, q = D[N][w] - D[k][w], N - k
            if mx is None or p * mx[1] > mx[0] * q:
                mx = (p, q)
        if mx is not None and (lam is None or mx[0] * lam[1] < lam[0] * mx[1]):
            lam, arg = mx, w
    if lam is None:
        return None, [], None
    walk = [arg]
    cur = arg
    for k in range(N, 0, -1):
        cur = P[k][cur]
        walk.append(cur)
    seen = {}
    cyc, cmean = [], None
    for t, u in enumerate(walk):
        if u in seen:
            i = seen[u]
            cyc = walk[i:t]
            tot = F(0)
            for j in range(i, t):
                tot += F(edges[(nodes[walk[j + 1]], nodes[walk[j]])])
            cmean = tot / (t - i)
            break
        seen[u] = t
    return F(lam[0], lam[1] * L), [nodes[j] for j in cyc], cmean


def potentials(nodes, edges, eps):
    """Float Bellman-Ford: x with x_w <= x_u + c - eps on every edge (if feasible)."""
    E = [(u, w, float(F(c) - eps)) for (u, w), c in edges.items()]
    x = {u: 0.0 for u in nodes}
    for _ in range(len(nodes) + 2):
        changed = False
        for u, w, c in E:
            val = x[u] + c
            if val < x[w] - 1e-18:
                x[w] = val
                changed = True
        if not changed:
            break
    return x


def polish(v, s, R, tol=1e-6):
    """Exact largest margin lambda of the greedy chain of (v, s) at radius R; if lambda > 0,
    shifts with margin lambda / 2, rounded and re-checked by both exact checkers."""
    R = F(R)
    chain, why = chain_of(v, s, R, tol)
    if chain is None:
        return {"lam": None, "why": why, "cover": False}
    edges = chain_edges(v, chain, R)
    nodes = sorted(set(i for i, _k in chain))
    lam, cyc, cmean = karp(nodes, edges)
    out = {"lam": lam, "chain": len(chain), "nodes": len(nodes), "cover": False,
           "cyc": sorted(v[i] for i in set(cyc)), "cmean": cmean}
    if lam is None:
        return out
    eps = lam / 2 if lam > 0 else lam - F(1, 10 ** 13)
    x = potentials(nodes, edges, eps)
    s_new = [float(t) % 1.0 for t in s]
    for i in nodes:
        s_new[i] = (v[i] * x[i]) % 1.0
    out["s_new"] = s_new
    if lam > 0:
        D, S = dk.compact_k(v, s_new, R)
        if D is not None:
            sf = [F(a, D) for a in S]
            out["cover"] = bool(slr.covers_endpoints(v, sf, R)[0])
            out["D"] = D
    return out


def lam_txt(lam):
    if lam is None:
        return "none"
    if lam == 0:
        return "0"
    return "%+.3g" % float(lam)


# ---------------------------------------------------------------- probe

A_SOURCES = ("C64", "R64")  # certified neighbour of Callens's cover; the raw transcription


def a_source(name):
    if name == "C64":
        return c63_certified()
    v, S, D = dj.c63()
    return list(v), [F(a, D) for a in S]


def _worker_a(cache, deadline):
    try:
        for name in A_SOURCES:
            path = os.path.join(cache, "a_%s.json" % name)
            if rs._load(path, {}).get("complete"):
                continue
            v, s = a_source(name)
            res = add_one_exact(v, s, F(1, 65), deadline=deadline)
            res["seconds_left"] = round(deadline - time.time(), 1)
            res["name"] = name
            rs._save(path, res)
    except Exception as e:
        import traceback
        with open(os.path.join(cache, "err_A.txt"), "w", encoding="utf-8") as f:
            f.write("%r\n%s" % (e, traceback.format_exc()[-500:]))


def run_tier_l(tag, deadline, rng, prev=None, seed=None):
    """Polish, then route-16 search from the polished shifts, in turns until the deadline."""
    st = dict(prev or {})
    if st.get("status") in ("FOUND", "BUG"):
        return st
    src, n, _mode = dk.TIERS_K[tag]
    R = F(1, n + 1)
    if st.get("v"):
        v, s = list(st["v"]), list(st["s"])
    elif seed and seed.get("v"):
        v, s = list(seed["v"]), list(seed["s"])
        st["seed"] = "k16"
    else:
        v, s, _start = dk.init_tier(tag, rng)
        st["seed"] = "init"
    st.update(tag=tag, n=n)
    pool_max = 2 * max(dk.source(src)[0])
    t0 = time.time()
    while time.time() < deadline - 8:
        pol = polish(v, s, R)
        st["polishes"] = st.get("polishes", 0) + 1
        lam = pol.get("lam")
        if "lam0" not in st:
            st["lam0"] = lam_txt(lam)
            st["chain0"] = pol.get("chain")
            st["cyc0"] = pol.get("cyc")
        if lam is not None:
            st["lam_last"] = lam_txt(lam)
            if st.get("lam_best_f") is None or float(lam) > st["lam_best_f"]:
                st["lam_best_f"] = float(lam)
                st["lam_best"] = lam_txt(lam)
                st["cyc"] = (pol.get("cyc") or [])[:12]
                st["chain"] = pol.get("chain")
        else:
            st["why"] = pol.get("why")
        if pol.get("cover"):
            cert = dk.certify_k(v, pol["s_new"], n)
            st.update(cert=cert, v=list(v), s=list(pol["s_new"]),
                      status="FOUND" if cert.get("ok") else "BUG")
            break
        if pol.get("s_new") is not None:
            s = list(pol["s_new"])
        if time.time() > deadline - 8:
            break
        res = dk.search_k(v, s, R, min(deadline - 8, time.time() + SLICE_L), rng, pool_max)
        st["slices"] = st.get("slices", 0) + 1
        for key in ("sweeps", "swaps", "kicks", "rejected"):
            st[key] = st.get(key, 0) + res[key]
        if res["status"] == "COVER":
            cert = dk.certify_k(res["v"], res["s"], n)
            st.update(cert=cert, v=list(res["v"]), s=list(res["s"]),
                      status="FOUND" if cert.get("ok") else "BUG")
            break
        v, s = list(res["v"]), list(res["s"])
        st["unc"] = res["best_unc"]
    st.setdefault("status", "UNKNOWN")
    if st["status"] == "UNKNOWN":
        st["v"], st["s"] = list(v), list(s)
    st["seconds"] = round(st.get("seconds", 0.0) + time.time() - t0, 1)
    st["turns"] = st.get("turns", 0) + 1
    return st


def _worker_l(tag, deadline, cache, kcache, seed):
    path = os.path.join(cache, "l_%s.json" % tag)
    try:
        prev = rs._load(path, {})
        kseed = rs._load(os.path.join(kcache, "k_%s.json" % tag), {})
        st = run_tier_l(tag, deadline, random.Random(seed), prev, kseed)
        rs._save(path, st)
        if st.get("status") == "FOUND":
            rs._save(os.path.join(cache, "cert_%s.json" % tag), st["cert"])
    except Exception as e:
        import traceback
        with open(os.path.join(cache, "err_%s.txt" % tag), "w", encoding="utf-8") as f:
            f.write("%r\n%s" % (e, traceback.format_exc()[-500:]))


def calibrate(cache):
    """Callens's own cover at 1/64 (must give lambda > 0 and a re-checked cover) and route 16's
    kC64 start (Callens's cover plus its best added runner, every shift free) at 1/65."""
    path = os.path.join(cache, "cal.json")
    old = rs._load(path, {})
    if old.get("done"):
        return old
    v0, S0, D0 = dj.c63()
    raw = slr.covers_sweep(v0, [F(a, D0) for a in S0], F(1, 64))[0]
    v, s = c63_certified()
    p = polish(v, s, F(1, 64))
    out = {"c63raw_covers": raw, "c63_lam": lam_txt(p.get("lam")), "c63_cover": p.get("cover"),
           "c63_chain": p.get("chain")}
    if p.get("cover"):
        c = dk.certify_k(v, p["s_new"], 63)
        out["c63_cert"] = bool(c.get("ok"))
    v2, s2, st = dk.init_up("C", 64, random.Random(1))
    q = polish(v2, s2, F(1, 65))
    out.update(up_w=st.get("add"), up_m0=st.get("m0"), up_lam=lam_txt(q.get("lam")),
               up_cover=q.get("cover"), up_chain=q.get("chain"), up_cyc=(q.get("cyc") or [])[:12],
               up_why=q.get("why"))
    if q.get("cover"):
        c = dk.certify_k(v2, q["s_new"], 64)
        out["up_cert"] = c
    out["done"] = True
    rs._save(path, out)
    return out


def a_line(a):
    if not a:
        return "A none"
    name = a.get("name", "C64")
    if a.get("covered"):
        return "A %s covered-without-adding" % name
    f = a.get("focus", {}).get("256") or a.get("focus", {}).get(256) or {}
    return ("A %s G=%s pts=%s meas=%.3g Lmax=%.3g W=%s done=%s complete=%s feas=%s tight=%s "
            "top=%s w256=%s/%s h=%.3g ex=%s" % (
                name, a.get("G"), a.get("npts"), a.get("meas", 0.0), a.get("Lmax", 0.0), a.get("W"),
                a.get("done"), a.get("complete"),
                ",".join("%s:s=%s:%s%s" % (d["w"], d["s"], d["sweep"], d["endpoints"])
                         for d in a.get("feasible", [])[:3])
                or "-", ",".join(str(w) for w in a.get("tight", [])[:8]) or "-",
                ",".join("%s:%s" % (w, c) for c, w in a.get("top", [])), f.get("cnt"),
                a.get("G"), f.get("hmin", 0.0), f.get("exact")))


def line_l(tag, st):
    return ("%s n=%s st=%s seed=%s lam0=%s ch0=%s lam=%s last=%s ch=%s cyc=%s pol=%s sl=%s "
            "unc=%.3g sw=%s swp=%s t=%ss tu=%s%s" % (
                tag, st.get("n"), st.get("status"), st.get("seed"), st.get("lam0"),
                st.get("chain0"), st.get("lam_best"), st.get("lam_last"), st.get("chain"),
                ",".join(str(x) for x in st.get("cyc") or []), st.get("polishes"),
                st.get("slices"), st.get("unc") or 0.0, st.get("sweeps"), st.get("swaps"),
                int(st.get("seconds") or 0), st.get("turns"),
                (" why=" + st["why"]) if st.get("why") and not st.get("lam_best") else ""))


def r16_line(kcache):
    out = []
    for tag in TIERS_L:
        st = rs._load(os.path.join(kcache, "k_%s.json" % tag), {})
        if st:
            out.append("%s=%s/%.3g/%s/tu%s" % (tag, (st.get("status") or "?")[:3],
                                               st.get("best_unc") or 0.0,
                                               "%.3g" % ((st.get("start") or {}).get("m0") or 0.0),
                                               st.get("turns")))
    return "R16 " + (" ".join(out) if out else "none")


def probe_l(budget=520, cache=None, kcache=None):
    t_end = time.time() + budget
    cache = cache or os.path.join(tempfile.gettempdir(), "mv2-slr-l1")
    kcache = kcache or os.path.join(tempfile.gettempdir(), "mv2-slr-k1")
    os.makedirs(cache, exist_ok=True)
    lines = []
    ctx = multiprocessing.get_context("spawn")
    procs = []
    if not all(rs._load(os.path.join(cache, "a_%s.json" % nm), {}).get("complete")
               for nm in A_SOURCES) and not os.path.exists(os.path.join(cache, "err_A.txt")):
        p = ctx.Process(target=_worker_a, args=(cache, t_end - 40))
        p.start()
        procs.append(("A", p))
    seed0 = int(time.time() * 1000) % (1 << 30)
    for idx, tag in enumerate(TIERS_L):
        st = rs._load(os.path.join(cache, "l_%s.json" % tag), {})
        if st.get("status") in ("FOUND", "BUG"):
            continue
        if os.path.exists(os.path.join(cache, "err_%s.txt" % tag)):
            continue
        p = ctx.Process(target=_worker_l, args=(tag, t_end - 40, cache, kcache,
                                                seed0 + 7919 * idx))
        p.start()
        procs.append((tag, p))
    try:
        cal = calibrate(cache)
    except Exception as e:
        cal = {"err": repr(e)[:150]}
    for tag, p in procs:
        p.join(max(0.5, t_end - 5 - time.time()))
        if p.is_alive():
            p.terminate()
            lines.append("killed %s" % tag)
    lines.append("procs=%d" % len(procs))
    for tag in ["A"] + TIERS_L:
        ep = os.path.join(cache, "err_%s.txt" % tag)
        if os.path.exists(ep):
            with open(ep, encoding="utf-8") as f:
                lines.append("ERROR %s %s" % (tag, f.read()[-200:].replace("\n", " | ")))
    lines.append(r16_line(kcache))
    lines.append("CAL " + " ".join("%s=%s" % (k, cal[k]) for k in sorted(cal)
                                   if k not in ("done", "up_cert")))
    if cal.get("up_cert"):
        c = cal["up_cert"]
        lines.append("RULE up64 n=%s ok=%s D=%s v=%s S=%s" % (
            c.get("n"), c.get("ok"), c.get("D"), ",".join(str(x) for x in c.get("v0") or []),
            ",".join(str(x) for x in c.get("S") or [])))
    states = {t: rs._load(os.path.join(cache, "l_%s.json" % t), {}) for t in TIERS_L}
    for tag in TIERS_L:
        if states[tag]:
            lines.append(line_l(tag, states[tag]))
    aa = {nm: rs._load(os.path.join(cache, "a_%s.json" % nm), {}) for nm in A_SOURCES}
    for nm in A_SOURCES:
        lines.append(a_line(aa[nm]) if aa[nm] else "A %s none" % nm)
    for tag in TIERS_L:
        if states[tag].get("status") in ("FOUND", "BUG"):
            lines.append(dk.rule_line(tag, states[tag]))
    lines.append("STATUS " + " ".join("%s=%s" % (t, states[t].get("status"))
                                      for t in TIERS_L if states[t]) +
                 "".join(" %s=%s" % (nm, "FEAS" if aa[nm].get("feasible") else
                                     ("NONE" if aa[nm].get("complete") else "PART"))
                         for nm in A_SOURCES))
    return "\n".join(lines)


def job_main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--minutes", type=float, default=120)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    rep = probe_l(budget=60.0 * a.minutes, cache=os.path.join(a.out_dir, "cache"),
                  kcache=os.path.join(a.out_dir, "kcache"))
    with open(os.path.join(a.out_dir, "report_l.txt"), "w", encoding="utf-8") as f:
        f.write(rep + "\n")
    print(rep)
    return rep


if __name__ == "__main__":
    job_main()
