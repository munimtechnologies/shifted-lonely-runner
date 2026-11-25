# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Exact search (CP-SAT) for local shifted-Lonely-Runner rules on a base of multiples of m.

Same encoding as rule_search.py (which is the case m = 2), with base speeds m, 2m, ..., L and
added speeds 1..A that are not multiples of m. The criterion is the one in rules_m.py. A
solver answer is only a candidate: job_rules_m.py re-checks it with rules_m.local_check
(exact, independent of this encoding) and then re-checks full configurations with both
global checkers of slr.py.

Menu (finite; a "no rule" answer is only about this menu): sigma0 is forced by the class it
covers (sigma0 = -c k mod 1) and must have a denominator in `dens`; beta is taken from `betas`.

Encoding. For each base w: bools rem_w, unt_w and one bool per rephase option; exactly one is
true. For each added a: at most one option. For each class (q, k) the z-line [-1, 1] is cut at
every interval endpoint; on each open segment the options whose closed interval contains it
form one clause (unt_q OR options...). Clauses that contain another clause are dropped.
Gain sum(rem) - sum(added) >= min_gain; objective 64 * gain - (number of touched speeds).
"""
import time
from fractions import Fraction as F

import rules_m


def halves(lo=-2, hi=2):
    return [F(j, 2) for j in range(2 * lo, 2 * hi + 1)]


def quarters(lo=-2, hi=2):
    return [F(j, 4) for j in range(4 * lo, 4 * hi + 1)]


def pools(L, A, m):
    base = list(range(m, L + 1, m))
    added = [a for a in range(1, A + 1) if a % m]
    return base, added


def pair_clauses(q, k, base, added, betas, dens):
    """Clauses (lists of option keys) for class k of q. Key ('u', w) = untouched base w,
    ('e', w, s0, b) = rephased base, ('o', a, s0, b) = added."""
    ivs = []
    for kind, pool in (("e", base), ("o", added)):
        for w in pool:
            c = F(w, q)
            s0 = (-c * k) % 1
            if dens is not None and s0.denominator not in dens:
                continue
            for b in betas:
                lo = (-1 - b) / c
                hi = (1 - b) / c
                if hi <= -1 or lo >= 1:
                    continue  # meets [-1, 1] in at most one point: covers no segment
                if kind == "e" and s0 == 0 and b == 0:
                    key = ("u", w)
                else:
                    key = (kind, w, s0, b)
                ivs.append((max(lo, F(-1)), min(hi, F(1)), key))
    pts = sorted({F(-1), F(1)} | {x for lo, hi, _ in ivs for x in (lo, hi)})
    starts, ends = {}, {}
    for i, (lo, hi, _) in enumerate(ivs):
        starts.setdefault(lo, []).append(i)
        ends.setdefault(hi, []).append(i)
    mask = 0
    seen = set()
    for j in range(len(pts) - 1):
        p = pts[j]
        for i in ends.get(p, ()):
            mask &= ~(1 << i)
        for i in starts.get(p, ()):
            mask |= 1 << i
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


def all_clauses(L, A, m, betas, dens, qs=None, lit_budget=None):
    base, added = pools(L, A, m)
    cl = {}
    lits = 0
    for q in (qs if qs is not None else base):
        for k in rules_m.responsible_classes(q, m):
            c = pair_clauses(q, k, base, added, betas, dens)
            cl[(q, k)] = c
            lits += sum(len(x) for x in c)
            if lit_budget is not None and lits > lit_budget:
                return None, lits
    return cl, lits


def clauses_satisfied(rule, clauses):
    """Classes (q, k) of touched q with a clause the rule does not satisfy (encoding check)."""
    _, removed, reph, added = rules_m._norm_rule(rule)
    X = set(removed) | set(reph)
    true_keys = set()
    for w, (s0, b) in reph.items():
        true_keys.add(("e", w, s0, b))
    for a, (s0, b) in added.items():
        true_keys.add(("o", a, s0, b))
    bad = []
    for (q, k), cls in clauses.items():
        if q not in X:
            continue
        for keys in cls:
            ok = False
            for key in keys:
                if key[0] == "u":
                    if key[1] not in X:
                        ok = True
                        break
                elif key in true_keys:
                    ok = True
                    break
            if not ok:
                bad.append((q, k))
                break
    return bad


def solve(L, A, m, betas, dens, time_limit, workers=2, min_gain=1, lit_budget=3_000_000,
          log=print):
    from ortools.sat.python import cp_model

    t0 = time.time()
    clauses, lits = all_clauses(L, A, m, betas, dens, lit_budget=lit_budget)
    info = {"m": m, "L": L, "rho": F(L, m).__str__(), "A": A, "n_betas": len(betas),
            "dens": sorted(dens) if dens is not None else "any", "literals": lits}
    if clauses is None:
        info["status"] = "too-big"
        info["build_seconds"] = round(time.time() - t0, 1)
        return None, info
    info["n_clauses"] = sum(len(c) for c in clauses.values())
    info["build_seconds"] = round(time.time() - t0, 1)

    md = cp_model.CpModel()
    base, _ = pools(L, A, m)
    rem = {w: md.NewBoolVar("rem%d" % w) for w in base}
    unt = {w: md.NewBoolVar("unt%d" % w) for w in base}
    opt = {}

    def lit(key):
        if key[0] == "u":
            return unt[key[1]]
        if key not in opt:
            opt[key] = md.NewBoolVar("o%d" % len(opt))
        return opt[key]

    for (q, k), cls in clauses.items():
        for keys in cls:
            md.AddBoolOr([lit(key) for key in keys] + [unt[q]])
    by_base = {w: [] for w in base}
    by_added = {}
    for key, var in opt.items():
        if key[0] == "e":
            by_base[key[1]].append(var)
        else:
            by_added.setdefault(key[1], []).append(var)
    for w in base:
        md.Add(rem[w] + unt[w] + sum(by_base[w]) == 1)
    for a, vs in by_added.items():
        md.Add(sum(vs) <= 1)
    added_vars = [v for vs in by_added.values() for v in vs]
    g = sum(rem.values()) - sum(added_vars)
    md.Add(g >= min_gain)
    touched = sum(rem.values()) + sum(v for w in base for v in by_base[w]) + sum(added_vars)
    md.Maximize(64 * g - touched)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit)
    try:
        solver.parameters.num_workers = int(workers)
    except (AttributeError, ValueError):
        solver.parameters.num_search_workers = int(workers)
    st = solver.Solve(md)
    info["status"] = solver.StatusName(st)
    info["solve_seconds"] = round(time.time() - t0, 1)
    info["n_option_vars"] = len(opt)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, info
    rule = {"m": m, "removed": [w for w in base if solver.Value(rem[w])],
            "rephased": {}, "added": {}}
    for key, var in opt.items():
        if solver.Value(var):
            if key[0] == "e":
                rule["rephased"][key[1]] = (key[2], key[3])
            else:
                rule["added"][key[1]] = (key[2], key[3])
    info["gain"] = rules_m.gain(rule)
    info["objective_optimal"] = st == cp_model.OPTIMAL
    log("m=%d L=%d status=%s gain=%s" % (m, L, info["status"], info["gain"]))
    return rule, info
