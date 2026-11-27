# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 19c (PREREG_rules_q.md): the exact fixed-N search of routes 19/19b in a SMALL menu.

Route 19b's gate probes P1 and P2 (2026-11-27) re-found two n = 63 covers at N = 64 from
scratch. One of them (sanity tier ph64, 4 iterations, 8 s) is much smaller than Callens's:

    remove 8, 32, 96; rephase 12, 24, 48 to 1/2 + delta/2, 16 to -3 delta/2, 64 to -delta and
    128 to +delta; add 3 and 9 at 3/4                                          (SIMPLE_63)

on the base 2, 4, ..., 128 with delta = 1/65: 11 touched speeds against Callens's 18. It is
Poliakova's 9 -> 8 rule (remove 8, 32, 192; rephase 12, 24, 48, 96 to 1/2 + delta/2 and 16, 64
to -delta; add 3, 9 at 1/4) cut off at 2N = 128: 96 is removed instead of rephased, 128 takes
the place of 192 through the top trick, 16 moves to -3 delta/2, and 3, 9 sit at 3/4 (the mirror
of 1/4). Both known gain-1 rules therefore live in a small menu: shifts s0 in quarters and
beta in halves of delta on [-2, 2]. Route 19b's targets used s0 in sixths and thirds too and
beta in eighths (menu x, about 4.7 times as many options per speed) and decided none of its
targets: the solver ran out of time on almost every iteration.

Route 19c runs the same exact CEGAR (top_p.cegar_p: top_o.fixed_check at the slack radius,
top_o.class_clauses_o, feasibility-only CP-SAT) in menu q = (s0 in {0, 1/4, 1/2, 3/4}, beta in
halves on [-2, 2]), which is a subset of menu x. So INFEASIBLE here says less than INFEASIBLE in
menu x ("no rule in menu q"), and FOUND here is FOUND in menu x too. Targets: gain 1 for every N
in 59..95 except 64 (n = N - 1), gain 2 at N = 64 (n = 62) and N = 96 (n = 94), and gain 2 with
5-smooth speeds at N = 64 and 96. Every FOUND rule is re-checked by both global exact checkers
of slr.py (top_o.certify) and by `indep_cover` below, a third exact checker written here.
"""
import json
import os
import tempfile
import time
from fractions import Fraction as F
from math import gcd

import rules_m
import rule_search_s as rs
import top_o as to
import top_p as tp

H = F(1, 2)
DENS_Q = frozenset({1, 2, 4})
KIND = "h"

# Found by route 19b's sanity tier ph64 (gate probe P1, 2026-11-27 21:28 UTC); certified there
# by both global checkers of slr.py at R = 1/64. 64 - 3 + 2 = 63 runners.
SIMPLE_63 = {
    "m": 2,
    "removed": [8, 32, 96],
    "rephased": {12: (H, H), 16: (F(0), F(-3, 2)), 24: (H, H), 48: (H, H),
                 64: (F(0), F(-1)), 128: (F(0), F(1))},
    "added": {3: (F(3, 4), F(0)), 9: (F(3, 4), F(0))},
}


def _tiers():
    """tag: (N, g, P)."""
    T = {"q64": (64, 1, to.P3), "q96": (96, 1, to.P3),          # sanity
         "q64g2": (64, 2, to.P3), "q96g2": (96, 2, to.P3),      # n = 62, n = 94
         "q64g2p5": (64, 2, to.P5), "q96g2p5": (96, 2, to.P5)}
    for N in range(59, 96):
        if N != 64:
            T["q%d" % N] = (N, 1, to.P3)                      # n = N - 1
    return T


TIERS = _tiers()
SANITY = ["q64", "q96"]
FIRST = ["q64g2", "q96g2", "q72", "q81", "q95", "q63", "q65"]
TARGETS = FIRST + ["q%d" % N for N in range(59, 96)
                   if N != 64 and "q%d" % N not in FIRST] + ["q64g2p5", "q96g2p5"]
ORDER = SANITY + TARGETS


def n_of(tag):
    N, g, _P = TIERS[tag]
    return N - g


def seed_tag(tag):
    """Route-19/19b tier with the same N and g (its classes seed this tier), or None."""
    N, g, P = TIERS[tag]
    if P != to.P3:
        return None
    if g == 1 and N != 64:
        return "x%d" % N
    if (N, g) == (64, 2):
        return "x64g2"
    return None


def seeds_for(tag, p1, o1, per_q=8):
    """Class ids (q, k) collected for the matching menu-x tier, at most per_q per speed q,
    only for speeds q touchable here. A class id is valid in any menu at the same N and g:
    its clauses are rebuilt from the current menu."""
    st = seed_tag(tag)
    if st is None:
        return []
    cl = (p1.get(st) or {}).get("classes") or (o1.get(st) or {}).get("classes") or []
    N, _g, P = TIERS[tag]
    touch = set(to.pools_o(N, P)[0])
    byq = {}
    for q, k in cl:
        if int(q) in touch:
            byq.setdefault(int(q), []).append(int(k))
    out = []
    for q in sorted(byq):
        for k in to._spread(sorted(set(byq[q])), per_q):
            out.append([q, k])
    return out


# ------------------------------------------------------------------ third exact checker

def _lcm(xs):
    out = 1
    for x in xs:
        out = out * x // gcd(out, x)
    return out


def indep_cover(v, s, R):
    """Do the open arcs {t : ||v_i t + s_i|| < R} cover R/Z? Exact, integers only.
    Criterion: if the open arcs miss a point, the uncovered set is closed, non-empty and not
    the whole circle, so it has a boundary point, and that point is an endpoint of some arc.
    Hence the arcs cover iff every arc endpoint lies inside some open arc.
    With D = lcm of all denominators, s_i = a_i/D, R = r/D, the endpoints of runner i are
    t = (j D + e - a_i)/(v_i D), e = +-r, j = 0..v_i - 1 (there v_i t + s_i = j + e/D), and
    runner l covers t iff min(Y, M - Y) < r v_i with M = v_i D, Y = (v_l num + a_l v_i) mod M.
    Returns (ok, first uncovered endpoint or None)."""
    R = F(R)
    s = [F(x) % 1 for x in s]
    D = _lcm([R.denominator] + [x.denominator for x in s])
    a = [int(x * D) for x in s]
    r = int(R * D)
    order = sorted(range(len(v)), key=lambda i: v[i])
    for i in range(len(v)):
        vi = v[i]
        M = vi * D
        lim = r * vi
        for j in range(vi):
            for e in (r, -r):
                num = j * D + e - a[i]
                hit = False
                for l in order:
                    if l == i:
                        continue
                    Y = (v[l] * num + a[l] * vi) % M
                    if Y < lim or M - Y < lim:
                        hit = True
                        break
                if not hit:
                    return False, F(num, M) % 1
    return True, None


def full_cert(rule, N, n):
    """top_o.certify (both slr.py checkers) plus indep_cover, on the padded configuration."""
    c = to.certify(rule, N, n=n)
    v = c.get("speeds")
    if v is None:
        c["indep"] = False
        c["ok"] = False
        return c
    s = [F(x) for x in c["shifts"]]
    ok3, _x = indep_cover(v, s, F(1, n + 1))
    c["indep"] = ok3
    c["ok"] = bool(c["ok"] and ok3)
    return c


# ------------------------------------------------------------------ probe

def _p1_lines(p1):
    """Final state of route 19b (cache mv2-slr-p1): counts, and in full every target it
    decided (P3's report was not seen)."""
    cnt = {}
    dec = []
    for t in tp.ORDER:
        st = p1.get(t, {})
        s = st.get("status", "-")
        cnt[s] = cnt.get(s, 0) + 1
        if t not in tp.SANITY and s in ("FOUND", "INFEASIBLE", "BUG"):
            dec.append(tp._tok(t, st))
    its = sum(p1.get(t, {}).get("it_total", 0) for t in tp.ORDER)
    sol = sum(p1.get(t, {}).get("solve_total", 0) for t in tp.ORDER)
    out = ["P1STATE " + " ".join("%s=%d" % (k, v) for k, v in sorted(cnt.items()))
           + " it=%d solve_s=%d x64g2=%s decided=%s" % (
               its, sol, tp._tok("x64g2", p1.get("x64g2")), ",".join(dec) or "-")]
    for t in tp.ORDER:
        st = p1.get(t, {})
        if t not in tp.SANITY and st.get("status") == "FOUND":
            out.append(("P1RULE %s %s" % (t, tp.short_rule(st["rule"])))[:700])
        if st.get("status") == "BUG":
            out.append(("P1BUG %s %s" % (t, " | ".join(st.get("why", []))))[:200])
    return out


def probe_q(budget=520, workers=8, cache=None, p1_cache=None, o1_cache=None, cap=40,
            cap_sanity=60):
    """Run pending tiers (fewest turns first), certify any FOUND tier with three exact
    checkers, return a short report whose last lines matter most."""
    t_end = time.time() + budget
    tmp = tempfile.gettempdir()
    cache = cache or os.path.join(tmp, "mv2-slr-q1")
    p1_cache = p1_cache or os.path.join(tmp, "mv2-slr-p1")
    o1_cache = o1_cache or os.path.join(tmp, "mv2-slr-o1")
    os.makedirs(cache, exist_ok=True)
    state_path = os.path.join(cache, "state.json")
    state = rs._load(state_path, {})
    p1 = rs._load(os.path.join(p1_cache, "state.json"), {})
    o1 = rs._load(os.path.join(o1_cache, "state.json"), {})
    head = []
    tail = []
    ok, note = rs.ensure_ortools()
    head.append("ortools=%s %s p1=%d o1=%d" % (ok, note[:30], len(p1), len(o1)))
    try:
        head.extend(_p1_lines(p1))
    except Exception as e:  # report, do not hide
        head.append("P1STATE ERROR %r" % (e,))
    while ok:
        pend = [t for t in ORDER if state.get(t, {}).get("status") not in
                ("FOUND", "INFEASIBLE", "BUG")]
        if not pend:
            break
        pend.sort(key=lambda t: (state.get(t, {}).get("turns", 0), ORDER.index(t)))
        tag = pend[0]
        N, g, P = TIERS[tag]
        left = t_end - time.time()
        if left < 25:
            break
        prev = state.get(tag, {})
        seeds = prev.get("classes")
        if seeds is None:
            seeds = seeds_for(tag, p1, o1)
        c = cap_sanity if tag in SANITY else cap
        try:
            info = tp.cegar_p(N, g, P, KIND, DENS_Q, time.time() + min(c, left - 12),
                              workers=workers, seed_classes=seeds)
        except Exception as e:
            info = {"status": "BUG", "why": [repr(e)[:160]], "iterations": 0, "seconds": 0,
                    "solve_seconds": 0, "classes": prev.get("classes", [])}
        info["turns"] = prev.get("turns", 0) + 1
        info["it_total"] = prev.get("it_total", 0) + info.get("iterations", 0)
        info["sec_total"] = prev.get("sec_total", 0) + info.get("seconds", 0)
        info["solve_total"] = prev.get("solve_total", 0) + info.get("solve_seconds", 0)
        if info["status"] == "FOUND":
            try:
                full = full_cert(rules_m.rule_from_json(info["rule"]), N, N - g)
            except Exception as e:
                full = {"ok": False, "why": repr(e)[:120]}
            info["cert"] = {k: v for k, v in full.items() if k not in ("speeds", "shifts")}
            if not full["ok"]:
                info["status"] = "BUG"
                info["why"] = ["fixed_check passed but a global check failed",
                               json.dumps(info["cert"])[:120]]
            else:
                with open(os.path.join(cache, "cert_%s.json" % tag), "w",
                          encoding="utf-8") as f:
                    json.dump({"tag": tag, "N": N, "n": N - g, "rule": info["rule"],
                               "cert": full}, f)
        state[tag] = info
        rs._save(state_path, state)
    toks = [tp._tok(t, state.get(t)) for t in ORDER]
    body = [" ".join(toks[i:i + 9]) for i in range(0, len(toks), 9)]
    its = sum(state.get(t, {}).get("it_total", 0) for t in ORDER)
    sol = sum(state.get(t, {}).get("solve_total", 0) for t in ORDER)
    body.append("QIT iterations=%d solve_s=%d per_it=%.1f" % (its, sol, sol / its if its else 0))
    for t in ORDER:
        st = state.get(t, {})
        if st.get("status") == "BUG":
            tail.append("BUG %s %s" % (t, " | ".join(st.get("why", []))[:240]))
    new = []
    for t in ORDER:
        st = state.get(t, {})
        if st.get("status") != "FOUND":
            continue
        if t in SANITY:
            tail.append(("SANE %s %s" % (t, tp.short_rule(st["rule"])))[:420])
            continue
        N, g, _P = TIERS[t]
        new.append(N - g)
        tail.append(("RULE %s N=%d n=%d %s" % (t, N, N - g, tp.short_rule(st["rule"])))[:900])
        tail.append("CERT %s %s" % (t, json.dumps(st.get("cert"))[:240]))
    cnt = {}
    for t in ORDER:
        s = state.get(t, {}).get("status", "-")
        cnt[s] = cnt.get(s, 0) + 1
    tail.append("STATUS new_n=%s %s" % (new or "-", " ".join(
        "%s=%d" % (k, v) for k, v in sorted(cnt.items()))))
    return "\n".join(head + body + tail)
