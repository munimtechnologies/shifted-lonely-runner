# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 13 (PREREG_rules_g.md): an exact search for a counterexample to the shifted Lonely
Runner Conjecture at ONE fixed n (n = 94), on a base of multiples of m = 2, 3, 4 or 6.

Routes 10-12 searched for uniform local rules (rules_m.py). A uniform rule must cover every
class of every touched speed for the closed radius delta = 1/(N+1) and for every N at once.
At one fixed n the real requirement is weaker: the OPEN arcs of radius R = 1/(n+1) must cover
the circle (then gamma(v; s) < 1/(n+1), slr.py). Starting from the base m, 2m, ..., mN with
N = n + g, R = 1/(n+1) is larger than the base's own Dirichlet radius 1/(N+1), so the base has
slack, and untouched base runners that are not multiples of a touched speed help as well.

Menu ("A"): every P-smooth base speed m j (j <= N) may be removed or rephased; the other base
speeds stay at shift 0. Added speeds: P-smooth positive integers up to 2 m N + 1 that are not
multiples of m. Every shift (rephase or added) is sigma0 + beta/(N+1) with sigma0 in
{a/d : d in DENS} and beta in steps of 1/2 on [-2, 2]; Poliakova's rule (arXiv:2609.23952) is in
this menu. A configuration of the menu is a counterexample for n if it has at most n runners
(padding with new speeds keeps a cover) and its open R-arcs cover the circle.

Decision procedure: counterexample-guided search over time points. For a point t, the clause
"some chosen option covers t" lists every option of the menu whose open R-arc contains t
(untouched touchable base speed, rephase option, added option); if a fixed base runner covers
t there is no clause. CP-SAT finds a configuration satisfying the clauses collected so far
with sum(removed) - sum(added) >= N - n; it is checked exactly; points it leaves uncovered
add new clauses (each violated by it), and so on. A configuration passing the exact checks is
FOUND and is then re-checked by both global checkers of slr.py. INFEASIBLE on the collected
clauses means no configuration of the menu covers even those points, so none exists (a proof
for the finite menu only). Options that occur in no clause are never created; a configuration
using one can drop it (an add) or remove that base speed instead (a rephase), keeping every
clause and not lowering the gain, so INFEASIBLE stays sound.
"""
import json
import math
import os
import tempfile
import time
from fractions import Fraction as F

import rule_search_s as rs
import slr

NMAX = 94
DENS_A = (1, 2, 3, 4, 6)
HALVES = tuple(F(b, 2) for b in range(-4, 5))
P3 = (2, 3)
P5 = (2, 3, 5)

# tag: (m, n, N, P, hint, expectation)
TIERS_G = {
    "g2H": (2, 95, 96, P3, "poliakova", "find"),   # sanity: Poliakova's rule as a solver hint
    "g2N": (2, 94, 95, P3, None, "none?"),          # control (aadrianvv: UNSAT in a Z/4 menu)
    "g6N": (6, 94, 95, P5, None, "search"),         # target: thirds and sixths, n = 94
    "g3N": (3, 94, 95, P5, None, "search"),
    "g4N": (4, 94, 95, P5, None, "search"),
    "g6G2": (6, 94, 96, P5, None, "search"),        # target: gain 2 from N = 96
}
ORDER_G = ["g2H", "g2N", "g6N", "g3N", "g4N", "g6G2"]

PLAN_G1 = [("g2H", 60), ("g2N", 170), ("g6N", 280)]
PLAN_G2 = [("g6N", 510)]
PLAN_G3 = [("g3N", 250), ("g4N", 260)]


def shift_unit(N):
    """Md = lcm(12, 2 (N + 1)): every menu shift is an integer multiple of 1/Md."""
    a, b = 12, 2 * (N + 1)
    return a * b // math.gcd(a, b)


def shift_menu(N, dens=DENS_A, betas=HALVES):
    """(Md, sorted list of S mod Md) for the shifts sigma0 + beta/(N+1)."""
    Md = shift_unit(N)
    out = set()
    for d in dens:
        for a in range(d):
            for b in betas:
                x = F(a, d) * Md + b * F(Md, N + 1)
                if x.denominator != 1:
                    raise ValueError("shift not on the grid")
                out.add(int(x) % Md)
    return Md, sorted(out)


def shift_key(sigma0, beta, N):
    """S of the shift sigma0 + beta/(N+1)."""
    Md = shift_unit(N)
    x = F(sigma0) * Md + F(beta) * F(Md, N + 1)
    if x.denominator != 1:
        raise ValueError("shift not on the grid")
    return int(x) % Md


def pools_g(m, N, P, A=None):
    """(touchable base speeds, fixed base speeds, addable speeds)."""
    A = 2 * m * N + 1 if A is None else A
    base = [m * j for j in range(1, N + 1)]
    touch = [w for w in base if rs.smooth(w, P)]
    fixed = [w for w in base if not rs.smooth(w, P)]
    added = [a for a in range(1, A + 1) if a % m and rs.smooth(a, P)]
    return touch, fixed, added


def covered_int(v, S, p, q, Md, n1):
    """Exact: is ||v p/q + S/Md|| < 1/n1 ?"""
    M = Md * q
    X = (v * p * Md + S * q) % M
    return min(X, M - X) * n1 < M


def point_clause(t, n, touch, fixed, added, Md, shifts):
    """Keys of every menu option whose open arc of radius 1/(n+1) contains t, or None if a
    fixed base runner covers t. Keys: 'u:w' (w untouched), 'e:w:S' (w rephased to S/Md),
    'o:a:S' (a added at S/Md)."""
    t = F(t) % 1
    p, q = t.numerator, t.denominator
    n1 = n + 1
    M = Md * q
    for w in fixed:
        if covered_int(w, 0, p, q, Md, n1):
            return None
    keys = []
    for kind, pool in (("e", touch), ("o", added)):
        for w in pool:
            base = (w * p * Md) % M
            for S in shifts:
                X = (base + S * q) % M
                if min(X, M - X) * n1 < M:
                    if kind == "e" and S == 0:
                        keys.append("u:%d" % w)
                    else:
                        keys.append("%s:%d:%d" % (kind, w, S))
            if kind == "e" and 0 not in shifts:
                if covered_int(w, 0, p, q, Md, n1):
                    keys.append("u:%d" % w)
    return keys


def config_of(cand, m, N, Md):
    """Speeds and exact shifts of a candidate {'removed': [...], 'rephased': {w: S},
    'added': {a: S}}."""
    rem = set(cand["removed"])
    v, s = [], []
    for j in range(1, N + 1):
        w = m * j
        if w in rem:
            continue
        v.append(w)
        s.append(F(cand["rephased"].get(w, 0), Md) % 1)
    for a in sorted(cand["added"]):
        v.append(a)
        s.append(F(cand["added"][a], Md) % 1)
    return v, s


def lits_of(cand, touch):
    """The set of keys a candidate makes true."""
    out = set()
    for w in touch:
        if w in cand["removed"]:
            continue
        S = cand["rephased"].get(w)
        out.add("u:%d" % w if S is None or S == 0 else "e:%d:%d" % (w, S))
    for a, S in cand["added"].items():
        out.add("o:%d:%d" % (a, S))
    return out


def uncovered_exact(t, v, s, n):
    """Exact: is t outside every open arc of radius 1/(n+1)?"""
    R = F(1, n + 1)
    for vi, si in zip(v, s):
        x = (vi * t + si) % 1
        if min(x, 1 - x) < R:
            return False
    return True


def float_scan(v, s, R, eps=1e-11):
    """Float sweep of the arcs {t : ||v t + s|| < R}. Returns (gaps, touches): the open gaps
    (a, b) of their union in [0, 1), and (runner index, i) of every arc whose left end lies
    within eps of the covered front (an exact abutment there leaves an isolated uncovered
    point, which a float sweep cannot see)."""
    arcs = []
    for k, (vi, si) in enumerate(zip(v, s)):
        sf = float(si)
        w = 2.0 * R / vi
        for i in range(vi):
            lo = ((i - sf - R) / vi) % 1.0
            hi = lo + w
            if hi <= 1.0:
                arcs.append((lo, hi, k, i))
            else:
                arcs.append((lo, 1.0, k, i))
                arcs.append((0.0, hi - 1.0, k, -1))
    arcs.sort()
    gaps = []
    touches = []
    cur = 0.0
    for lo, hi, k, i in arcs:
        if lo > cur + eps:
            gaps.append((cur, lo))
        elif lo > cur - eps and i >= 0:  # abutment or a gap too thin for floats
            touches.append((k, i))
        if hi > cur:
            cur = hi
    if cur < 1.0:
        gaps.append((cur, 1.0))
    return gaps, touches


def float_gaps(v, s, R):
    """Open gaps (a, b) of the union of the float arcs {t : ||v t + s|| < R} in [0, 1)."""
    return float_scan(v, s, R)[0]


def touch_points(touches, v, s, n, cap):
    """Exact left ends of the touching arcs that no open arc contains (at most cap)."""
    R = F(1, n + 1)
    out = []
    for k, i in touches:
        t = ((i - F(s[k]) - R) / v[k]) % 1
        if uncovered_exact(t, v, s, n):
            out.append(t)
            if len(out) >= cap:
                break
    return out


def gap_points(gaps, cap):
    """Up to 3 exact points per gap (midpoint first), at most cap in total."""
    pts = []
    for a, b in sorted(gaps, key=lambda g: g[0] - g[1]):
        for f in (0.5, 0.25, 0.75):
            x = a + f * (b - a)
            if a < x < b:
                pts.append(F(x) % 1)
        if len(pts) >= cap:
            break
    return pts[:cap]


def poliakova_cand(N):
    """Poliakova's 9 -> 8 rule (m = 2) as a candidate of this menu at base size N."""
    h = F(1, 2)
    return {"removed": [8, 32, 192],
            "rephased": {12: shift_key(h, h, N), 24: shift_key(h, h, N),
                         48: shift_key(h, h, N), 96: shift_key(h, h, N),
                         16: shift_key(0, -1, N), 64: shift_key(0, -1, N)},
            "added": {3: shift_key(F(1, 4), 0, N), 9: shift_key(F(1, 4), 0, N)}}


def seed_points(m, n, N, touch):
    """Dirichlet points c/(m (n+1)) and c/(m (N+1)), and exact points of the gaps that each
    touchable speed alone fills in the base."""
    pts = set()
    for D in (m * (n + 1), m * (N + 1)):
        for c in range(D):
            pts.add(F(c, D))
    base = [m * j for j in range(1, N + 1)]
    R = 1.0 / (n + 1)
    for w in touch:
        v = [x for x in base if x != w]
        s = [F(0)] * len(v)
        gaps, touches = float_scan(v, s, R)
        for x in gap_points(gaps, 12):
            pts.add(x)
        for x in touch_points(touches, v, s, n, 12):
            pts.add(x)
    return sorted(pts)


def solve_g(clauses, touch, need, time_limit, workers, hint=None):
    """CP-SAT over the collected clauses. Returns (status name, candidate or None)."""
    from ortools.sat.python import cp_model
    _m = rs._m
    md = cp_model.CpModel()
    nb = _m(md, "new_bool_var", "NewBoolVar")
    bor = _m(md, "add_bool_or", "AddBoolOr")
    add = _m(md, "add", "Add")
    rem = {w: nb("rem%d" % w) for w in touch}
    unt = {w: nb("unt%d" % w) for w in touch}
    opt = {}

    def lit(key):
        if key.startswith("u:"):
            return unt[int(key[2:])]
        if key not in opt:
            opt[key] = nb("x%d" % len(opt))
        return opt[key]

    for keys in clauses:
        bor([lit(k) for k in keys])
    hl = lits_of(hint, touch) if hint is not None else set()
    for key in sorted(hl):  # the hint's own options exist even before a clause names them
        lit(key)
    by_base = {w: [] for w in touch}
    by_added = {}
    for key, var in opt.items():
        kind, w, _S = key.split(":")
        if kind == "e":
            by_base[int(w)].append(var)
        else:
            by_added.setdefault(int(w), []).append(var)
    for w in touch:
        add(rem[w] + unt[w] + sum(by_base[w]) == 1)
    for _a, vs in by_added.items():
        add(sum(vs) <= 1)
    added_vars = [v for vs in by_added.values() for v in vs]
    add(sum(rem.values()) - sum(added_vars) >= need)
    if hint is not None:
        ah = _m(md, "add_hint", "AddHint")
        for w in touch:
            ah(rem[w], 1 if w in hint["removed"] else 0)
            ah(unt[w], 1 if "u:%d" % w in hl else 0)
        for key, var in opt.items():
            ah(var, 1 if key in hl else 0)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(max(time_limit, 1.0))
    try:
        solver.parameters.num_workers = int(workers)
    except (AttributeError, ValueError):
        solver.parameters.num_search_workers = int(workers)
    st = _m(solver, "solve", "Solve")(md)
    name = _m(solver, "status_name", "StatusName")(st)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return name, None
    val = _m(solver, "value", "Value")
    cand = {"removed": [w for w in touch if val(rem[w])], "rephased": {}, "added": {}}
    for key, var in opt.items():
        if val(var):
            kind, w, S = key.split(":")
            if kind == "e":
                cand["rephased"][int(w)] = int(S)
            else:
                cand["added"][int(w)] = int(S)
    return name, cand


def fmt_cand(cand, Md):
    rp = ";".join("%d:%d" % (w, S) for w, S in sorted(cand["rephased"].items()))
    ad = ";".join("%d:%d" % (a, S) for a, S in sorted(cand["added"].items()))
    return "R=%s S={%s} A={%s} /Md=%d" % (sorted(cand["removed"]), rp, ad, Md)


def certify_g(cand, m, n, N, Md):
    """Both global exact checkers of slr.py at R = 1/(n+1), padded to exactly n runners."""
    v, s = config_of(cand, m, N, Md)
    k = N + 1
    while len(v) < n:
        while m * k in v:
            k += 1
        v.append(m * k)
        s.append(F(0))
        k += 1
    R = F(1, n + 1)
    a, _ = slr.covers_sweep(v, s, R)
    b, _ = slr.covers_endpoints(v, s, R) if a else (False, None)
    return {"n": len(v), "distinct": len(set(v)) == len(v), "sweep": a, "endpoints": b,
            "ok": bool(a and b and len(v) == n and len(set(v)) == len(v)),
            "speeds": v, "shifts": [str(x) for x in s]}


def cegar_g(tag, deadline, workers=6, prev=None, pts_per_it=240):
    """Point-CEGAR for one tier. prev: cached state (clauses, time limit). Status FOUND,
    INFEASIBLE, UNKNOWN or BUG."""
    t0 = time.time()
    m, n, N, P, hint_kind, _e = TIERS_G[tag]
    touch, fixed, added = pools_g(m, N, P)
    Md, shifts = shift_menu(N)
    need = N - n
    hint = poliakova_cand(N) if hint_kind == "poliakova" else None
    prev = prev or {}
    clauses = [list(c) for c in prev.get("clauses", [])]
    seen = set(frozenset(c) for c in clauses)
    info = {"tag": tag, "m": m, "n": n, "N": N, "n_touch": len(touch), "n_added": len(added),
            "n_shifts": len(shifts), "Md": Md, "status": "UNKNOWN"}

    def add_point(t):
        c = point_clause(t, n, touch, fixed, added, Md, shifts)
        if c is None:
            return 0
        fc = frozenset(c)
        if fc in seen:
            return 0
        seen.add(fc)
        clauses.append(sorted(fc))
        return 1

    if not clauses:
        for t in seed_points(m, n, N, touch):
            add_point(t)
            if time.time() > deadline - 30:
                break
    info["seeded"] = len(clauses)
    tl = float(prev.get("tl", 15.0))
    it = 0
    status = "UNKNOWN"
    while True:
        if any(len(c) == 0 for c in clauses):
            status = "INFEASIBLE"
            info["why"] = "a point no option covers"
            break
        left = deadline - time.time()
        if left < 10:
            break
        it += 1
        st, cand = solve_g(clauses, touch, need, min(tl, left - 6), workers, hint)
        if st == "INFEASIBLE":
            status = "INFEASIBLE"
            break
        if cand is None:
            tl = min(3 * tl, 600.0)
            continue
        v, s = config_of(cand, m, N, Md)
        lits = lits_of(cand, touch)
        new = 0
        gaps, touches = float_scan(v, s, 1.0 / (n + 1))
        pts = [x for x in gap_points(gaps, pts_per_it) if uncovered_exact(x, v, s, n)]
        if len(pts) < pts_per_it:
            pts += touch_points(touches, v, s, n, pts_per_it - len(pts))
        if not pts:
            ok, x = slr.covers_sweep(v, s, F(1, n + 1))
            if ok:
                cert = certify_g(cand, m, n, N, Md)
                info["cert"] = cert
                info["cand"] = {"removed": cand["removed"],
                                "rephased": {str(w): S for w, S in cand["rephased"].items()},
                                "added": {str(a): S for a, S in cand["added"].items()}}
                info["rule"] = fmt_cand(cand, Md)
                status = "FOUND" if cert["ok"] else "BUG"
                break
            pts = [F(x) % 1]
        for x in pts:
            c = point_clause(x, n, touch, fixed, added, Md, shifts)
            if c is not None and lits.intersection(c):
                status = "BUG"
                info["stuck_on"] = "candidate covers %s by the clause but not exactly" % x
                break
            new += add_point(x)
        if status == "BUG":
            break
        if new == 0:
            status = "BUG"
            info["stuck_on"] = "no new clause"
            break
    info.update({"status": status, "iterations": it, "n_clauses": len(clauses),
                 "literals": sum(len(c) for c in clauses), "tl": tl,
                 "seconds": round(time.time() - t0, 1), "clauses": clauses})
    return info


def _line(tag, r):
    return "%s m=%s n=%s N=%s st=%s it=%s cls=%s lits=%s tl=%s t=%ss" % (
        tag, r.get("m"), r.get("n"), r.get("N"), r.get("status"), r.get("iterations_total"),
        r.get("n_clauses"), r.get("literals"), int(r.get("tl", 0)), round(r.get("seconds_total", 0)))


def probe_g(plan, budget=530, workers=6, cache=None):
    """Run the (tag, seconds) plan in order; decided tiers are skipped, open ones resume.
    Report: details first, summary lines last."""
    t_end = time.time() + budget
    cache = cache or os.path.join(tempfile.gettempdir(), "mv2-slr-rules-g1")
    os.makedirs(cache, exist_ok=True)
    state_path = os.path.join(cache, "tiers.json")
    state = rs._load(state_path, {})
    lines = []
    ok, note = rs.ensure_ortools()
    lines.append("ortools ok=%s %s" % (ok, note[:100]))
    carry = 0.0
    if ok:
        for tag, secs in plan:
            if state.get(tag, {}).get("status") in ("FOUND", "INFEASIBLE", "BUG"):
                carry += secs
                continue
            wall = min(secs + carry, t_end - time.time() - 15)
            if wall < 30:
                lines.append("stop: no time for %s" % tag)
                break
            t1 = time.time()
            prev = state.get(tag, {})
            try:
                info = cegar_g(tag, time.time() + wall, workers=workers, prev=prev)
            except Exception as e:  # report, keep the other tiers going
                lines.append("ERROR %s %r" % (tag, e))
                continue
            carry = max(0.0, secs + carry - (time.time() - t1))
            info["iterations_total"] = info["iterations"] + prev.get("iterations_total", 0)
            info["seconds_total"] = info["seconds"] + prev.get("seconds_total", 0)
            state[tag] = info
            rs._save(state_path, state)
            if info["status"] == "FOUND":
                with open(os.path.join(cache, "cert_%s.json" % tag), "w", encoding="utf-8") as f:
                    json.dump(info["cert"], f)
    for tag in ORDER_G:
        r = state.get(tag)
        if not r:
            continue
        if r.get("status") == "FOUND":
            c = r.get("cert", {})
            lines.append("RULE %s n=%s sweep=%s endpoints=%s %s" % (
                tag, c.get("n"), c.get("sweep"), c.get("endpoints"), r.get("rule")))
        if r.get("status") == "BUG":
            lines.append("BUG %s %s" % (tag, r.get("stuck_on")))
        if r.get("why"):
            lines.append("WHY %s %s" % (tag, r["why"]))
    for tag in ORDER_G:
        if tag in state:
            lines.append(_line(tag, state[tag]))
    lines.append("STATUS " + " ".join("%s=%s" % (t, state[t].get("status"))
                                      for t in ORDER_G if t in state))
    return "\n".join(lines)


def job_main(argv=None):
    """Compete driver: every tier of ORDER_G in turn, report to --out-dir."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--minutes", type=float, default=180)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    per = 60.0 * a.minutes / len(ORDER_G)
    rep = probe_g([(t, per) for t in ORDER_G], budget=60.0 * a.minutes, workers=a.workers,
                  cache=os.path.join(a.out_dir, "cache"))
    with open(os.path.join(a.out_dir, "report_g.txt"), "w", encoding="utf-8") as f:
        f.write(rep + "\n")
    print(rep)
    return rep


if __name__ == "__main__":
    job_main()
