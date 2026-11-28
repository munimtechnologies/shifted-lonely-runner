# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 19e (PREREG_rules_t.md): the exact fixed-N rule search of routes 19c/19d in menu q with
7-smooth speeds, P = (2, 3, 5, 7), at the bases N in 59..95 where 2N is 7-smooth but not
5-smooth: N = 63, 70, 84 (n = 62, 69, 83), plus the sanity tier t80 (N = 80, gain 1, 7-smooth),
which must re-find a rule because the n = 79 rule of cover_n079.json lies in this menu.

Both known single-base covers in the open range touch their top speed 2N (128 at N = 64, 160 at
N = 80), and every base whose 2N is 5-smooth was already a route-19d target. The bases where 7
first makes the top speed touchable are exactly 63, 70 and 84.

One tier-turn per probe (cap 440 s), because a solver call that is cut off adds nothing and
route 19d's 5-smooth calls already took 160-250 s. State is kept in %TEMP%/mv2-slr-t1; a tier
is seeded with the classes route 19d collected at the same N and gain (%TEMP%/mv2-slr-r1),
which is valid in any menu because clauses are rebuilt from the current menu.

Every FOUND tier is checked by top_q.full_cert (both slr.py checkers and indep_cover) and, in
addition, by the stand-alone verify_cover.first_gap at radius 1/(n+1), with the runner count
and distinctness checked here.
"""
import json
import os
import tempfile
import time
from fractions import Fraction as F

import rules_m
import rule_search_s as rs
import top_o as to
import top_p as tp
import top_q as tq
import verify_cover as vc

P7 = (2, 3, 5, 7)
KIND = tq.KIND
DENS_Q = tq.DENS_Q

TIERS = {"t63": (63, 1, P7), "t70": (70, 1, P7), "t84": (84, 1, P7), "t80": (80, 1, P7)}
SANITY = ["t80"]
ORDER = ["t63", "t70", "t84", "t80"]
CAP = 440


def menu_line(tag):
    N, g, P = TIERS[tag]
    touch, fixed, added = to.pools_o(N, P)
    return "MENU %s N=%d n=%d top=%d touch=%d fixed=%d added=%d top_touchable=%s" % (
        tag, N, N - g, 2 * N, len(touch), len(fixed), len(added), (2 * N) in touch)


def seeds_from_r(tag, r1):
    """Classes route 19d collected at the same N and gain (valid in any menu)."""
    N, g, _P = TIERS[tag]
    src = "r%d" % N if g == 1 else "r%dg%d" % (N, g)
    return [[int(q), int(k)] for q, k in ((r1.get(src) or {}).get("classes") or [])]


def stand_alone(cert, n):
    """verify_cover on the certified speeds/shifts: (ok, note)."""
    v = [int(x) for x in cert.get("speeds") or []]
    s = [F(x) for x in cert.get("shifts") or []]
    if not v or len(v) != len(s):
        return False, "no speeds"
    if len(set(v)) != len(v) or min(v) < 1:
        return False, "speeds not distinct positive"
    if len(v) > n:
        return False, "%d runners > n" % len(v)
    gap = vc.first_gap(v, s, F(1, n + 1))
    return gap is None, "runners=%d gap=%s" % (len(v), gap)


def probe_t(label, budget=480, workers=8, cache=None, r1_cache=None):
    """Run pending tiers (fewest turns first), certify any FOUND tier with four exact
    checkers, return a short report whose last lines matter most."""
    t0 = time.time()
    t_end = t0 + budget
    tmp = tempfile.gettempdir()
    cache = cache or os.path.join(tmp, "mv2-slr-t1")
    r1_cache = r1_cache or os.path.join(tmp, "mv2-slr-r1")
    os.makedirs(cache, exist_ok=True)
    state_path = os.path.join(cache, "state.json")
    state = rs._load(state_path, {})
    r1 = rs._load(os.path.join(r1_cache, "state.json"), {})
    head = ["REPORT %s" % label]
    ok, note = rs.ensure_ortools()
    head.append("ortools=%s %s r1=%d" % (ok, note[:30], len(r1)))
    for t in ORDER:
        try:
            head.append(menu_line(t))
        except Exception as e:  # report, do not hide
            head.append("MENU %s ERROR %r" % (t, e))
    diag = []
    while ok:
        pend = [t for t in ORDER if state.get(t, {}).get("status") not in
                ("FOUND", "INFEASIBLE", "BUG")]
        if not pend:
            break
        pend.sort(key=lambda t: (state.get(t, {}).get("turns", 0), ORDER.index(t)))
        tag = pend[0]
        N, g, P = TIERS[tag]
        left = t_end - time.time()
        if left < 60:
            break
        prev = state.get(tag, {})
        seeds = prev.get("classes")
        if seeds is None:
            seeds = seeds_from_r(tag, r1)
        try:
            info = tp.cegar_p(N, g, P, KIND, DENS_Q, time.time() + min(CAP, left - 15),
                              workers=workers, seed_classes=seeds)
        except Exception as e:
            info = {"status": "BUG", "why": [repr(e)[:160]], "iterations": 0, "seconds": 0,
                    "solve_seconds": 0, "classes": prev.get("classes", seeds or [])}
        info["seeded"] = len(seeds or [])
        info["turns"] = prev.get("turns", 0) + 1
        info["it_total"] = prev.get("it_total", 0) + info.get("iterations", 0)
        info["sec_total"] = prev.get("sec_total", 0) + info.get("seconds", 0)
        info["solve_total"] = prev.get("solve_total", 0) + info.get("solve_seconds", 0)
        if info["status"] == "FOUND":
            n = N - g
            try:
                full = tq.full_cert(rules_m.rule_from_json(info["rule"]), N, n)
                ok4, note4 = stand_alone(full, n)
            except Exception as e:
                full, ok4, note4 = {"ok": False, "why": repr(e)[:120]}, False, "error"
            info["cert"] = {k: v for k, v in full.items() if k not in ("speeds", "shifts")}
            info["cert"]["stand_alone"] = ok4
            info["cert"]["stand_alone_note"] = note4
            if not (full.get("ok") and ok4):
                info["status"] = "BUG"
                info["why"] = ["fixed_check passed but a global check failed",
                               json.dumps(info["cert"])[:160]]
            else:
                with open(os.path.join(cache, "cert_%s.json" % tag), "w",
                          encoding="utf-8") as f:
                    json.dump({"tag": tag, "N": N, "n": n, "rule": info["rule"],
                               "speeds": full["speeds"],
                               "shifts": [str(x) for x in full["shifts"]],
                               "cert": info["cert"]}, f)
        state[tag] = info
        rs._save(state_path, state)
        diag.append("D %s %s turn=%d seeded=%d it=%d cls=%d solve=%s sec=%s" % (
            tag, info["status"][:4], info["turns"], info["seeded"], info.get("iterations", 0),
            len(info.get("classes") or []), info.get("solve_seconds", "-"),
            info.get("seconds", "-")))
    toks = " ".join(tp._tok(t, state.get(t)) for t in ORDER)
    tail = []
    new = []
    for t in ORDER:
        st = state.get(t, {})
        if st.get("status") == "BUG":
            tail.append("BUG %s %s" % (t, " | ".join(st.get("why", []))[:240]))
        if st.get("status") != "FOUND":
            continue
        N, g, _P = TIERS[t]
        word = "SANE" if t in SANITY else "RULE"
        if t not in SANITY:
            new.append(N - g)
        tail.append(("%s %s N=%d n=%d %s" % (word, t, N, N - g, tp.short_rule(st["rule"])))[:900])
        tail.append("CERT %s %s" % (t, json.dumps(st.get("cert"))[:300]))
    cnt = {}
    for t in ORDER:
        s = state.get(t, {}).get("status", "-")
        cnt[s] = cnt.get(s, 0) + 1
    tail.append("STATUS new_n=%s %s elapsed=%.0f" % (new or "-", " ".join(
        "%s=%d" % (k, v) for k, v in sorted(cnt.items())), time.time() - t0))
    return "\n".join(head + diag + ["TIT " + toks] + tail)
