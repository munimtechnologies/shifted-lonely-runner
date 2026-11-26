# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 11 (PREREG_rules_c.md): local shifted-Lonely-Runner rules on bases of multiples of
m = 3, 4, 6, 12, decided by counterexample-guided clause generation (CEGAR).

The criterion and its proof are in rules_m.py: a rule of modulus m with gain g >= 1, largest
touched base speed L and untouched helpers <= L gives a counterexample to the shifted Lonely
Runner Conjecture for every n >= ceil(L/m) - g. The open range is 58 <= n <= 94 (2026-11-26).
Poliakova's rule (m = 2, L = 192) gives n >= 95. Exact searches for m = 2 (aadrianvv's structured
patch and tomdif's rule3/rule4, both in 1337isnot1337/solved-conjectures, results/shifted-lonely-
runner-counterexamples) found no gain-1 rule below L = 192 in their menus. Bases of multiples of
3, 4, 6 or 12 let the added runners sit at thirds, quarters and sixths of the base time scale,
which those searches did not allow.

Differences from rule_search_s.py (route 10):
  * every untouched base runner (a multiple of m up to L) counts as a helper, including the
    speeds that are not P-smooth. Route 10 dropped those, so its INFEASIBLE answers covered a
    smaller family than local_check allows. Here only the TOUCHED and ADDED speeds are P-smooth;
  * clauses are generated lazily: solve on the classes collected so far, check the candidate
    with rules_m.local_check (exact), add the clauses of the classes it fails, and repeat.
    Each new batch of clauses is violated by the last candidate, so the loop makes progress.
    It ends with a rule that passes local_check (found) or with CP-SAT INFEASIBLE on a subset
    of the menu's clauses. Every rule of the menu that passes local_check satisfies all the
    clauses, so INFEASIBLE on a subset means no rule of the menu exists (a proof for the finite
    menu only).
"""
import json
import os
import tempfile
import time
from fractions import Fraction as F

import rules_m
import rule_search_m
import rule_search_s as rs

NMAX = 94

DENS_A = frozenset({1, 2, 3, 4, 6})
DENS_B = frozenset({1, 2, 3, 4, 6, 8, 12})
P5 = (2, 3, 5)

# tag: (m, L, P, beta menu 'h' (halves on [-2, 2]) or 'q' (quarters), dens, expectation)
TIERS = {
    # sanity: Poliakova's rule exists at m = 2, L = 192 in the 3-smooth halves menu
    "c2chk": (2, 192, (2, 3), "h", DENS_A, "find"),
    # cross-check: tomdif's rule3 reports no gain-1 rule at L <= 190 for primes {2, 3} (m = 2)
    "c2neg": (2, 190, (2, 3), "h", DENS_A, "none?"),
    # threshold 58 (L = 59 m): would settle all of 58..94
    "c3A58": (3, 177, P5, "h", DENS_A, "search"),
    "c6A58": (6, 354, P5, "h", DENS_A, "search"),
    "c4A58": (4, 236, P5, "h", DENS_A, "search"),
    "c3B58": (3, 177, P5, "q", DENS_B, "search"),
    "c6B58": (6, 354, P5, "q", DENS_B, "search"),
    "c4B58": (4, 236, P5, "q", DENS_B, "search"),
    # threshold 94 (L = 95 m): any rule here beats Poliakova's n >= 95
    "c3A94": (3, 285, P5, "h", DENS_A, "search"),
    "c6A94": (6, 570, P5, "h", DENS_A, "search"),
    "c4A94": (4, 380, P5, "h", DENS_A, "search"),
    "c12A58": (12, 708, P5, "h", DENS_B, "search"),
}
ORDER = ["c2chk", "c3A58", "c6A58", "c4A58", "c2neg", "c3B58", "c6B58", "c4B58",
         "c3A94", "c6A94", "c4A94", "c12A58"]


def pools_c(m, L, P, A=None):
    """(touchable, fixed, added): P-smooth multiples of m up to L (may be removed or rephased),
    the other multiples of m up to L (always untouched helpers), and the P-smooth
    non-multiples of m up to A = 2 L + 1 (may be added)."""
    A = 2 * L + 1 if A is None else A
    touch = [w for w in range(m, L + 1, m) if rs.smooth(w, P)]
    fixed = [w for w in range(m, L + 1, m) if not rs.smooth(w, P)]
    added = [a for a in range(1, A + 1) if a % m and rs.smooth(a, P)]
    return touch, fixed, added


def class_clauses(q, k, touch, fixed, added, betas, dens):
    """Clauses for class k of the base speed q (q touched). Keys: ('u', w) untouched touchable
    base w, ('e', w, s0, b) rephased base w, ('o', a, s0, b) added a. Segments of [-1, 1]
    covered by a fixed helper (always present) need no clause. A clause with no keys means
    that a segment is covered by no option at all, so q cannot be touched."""
    ivs = []
    const = []
    for w in fixed:
        if w % q == 0:  # a helper covers class (q, k) only if q divides it (c integer, s0 = 0)
            c = w // q
            const.append((F(-1, c), F(1, c)))
    for kind, pool in (("e", touch), ("o", added)):
        for w in pool:
            c = F(w, q)
            s0 = (-c * k) % 1
            if kind == "e" and s0 == 0:
                lo, hi = -1 / c, 1 / c
                if hi > -1 and lo < 1:
                    ivs.append((max(lo, F(-1)), min(hi, F(1)), ("u", w)))
            if s0.denominator not in dens:
                continue
            for b in betas:
                if kind == "e" and s0 == 0 and b == 0:
                    continue
                lo = (-1 - b) / c
                hi = (1 - b) / c
                if hi <= -1 or lo >= 1:
                    continue
                ivs.append((max(lo, F(-1)), min(hi, F(1)), (kind, w, s0, b)))
    pts = sorted({F(-1), F(1)} | {x for lo, hi, _ in ivs for x in (lo, hi)}
                 | {x for lo, hi in const for x in (lo, hi) if -1 < x < 1})
    starts, ends = {}, {}
    for i, (lo, hi, _) in enumerate(ivs):
        starts.setdefault(lo, []).append(i)
        ends.setdefault(hi, []).append(i)
    cst, cen = {}, {}
    for lo, hi in const:
        cst[max(lo, F(-1))] = cst.get(max(lo, F(-1)), 0) + 1
        cen[min(hi, F(1))] = cen.get(min(hi, F(1)), 0) + 1
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
    ms = sorted(seen, key=lambda x: bin(x).count("1"))
    kept = []
    for x in ms:
        if any((y & x) == y for y in kept):
            continue
        kept.append(x)
    out = []
    for x in kept:
        keys = []
        i = 0
        while x:
            if x & 1:
                keys.append(ivs[i][2])
            x >>= 1
            i += 1
        out.append(keys)
    return out


def _spread(xs, n):
    if len(xs) <= n:
        return list(xs)
    step = len(xs) / float(n)
    return [xs[int(i * step)] for i in range(n)]


def build_and_solve(clauses, touch, min_gain, time_limit, workers, hint=None):
    """One CP-SAT call over the collected clauses. Returns (status, rule or None)."""
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
        if key[0] == "u":
            return unt[key[1]]
        if key not in opt:
            opt[key] = nb("o%d" % len(opt))
        return opt[key]

    for (q, k), cls in clauses.items():
        for keys in cls:
            bor([lit(key) for key in keys] + [unt[q]])
    by_base = {w: [] for w in touch}
    by_added = {}
    for key, var in opt.items():
        if key[0] == "e":
            by_base[key[1]].append(var)
        else:
            by_added.setdefault(key[1], []).append(var)
    for w in touch:
        add(rem[w] + unt[w] + sum(by_base[w]) == 1)
    for a, vs in by_added.items():
        add(sum(vs) <= 1)
    added_vars = [v for vs in by_added.values() for v in vs]
    add(sum(rem.values()) - sum(added_vars) >= min_gain)
    touched = sum(rem.values()) + sum(v for w in touch for v in by_base[w]) + sum(added_vars)
    _m(md, "minimize", "Minimize")(touched)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit)
    try:
        solver.parameters.num_workers = int(workers)
    except (AttributeError, ValueError):
        solver.parameters.num_search_workers = int(workers)
    st = _m(solver, "solve", "Solve")(md)
    name = _m(solver, "status_name", "StatusName")(st)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return name, None
    val = _m(solver, "value", "Value")
    m_rule = {"removed": [w for w in touch if val(rem[w])], "rephased": {}, "added": {}}
    for key, var in opt.items():
        if val(var):
            if key[0] == "e":
                m_rule["rephased"][key[1]] = (key[2], key[3])
            else:
                m_rule["added"][key[1]] = (key[2], key[3])
    return name, m_rule


def cegar(m, L, P, betas, dens, deadline, workers=6, min_gain=1, seed_classes=None,
          per_q=16, seed_per_q=4, it_time=20.0, log=None):
    """Decide whether the menu has a gain->=min_gain rule with local_check(rule, L) true.
    Returns info with status 'FOUND' (info['rule']), 'INFEASIBLE' (none in the menu),
    or 'UNKNOWN' (time ran out), and the classes collected (for resuming)."""
    t0 = time.time()
    touch, fixed, added = pools_c(m, L, P)
    info = {"m": m, "L": L, "P": list(P), "n_touch": len(touch), "n_fixed": len(fixed),
            "n_added": len(added), "n_betas": len(betas), "dens": sorted(dens)}
    clauses = {}
    lits = 0

    def add_class(q, k):
        nonlocal lits
        if (q, k) in clauses:
            return False
        c = class_clauses(q, k, touch, fixed, added, betas, dens)
        clauses[(q, k)] = c
        lits += sum(len(x) for x in c) + len(c)
        return True

    for q in touch:
        for k in _spread(rules_m.responsible_classes(q, m), seed_per_q):
            add_class(q, k)
    for qk in seed_classes or []:
        add_class(int(qk[0]), int(qk[1]))
    it = 0
    tl = it_time
    status = "UNKNOWN"
    while True:
        left = deadline - time.time()
        if left < 10:
            break
        it += 1
        st, cand = build_and_solve(clauses, touch, min_gain, min(tl, left - 5), workers)
        if st == "INFEASIBLE":
            status = "INFEASIBLE"
            break
        if cand is None:  # no solution within the time limit: give the solver more time
            tl = min(4 * tl, 600.0)
            if log:
                log("  it=%d %s, time limit now %.0fs" % (it, st, tl))
            continue
        rule = {"m": m, "removed": cand["removed"], "rephased": cand["rephased"],
                "added": cand["added"]}
        ok, fails = rules_m.local_check(rule, untouched_upto=L)
        if ok:
            status = "FOUND"
            info["rule"] = rules_m.rule_to_json(rule)
            info["gain"] = rules_m.gain(rule)
            info["threshold"] = rules_m.threshold(rule, untouched_upto=L)
            break
        if fails and not isinstance(fails[0], tuple):
            info["shape_problems"] = fails
            status = "BUG"
            break
        byq = {}
        for q, k, _z in fails:
            byq.setdefault(q, []).append(k)
        new = 0
        for q, ks in byq.items():
            for k in _spread(ks, per_q):
                new += add_class(q, k)
        if log and (it <= 3 or it % 10 == 0):
            log("  it=%d st=%s touched=%d fails=%d new=%d classes=%d lits=%d t=%.0f" % (
                it, st, len(rule["removed"]) + len(rule["rephased"]) + len(rule["added"]),
                len(fails), new, len(clauses), lits, time.time() - t0))
        if new == 0:  # cannot happen if the encoding is right: the candidate failed a class
            status = "BUG"  # whose clauses were already present
            info["stuck_on"] = [list(map(str, f)) for f in fails[:3]]
            break
    info.update({"status": status, "iterations": it, "n_classes": len(clauses),
                 "literals": lits, "seconds": round(time.time() - t0, 1),
                 "classes": sorted([list(x) for x in clauses])})
    return info


def run_tier(tag, deadline, workers=6, seed_classes=None, log=None):
    m, L, P, kind, dens, _exp = TIERS[tag]
    info = cegar(m, L, P, rs.betas_of(kind), dens, deadline, workers=workers,
                 seed_classes=seed_classes, log=log)
    info["tag"] = tag
    return info


def probe(tags, budget=540, workers=6, cache=None, nmax=NMAX, verbose=False):
    """Run the tiers in order (a decided tier is not run again; an UNKNOWN one resumes from
    its collected classes). The first rule with threshold <= 94 is then certified for every
    n from its threshold to nmax by the two global checkers of slr.py. Returns a report."""
    t_end = time.time() + budget
    cache = cache or os.path.join(tempfile.gettempdir(), "mv2-slr-rules-c1")
    os.makedirs(cache, exist_ok=True)
    rule_path = os.path.join(cache, "rule.json")
    cert_path = os.path.join(cache, "certs.json")
    state_path = os.path.join(cache, "tiers.json")
    lines = []
    state = rs._load(state_path, {})
    found = rs._load(rule_path, None)
    ok = False
    if found is None and tags:
        ok, note = rs.ensure_ortools()
        lines.append("ortools ok=%s %s" % (ok, note[:200]))
    elif found is not None:
        lines.append("cached rule from %s" % found["tag"])
    log = lines.append if verbose else None
    if ok:
        for tag in tags:
            if tag in state and state[tag]["status"] in ("FOUND", "INFEASIBLE", "BUG"):
                lines.append("%s done earlier: %s" % (tag, state[tag]["status"]))
                continue
            if found is not None:
                break
            if t_end - time.time() < 45:
                lines.append("stop: no time for %s" % tag)
                break
            seed = state.get(tag, {}).get("classes")
            info = run_tier(tag, t_end - 20, workers=workers, seed_classes=seed, log=log)
            prev = state.get(tag, {})
            info["iterations_total"] = info["iterations"] + prev.get("iterations_total", 0)
            info["seconds_total"] = info["seconds"] + prev.get("seconds_total", 0)
            state[tag] = info
            rs._save(state_path, state)
            lines.append("%s m=%d L=%d P=%s betas=%d dens=%s touch=%d fixed=%d add=%d st=%s "
                         "it=%d classes=%d lits=%d t=%ss" % (
                             tag, info["m"], info["L"], info["P"], info["n_betas"],
                             "".join(str(d) for d in info["dens"]), info["n_touch"],
                             info["n_fixed"], info["n_added"], info["status"],
                             info["iterations_total"], info["n_classes"], info["literals"],
                             round(info["seconds_total"])))
            if info["status"] == "BUG":
                lines.append("BUG %s %s" % (tag, info.get("stuck_on") or info.get("shape_problems")))
            if info["status"] == "FOUND":
                lines.append("RULE %s gain=%d thr=%d %s" % (tag, info["gain"], info["threshold"],
                                                          rs.fmt_rule(info["rule"])))
                if info["threshold"] <= NMAX and found is None:
                    found = {"tag": tag, "L": info["L"], "rule": info["rule"],
                             "threshold": info["threshold"]}
                    rs._save(rule_path, found)
    if found is not None:
        rule = rules_m.rule_from_json(found["rule"])
        certs = rs._load(cert_path, {})
        for n in range(found["threshold"], nmax + 1):
            if str(n) in certs:
                continue
            if t_end - time.time() < 25:
                break
            rec = rs.certify_n(rule, found["L"], n)
            certs[str(n)] = {k: rec[k] for k in ("ok", "endpoints", "sweep", "R_ok",
                                                  "distinct", "seconds", "N")}
            rs._save(cert_path, certs)
            with open(os.path.join(cache, "certificates.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
        good = [int(n) for n, r in certs.items() if r["ok"]]
        bad = [int(n) for n, r in certs.items() if not r["ok"]]
        lines.append("CERTIFIED n=%s FAILED=%s missing_58_94=%s" % (
            rs._ranges(good), rs._ranges(bad),
            rs._ranges([n for n in range(58, NMAX + 1) if n not in good])))
    return "\n".join(lines)
