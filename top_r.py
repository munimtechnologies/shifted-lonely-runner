# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 19d (PREREG_rules_r.md): menu q with 5-smooth speeds, and a clause-soundness check.

Route 19c (top_q.py, RESULTS_rules_q.md) decided 38 of its 40 targets in menu q (s0 in quarters,
beta in halves of delta on [-2, 2], 3-smooth speeds): every one INFEASIBLE. Within that menu there
is no gain-1 rule at any N in 59..95 except 64, and no gain-2 rule at N = 64 or N = 96. Its sanity
tiers re-found gain-1 rules at N = 64 (n = 63) and N = 96 (n = 95) from scratch. Both known gain-1
constructions are 3-smooth; the next natural family lets 5 in: touchable speeds become the
5-smooth multiples of 4 up to 2N (20, 40, 60, 80, 100, 120, 160, 180, ...), added speeds the odd
5-smooth ones (5, 15, 25, 45, 75, 125, 135, ...), and the top trick becomes available at the
N with 2N 5-smooth: 60, 75, 80, 90 (besides 64, 72, 81, 96).

Route 19d runs the same exact CEGAR (top_p.cegar_p) in menu q with P = (2, 3, 5): gain 1 at every
N in 59..95 except 64, and gain 2 at N = 64 and 96 (route 19c's two undecided tiers, resumed from
their collected classes). Every FOUND rule is re-checked by three global exact checkers
(top_q.full_cert).

It also adds an independent check of the clause generator that every INFEASIBLE rests on:
`violations(rule, N, g, P)` rebuilds every clause of every class of every speed the rule touches
and lists the clauses the rule falsifies. A rule that passes the exact closed-cover test
`top_o.fixed_check` must falsify none (the clauses are necessary conditions); test_top_r.py checks
this on four certified covers (SIMPLE_63, Poliakova's 9 -> 8 rule, and route 19c's two sanity
rules RULE_Q64, RULE_Q96), and checks that two failing rules do falsify some clause.
"""
import os
import tempfile
import time
import json

import rules_m
import rule_search_s as rs
import top_o as to
import top_p as tp
import top_q as tq

from fractions import Fraction as F

H = F(1, 2)
Q4 = F(1, 4)
Q34 = F(3, 4)
KIND = tq.KIND
DENS_Q = tq.DENS_Q

# Route 19c's sanity tiers (gate probe Q1, 2026-11-27 23:06 UTC), FOUND from scratch and accepted
# there by all three global exact checkers. Written out from the SANE lines of RESULTS_rules_q.md.
# N = 64: 5 removed, 4 added, gain 1, 64 - 1 = 63 runners.
RULE_Q64 = {
    "m": 2,
    "removed": [4, 8, 32, 36, 96],
    "rephased": {12: (H, H), 16: (F(0), F(-1)), 24: (H, H), 48: (H, -H), 64: (F(0), F(1)),
                 128: (F(0), F(-1))},
    "added": {1: (Q4, -H), 3: (Q4, F(0)), 9: (Q4, F(0)), 27: (Q4, F(0))},
}
# N = 96: 4 removed, 3 added, gain 1, 96 - 1 = 95 runners.
RULE_Q96 = {
    "m": 2,
    "removed": [8, 32, 144, 192],
    "rephased": {12: (H, -H), 16: (F(0), F(1)), 24: (H, -H), 36: (H, -H), 48: (H, -H),
                 64: (F(0), F(1)), 72: (H, F(0)), 96: (H, -H)},
    "added": {3: (Q34, -H), 9: (Q34, F(0)), 27: (Q34, F(0))},
}


# ------------------------------------------------------------------ clause-soundness check

def present_keys(rule, N, P):
    """Clause keys that the rule makes true (keys as in top_o.class_clauses_o)."""
    _m, removed, reph, added = rules_m._norm_rule(rule)
    touch, _fixed, _add = to.pools_o(N, P)
    rem = set(removed)
    keys = set()
    for w in touch:
        if w in rem:
            continue
        if w in reph:
            s0, b = reph[w]
            keys.add(("e", w, s0, b))
        else:
            keys.add(("u", w))
    for a, (s0, b) in added.items():
        keys.add(("o", a, s0, b))
    return keys


def violations(rule, N, g, P, qs=None):
    """Every (q, k, clause) of a touched speed q that the rule falsifies, with the clauses built
    exactly as the CEGAR builds them (menu q, slack radius of N and g). A clause of class (q, k)
    is 'some key in it is true, or q is untouched'; the rule touches q, so it needs a true key."""
    _m, removed, reph, _added = rules_m._norm_rule(rule)
    rho = to.rho_of(N, g)
    touch, fixed, add_pool = to.pools_o(N, P)
    s0s = to.s0_menu(DENS_Q)
    betas = to.betas_of(KIND)
    pres = present_keys(rule, N, P)
    out = []
    for q in sorted(set(removed) | set(reph)):
        if qs is not None and q not in qs:
            continue
        for k in rules_m.responsible_classes(q, 2):
            for keys in to.class_clauses_o(q, k, N, rho, touch, fixed, add_pool, s0s, betas):
                if not any(tuple(key) in pres for key in keys):
                    out.append((q, k, keys))
    return out


# ------------------------------------------------------------------ tiers

def _tiers():
    """tag: (N, g, P)."""
    T = {"r64": (64, 1, to.P5),                       # sanity, from scratch
         "r64g2": (64, 2, to.P5), "r96g2": (96, 2, to.P5)}
    for N in range(59, 96):
        if N != 64:
            T["r%d" % N] = (N, 1, to.P5)              # n = N - 1
    return T


TIERS = _tiers()
SANITY = ["r64"]
TOP5 = [60, 75, 80, 90, 72, 81]   # 2N is 5-smooth: the top trick is available
FIRST = ["r64g2", "r96g2"] + ["r%d" % N for N in TOP5]
TARGETS = FIRST + ["r%d" % N for N in range(59, 96) if N != 64 and N not in TOP5]
ORDER = SANITY + TARGETS
CAPS = {"r64": 120, "r64g2": 150, "r96g2": 150}
CAP = 60


def n_of(tag):
    N, g, _P = TIERS[tag]
    return N - g


def seed_sources(tag):
    """Route-19c tiers (cache mv2-slr-q1) whose collected classes seed this tier."""
    if tag in SANITY:
        return []
    N, g, _P = TIERS[tag]
    if g == 2:
        return ["q%dg2p5" % N, "q%dg2" % N]
    return ["q%d" % N]


def seeds_for(tag, q1):
    """Class ids (q, k) from route 19c for the same N and g, deduplicated, only for speeds q
    touchable here. A class id is valid in any menu at the same N and g (its clauses are
    rebuilt from the current menu), so a seeded INFEASIBLE means the same as an unseeded one."""
    N, _g, P = TIERS[tag]
    touch = set(to.pools_o(N, P)[0])
    out = []
    seen = set()
    for src in seed_sources(tag):
        for q, k in (q1.get(src) or {}).get("classes") or []:
            key = (int(q), int(k))
            if key[0] in touch and key not in seen:
                seen.add(key)
                out.append([key[0], key[1]])
    return sorted(out)


# ------------------------------------------------------------------ probe

def q1_lines(q1):
    """Route 19c's final cache state: counts, solver seconds per iteration, the tokens of the
    tiers whose reports were cut off, and any BUG (sanity rule S2 of PREREG_rules_q.md)."""
    cnt = {}
    for t in tq.ORDER:
        s = q1.get(t, {}).get("status", "-")
        cnt[s] = cnt.get(s, 0) + 1
    its = sum(q1.get(t, {}).get("it_total", 0) for t in tq.ORDER)
    sol = sum(q1.get(t, {}).get("solve_total", 0) for t in tq.ORDER)
    out = ["QSTATE " + " ".join("%s=%d" % (k, v) for k, v in sorted(cnt.items()))
           + " QIT it=%d solve_s=%d per_it=%.1f" % (its, sol, sol / its if its else 0)]
    show = tq.SANITY + tq.FIRST + ["q64g2p5", "q96g2p5"]
    out.append("QTOK " + " ".join(tp._tok(t, q1.get(t)) for t in show))
    bugs = [t for t in tq.ORDER if q1.get(t, {}).get("status") == "BUG"]
    out.append("QBUG " + (",".join(bugs) if bugs else "none"))
    for t in tq.TARGETS:
        if q1.get(t, {}).get("status") == "FOUND":
            out.append(("QRULE %s %s" % (t, tp.short_rule(q1[t]["rule"])))[:700])
    return out


def probe_r(budget=520, workers=8, cache=None, q1_cache=None):
    """Run pending tiers (fewest turns first), certify any FOUND tier with three exact
    checkers, return a short report whose last lines matter most."""
    t_end = time.time() + budget
    tmp = tempfile.gettempdir()
    cache = cache or os.path.join(tmp, "mv2-slr-r1")
    q1_cache = q1_cache or os.path.join(tmp, "mv2-slr-q1")
    os.makedirs(cache, exist_ok=True)
    state_path = os.path.join(cache, "state.json")
    state = rs._load(state_path, {})
    q1 = rs._load(os.path.join(q1_cache, "state.json"), {})
    head = []
    tail = []
    ok, note = rs.ensure_ortools()
    head.append("ortools=%s %s q1=%d" % (ok, note[:30], len(q1)))
    try:
        head.extend(q1_lines(q1))
    except Exception as e:  # report, do not hide
        head.append("QSTATE ERROR %r" % (e,))
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
            seeds = seeds_for(tag, q1)
        c = CAPS.get(tag, CAP)
        try:
            info = tp.cegar_p(N, g, P, KIND, DENS_Q, time.time() + min(c, left - 12),
                              workers=workers, seed_classes=seeds)
        except Exception as e:
            info = {"status": "BUG", "why": [repr(e)[:160]], "iterations": 0, "seconds": 0,
                    "solve_seconds": 0, "classes": prev.get("classes", seeds or [])}
        info["turns"] = prev.get("turns", 0) + 1
        info["it_total"] = prev.get("it_total", 0) + info.get("iterations", 0)
        info["sec_total"] = prev.get("sec_total", 0) + info.get("seconds", 0)
        info["solve_total"] = prev.get("solve_total", 0) + info.get("solve_seconds", 0)
        if info["status"] == "FOUND":
            try:
                full = tq.full_cert(rules_m.rule_from_json(info["rule"]), N, N - g)
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
    body.append("RIT iterations=%d solve_s=%d per_it=%.1f" % (its, sol, sol / its if its else 0))
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
