# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 19 (PREREG_rules_o.md): rules on the even base at ONE fixed N, with the slack radius.

Poliakova's local rules (arXiv:2609.23952; rules.py, rules_m.py here) must work for every N
at once, so they cover at radius exactly delta = 1/(N+1) and give n >= L/2 - g. A gain-g
configuration for ONE n = N - g only has to cover at some radius r < 1/(n+1), which is larger
than delta. Xavier Callens's n = 63 cover (Zenodo 24051700) uses exactly that slack: it is a
Poliakova-type rule on 2, 4, ..., 128 whose top speed 128 = 2N sits at shift -delta, and the
half of the top speed's times it leaves open is closed by the untouched speed 2 at radius
delta (1 + delta) = 66/4225 < 1/64 (README, "top trick").

Fixed-N criterion (`fixed_check`). Base: speeds 2, 4, ..., 2N, shift 0, a closed delta-cover
(Dirichlet). Edit it by a rule (removed R, rephased S with shift s0 + beta delta, added odd
speeds A with shift s0 + beta delta), gain g = |R| - |A| >= 1, n = N - g, and fix a radius
r = rho delta with delta <= r < 1/(n+1). Suppose that for every touched q (in R or S), every
integer k in [0, q) with gcd(k, q/2) = 1 and every z in [-1, 1] there are a runner (speed w,
shift s0 + beta delta; untouched base runners have s0 = beta = 0) and an integer J with

    | (x - J)(N + 1) + c z + beta | <= rho,    c = w / q,  x = c k + s0.

Then the edited configuration (N - g runners, all speeds distinct) covers the circle with
CLOSED arcs of radius r, so its open arcs of radius 1/(n+1) cover it and, padded with unused
speeds at shift 0 up to n runners, it is a counterexample to the shifted Lonely Runner
Conjecture for n.

Proof. Fix t and let q be the smallest base speed with ||q t|| <= delta. If q is untouched it
is present and covers t at radius delta <= r. Otherwise write q t = k + delta z with k an
integer and |z| <= 1; as in rules_m.py, minimality of q forces gcd(k, q/2) = 1, and k may be
taken mod q. A runner of speed w and shift s0 + beta delta sits at
w t + s0 + beta delta = x + delta (c z + beta), and its distance to the integer J is
delta |(x - J)(N + 1) + c z + beta| <= rho delta = r. QED.

The condition ranges over every runner and every J, so it is also NECESSARY for a closed
r-cover: `fixed_check` is an exact closed-cover test at radius r, organised by the class of
the responsible base speed (test_top_o.py checks it against slr.covers_sweep on random rules).

Search (`cegar_o`). For one N and gain g, the touchable speeds are the P-smooth even speeds up
to 2N (removed, untouched, or rephased with s0 in a finite menu of fractions and beta in a
finite menu); the other even speeds stay untouched; the P-smooth odd speeds up to 2N + 1 may be
added. Clauses per class (q, k) are built exactly as in rule_search_c.class_clauses, but with
every runner and every lift J (near misses included) and with the slack rho; CP-SAT
(rule_search_c.build_and_solve) proposes a rule, `fixed_check` tests it exactly, failing
classes are added. The loop ends FOUND (then `certify`: both global exact checkers of slr.py at
R = 1/(n+1)) or INFEASIBLE on a subset of the clauses, which is a proof for that finite menu
only.
"""
import json
import math
import os
import tempfile
import time
from fractions import Fraction as F

import rules_m
import rule_search_m
import rule_search_s as rs
import rule_search_c as rsc
import slr

H = F(1, 2)
DENS_A = frozenset({1, 2, 3, 4, 6})
P3 = (2, 3)
P5 = (2, 3, 5)
KNOWN_N = 63  # Callens; open: 58..62 and 64..94 (2026-11-27)

# Callens, Zenodo 24051700 (cert_n063.json, CC BY 4.0), written as a rule at N = 64,
# delta = 1/65: every shift of his certificate is a / 520 and 8/520 = delta.
CALLENS_63 = {
    "m": 2,
    "removed": [4, 8, 32, 72, 96, 108],
    "rephased": {12: (H, H), 16: (F(0), F(-1)), 24: (H, H), 36: (H, H), 48: (H, -H),
                 64: (F(0), F(1)), 128: (F(0), F(-1))},
    "added": {1: (F(3, 4), F(-5, 8)), 3: (F(3, 4), F(0)), 9: (F(3, 4), F(-1, 4)),
              27: (F(3, 4), F(1, 8)), 81: (F(3, 4), F(1, 8))},
}


def radius(n):
    """Closed radius used for n runners: r = 128 / (128 (n + 1) + 1), just below 1/(n+1)."""
    return F(128, 128 * (n + 1) + 1)


def rho_of(N, g):
    """rho = r (N + 1) for n = N - g."""
    return radius(N - g) * (N + 1)


def runners_of(rule, N):
    """(speed, s0, beta) of every runner of the rule applied to the base 2, 4, ..., 2N."""
    m, removed, reph, added = rules_m._norm_rule(rule)
    if m != 2:
        raise ValueError("route 19 uses the even base (m = 2)")
    X = set(removed) | set(reph)
    if X and max(X) > 2 * N:
        raise ValueError("rule touches a speed above 2N")
    rem = set(removed)
    out = []
    for w in range(2, 2 * N + 1, 2):
        if w in rem:
            continue
        s0, b = reph.get(w, (F(0), F(0)))
        out.append((w, s0, b))
    for a in sorted(added):
        s0, b = added[a]
        out.append((a, s0, b))
    return out


def z_intervals(w, s0, b, q, k, N, rho):
    """Closed z-intervals in [-1, 1] on which runner (w, s0 + b delta) is within rho delta of
    an integer at t = (k + delta z)/q, delta = 1/(N+1). One interval per lift J."""
    d = N + 1
    cf = w / q
    xf = w * k / q + float(s0)
    bf = float(b)
    rf = float(rho)
    if math.floor(xf + (bf + rf + cf) / d + 1e-9) < math.ceil(xf + (bf - rf - cf) / d - 1e-9):
        return []
    c = F(w, q)
    x = F(w * k, q) + s0
    jlo = math.ceil(x + (b - rho - c) / d)
    jhi = math.floor(x + (b + rho + c) / d)
    out = []
    for J in range(jlo, jhi + 1):
        A = (x - J) * d
        lo = max((-rho - b - A) / c, F(-1))
        hi = min((rho - b - A) / c, F(1))
        if lo <= hi:
            out.append((lo, hi))
    return out


def fixed_check(rule, N, g=None, rho=None):
    """Exact closed-cover test at radius rho/(N+1) (module docstring). Returns (ok, fails)
    with fails [(q, k, z), ...] (z: first uncovered point found), or (False, [problems])."""
    probs = rules_m.shape_problems(rule)
    if probs:
        return False, probs
    m, removed, reph, added = rules_m._norm_rule(rule)
    if g is None:
        g = len(removed) - len(added)
    if rho is None:
        rho = rho_of(N, g)
    runners = runners_of(rule, N)
    fails = []
    for q in sorted(set(removed) | set(reph)):
        for k in rules_m.responsible_classes(q, 2):
            iv = []
            for w, s0, b in runners:
                iv.extend(z_intervals(w, s0, b, q, k, N, rho))
            ok, z = rules_m.closed_cover(iv)
            if not ok:
                fails.append((q, k, z))
    return not fails, fails


def _pad(v, s, n):
    """Pad to n runners with the smallest unused odd speeds at shift 0."""
    v, s = list(v), list(s)
    used = set(v)
    a = 1
    while len(v) < n:
        if a not in used:
            v.append(a)
            s.append(F(0))
            used.add(a)
        a += 2
    return v, s


def certify(rule, N, n=None):
    """Both global exact checkers of slr.py at R = 1/(n+1), n = N - g unless given (n must be
    at least the number of runners; extra runners are padded at shift 0)."""
    g = rules_m.gain(rule)
    v, s, _delta, k = rules_m.build_config(rule, N)
    n = N - g if n is None else n
    t0 = time.time()
    if k > n:
        return {"ok": False, "n": n, "N": N, "why": "more runners than n"}
    v, s = _pad(v, s, n)
    R = F(1, n + 1)
    a, _ = slr.covers_sweep(v, s, R)
    b, _ = slr.covers_endpoints(v, s, R)
    distinct = len(set(v)) == len(v) == n
    return {"ok": bool(a and b and distinct), "n": n, "N": N, "sweep": a, "endpoints": b,
            "distinct": distinct, "R": str(R), "seconds": round(time.time() - t0, 2),
            "speeds": v, "shifts": [str(x) for x in s]}


# ------------------------------------------------------------------ search

def s0_menu(dens):
    return sorted({F(j, d) for d in dens for j in range(d)})


def betas_of(kind):
    """'h': halves on [-2, 2]; 'x': eighths on [-1, 1] and halves on [-2, 2]."""
    if kind == "h":
        return rule_search_m.halves()
    if kind == "x":
        return sorted(set(rule_search_m.halves()) | {F(j, 8) for j in range(-8, 9)})
    raise ValueError(kind)


def pools_o(N, P):
    """(touchable, fixed, added) at base size N. Touchable: the P-smooth multiples of 4 up to
    2N and the top speed 2N itself if it is P-smooth (Callens's and Poliakova's rules touch
    only multiples of 4). Every other even speed is a fixed, untouched runner."""
    touch = [w for w in range(2, 2 * N + 1, 2)
             if rs.smooth(w, P) and (w % 4 == 0 or w == 2 * N)]
    tset = set(touch)
    fixed = [w for w in range(2, 2 * N + 1, 2) if w not in tset]
    added = [a for a in range(1, 2 * N + 2, 2) if rs.smooth(a, P)]
    return touch, fixed, added


def class_clauses_o(q, k, N, rho, touch, fixed, added, s0s, betas):
    """Clauses for class k of the touched base speed q (keys as in rule_search_c:
    ('u', w) untouched touchable, ('e', w, s0, b) rephased, ('o', a, s0, b) added). A segment
    of [-1, 1] covered by a fixed (never touched) runner needs no clause; an empty clause
    means that q cannot be touched."""
    ivs = []
    const = []
    zero = F(0)
    for w in fixed:
        for lo, hi in z_intervals(w, zero, zero, q, k, N, rho):
            if lo < hi:
                const.append((lo, hi))
    for w in touch:
        for lo, hi in z_intervals(w, zero, zero, q, k, N, rho):
            if lo < hi:
                ivs.append((lo, hi, ("u", w)))
        for s0 in s0s:
            for b in betas:
                if s0 == 0 and b == 0:
                    continue
                for lo, hi in z_intervals(w, s0, b, q, k, N, rho):
                    if lo < hi:
                        ivs.append((lo, hi, ("e", w, s0, b)))
    for a in added:
        for s0 in s0s:
            for b in betas:
                for lo, hi in z_intervals(a, s0, b, q, k, N, rho):
                    if lo < hi:
                        ivs.append((lo, hi, ("o", a, s0, b)))
    pts = sorted({F(-1), F(1)} | {x for lo, hi, _ in ivs for x in (lo, hi)}
                 | {x for lo, hi in const for x in (lo, hi)})
    starts, ends = {}, {}
    for i, (lo, hi, _) in enumerate(ivs):
        starts.setdefault(lo, []).append(i)
        ends.setdefault(hi, []).append(i)
    cst, cen = {}, {}
    for lo, hi in const:
        cst[lo] = cst.get(lo, 0) + 1
        cen[hi] = cen.get(hi, 0) + 1
    mask = 0
    ccount = 0
    seen = set()
    for j in range(len(pts) - 1):
        p = pts[j]
        for i in ends.get(p, ()):
            mask &= ~(1 << i)
        for i in starts.get(p, ()):
            mask |= 1 << i
        ccount += cst.get(p, 0) - cen.get(p, 0)
        if ccount <= 0:
            seen.add(mask)
    uniq = set()
    for x in seen:
        keys = set()
        while x:
            low = x & -x
            keys.add(ivs[low.bit_length() - 1][2])
            x ^= low
        uniq.add(frozenset(keys))
    keysets = sorted(uniq, key=lambda ks: (len(ks), sorted(map(repr, ks))))
    if len(keysets) <= 400:  # drop clauses implied by smaller ones (only an optimisation)
        kept = []
        for ks in keysets:
            if any(y <= ks for y in kept):
                continue
            kept.append(ks)
        keysets = kept
    return [sorted(ks, key=repr) for ks in keysets]


def _spread(xs, n):
    if len(xs) <= n:
        return list(xs)
    step = len(xs) / float(n)
    return [xs[int(i * step)] for i in range(n)]


def cegar_o(N, g, P, kind, dens, deadline, workers=6, seed_classes=None, per_q=12,
            seed_per_q=3, it_time=20.0):
    """Decide whether the menu has a rule of gain >= g passing fixed_check at N.
    Returns info: status FOUND (info['rule']), INFEASIBLE (none in the menu), UNKNOWN, BUG."""
    t0 = time.time()
    rho = rho_of(N, g)
    touch, fixed, added = pools_o(N, P)
    s0s = s0_menu(dens)
    betas = betas_of(kind)
    clauses = {}

    def add_class(q, k):
        if (q, k) in clauses:
            return False
        clauses[(q, k)] = class_clauses_o(q, k, N, rho, touch, fixed, added, s0s, betas)
        return True

    for q in touch:
        for k in _spread(rules_m.responsible_classes(q, 2), seed_per_q):
            add_class(q, k)
    for qk in seed_classes or []:
        add_class(int(qk[0]), int(qk[1]))
    it = 0
    tl = it_time
    status = "UNKNOWN"
    info = {}
    while True:
        left = deadline - time.time()
        if left < 8:
            break
        it += 1
        st, cand = rsc.build_and_solve(clauses, touch, g, min(tl, left - 4), workers)
        if st == "INFEASIBLE":
            status = "INFEASIBLE"
            break
        if cand is None:
            tl = min(4 * tl, 300.0)
            continue
        rule = {"m": 2, "removed": cand["removed"], "rephased": cand["rephased"],
                "added": cand["added"]}
        ok, fails = fixed_check(rule, N, g=g, rho=rho)
        if ok:
            status = "FOUND"
            info["rule"] = rules_m.rule_to_json(rule)
            info["gain"] = rules_m.gain(rule)
            break
        if fails and not isinstance(fails[0], tuple):
            status = "BUG"
            info["why"] = [str(x) for x in fails[:2]]
            break
        byq = {}
        for q, k, _z in fails:
            byq.setdefault(q, []).append(k)
        new = 0
        for q, ks in byq.items():
            for k in _spread(ks, per_q):
                new += add_class(q, k)
        if new == 0:
            status = "BUG"
            info["why"] = ["no new class", str(fails[:2])]
            break
    info.update({"status": status, "iterations": it, "n_classes": len(clauses),
                 "seconds": round(time.time() - t0, 1), "n_touch": len(touch),
                 "classes": sorted([list(x) for x in clauses])})
    return info


# ------------------------------------------------------------------ tiers and probe

def _tiers():
    """tag: (N, g, P, beta kind, dens, cap seconds per turn)."""
    T = {"f96h": (96, 1, P3, "h", DENS_A, 90),   # sanity: Poliakova's 9 -> 8 rule fits
         "f64x": (64, 1, P3, "x", DENS_A, 150),  # sanity: Callens's rule is in this menu
         "h64": (64, 1, P3, "h", DENS_A, 40),    # calibration: are halves enough at N = 64?
         "x64g2": (64, 2, P3, "x", DENS_A, 60)}  # n = 62
    for N in [72, 81] + [N for N in range(59, 96) if N not in (64, 72, 81)]:
        T["x%d" % N] = (N, 1, P3, "x", DENS_A, 45)  # n = N - 1
    return T


TIERS = _tiers()
ORDER = ["f96h", "f64x", "h64", "x64g2", "x72", "x81"] + [
    "x%d" % N for N in range(59, 96) if N not in (64, 72, 81)]


def _tok(tag, st):
    if not st:
        return "%s:-" % tag
    return "%s:%s%d/%d" % (tag, st["status"][0], st.get("it_total", 0), st.get("sec_total", 0))


def checks():
    """Exact calibration on the two known rules (cheap)."""
    out = {}
    out["cal"] = fixed_check(CALLENS_63, 64)[0]
    out["cal1"] = fixed_check(CALLENS_63, 64, rho=F(1))[0]
    out["cal66"] = fixed_check(CALLENS_63, 64, rho=F(66, 65))[0]  # gamma = 66/4225 exactly?
    out["calcert"] = certify(CALLENS_63, 64)["ok"]
    out["pol"] = fixed_check(rules_m.POLIAKOVA_9_8, 96, rho=F(1))[0]
    return out


def probe_o(budget=520, workers=6, cache=None, order=None):
    """Run pending tiers (fewest turns first), certify any FOUND target, return a short
    report whose last lines are the ones that matter."""
    t_end = time.time() + budget
    cache = cache or os.path.join(tempfile.gettempdir(), "mv2-slr-o1")
    os.makedirs(cache, exist_ok=True)
    state_path = os.path.join(cache, "state.json")
    state = rs._load(state_path, {})
    head = []
    tail = []
    try:
        c = checks()
        head.append("CHK " + " ".join("%s=%s" % (k, "T" if v else "F") for k, v in c.items()))
    except Exception as e:  # report, do not hide
        head.append("CHK ERROR %r" % (e,))
    ok, note = rs.ensure_ortools()
    head.append("ortools=%s %s" % (ok, note[:60]))
    order = order or ORDER
    while ok:
        pend = [t for t in order if state.get(t, {}).get("status") not in
                ("FOUND", "INFEASIBLE", "BUG")]
        if not pend:
            break
        pend.sort(key=lambda t: (state.get(t, {}).get("turns", 0), order.index(t)))
        tag = pend[0]
        N, g, P, kind, dens, cap = TIERS[tag]
        left = t_end - time.time()
        if left < 30:
            break
        prev = state.get(tag, {})
        try:
            info = cegar_o(N, g, P, kind, dens, time.time() + min(cap, left - 15),
                           workers=workers, seed_classes=prev.get("classes"))
        except Exception as e:
            info = {"status": "BUG", "why": [repr(e)[:160]], "iterations": 0, "seconds": 0,
                    "classes": prev.get("classes", [])}
        info["turns"] = prev.get("turns", 0) + 1
        info["it_total"] = prev.get("it_total", 0) + info.get("iterations", 0)
        info["sec_total"] = prev.get("sec_total", 0) + info.get("seconds", 0)
        if info["status"] == "FOUND":
            full = certify(rules_m.rule_from_json(info["rule"]), N, n=N - g)
            info["cert"] = {k: v for k, v in full.items() if k not in ("speeds", "shifts")}
            if not full["ok"]:
                info["status"] = "BUG"
                info["why"] = ["fixed_check passed but the global check failed"]
            else:
                with open(os.path.join(cache, "cert_%s.json" % tag), "w",
                          encoding="utf-8") as f:
                    json.dump({"tag": tag, "rule": info["rule"], "cert": full}, f)
        state[tag] = info
        rs._save(state_path, state)
    toks = [_tok(t, state.get(t)) for t in order]
    body = [" ".join(toks[i:i + 8]) for i in range(0, len(toks), 8)]
    for t in order:
        st = state.get(t, {})
        if st.get("status") == "BUG":
            tail.append("BUG %s %s" % (t, " | ".join(st.get("why", []))[:200]))
    new = []
    for t in order:
        st = state.get(t, {})
        if st.get("status") != "FOUND":
            continue
        N, g = TIERS[t][0], TIERS[t][1]
        rj = st["rule"]
        if t.startswith("f") or N - g == KNOWN_N or N - g >= 95:
            tail.append("SANE %s gain=%d touched=%d" % (
                t, st.get("gain", 0), len(rj["removed"]) + len(rj["rephased"]) + len(rj["added"])))
            continue
        new.append(N - g)
        tail.append(("RULE %s n=%d %s" % (t, N - g, rs.fmt_rule(rj)))[:700])
        tail.append("CERT %s %s" % (t, json.dumps(st.get("cert"))[:200]))
    cnt = {}
    for t in order:
        s = state.get(t, {}).get("status", "-")
        cnt[s] = cnt.get(s, 0) + 1
    tail.append("STATUS new_n=%s %s" % (new or "-", " ".join(
        "%s=%d" % (k, v) for k, v in sorted(cnt.items()))))
    return "\n".join(head + body + tail)
