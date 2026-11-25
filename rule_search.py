# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Exact search (CP-SAT) for local shifted-Lonely-Runner rules with small largest speed L.

The criterion is the one in rules.py: every class (q, k) of every touched even speed q
must be covered for all z in [-1, 1] by rephased runners, added odd runners, or untouched
even runners <= L. A solver answer is only a candidate: job_rules.py re-checks every rule
with rules.local_check (exact, independent of this encoding) and then builds the full
configurations and re-checks them with both global checkers in slr.py.

Menu (a finite search space; a "no rule" answer is only about this menu):
  even speeds 2..L, odd speeds 1..A, shift sigma0 forced by the class it covers
  (sigma0 = -c k mod 1) with denominator in `dens` (None = any), tilt beta in `betas`.

Encoding. For each even w: bools rem_w, unt_w and one bool per rephase option; exactly one
is true. For each odd a: at most one option bool. For each (q, k) the z-line [-1, 1] is cut
at every interval endpoint; on each open segment the set of options whose closed interval
contains it is one clause (unt_q OR options...). Segments whose option set contains another
segment's set are dropped (implied). Gain sum(rem) - sum(added) >= min_gain.
"""
import time
from fractions import Fraction as F
from math import gcd

import rules


def halves(lo=-2, hi=2):
    return [F(j, 2) for j in range(2 * lo, 2 * hi + 1)]


def quarters(lo=-2, hi=2):
    return [F(j, 4) for j in range(4 * lo, 4 * hi + 1)]


def pair_clauses(q, k, evens, odds, betas, dens):
    """Clauses (lists of option keys) for class k of q. Key ('u', w) = untouched even w,
    ('e', w, s0, b) = rephased even, ('o', a, s0, b) = added odd."""
    ivs = []
    for kind, pool in (("e", evens), ("o", odds)):
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
    # drop supersets (implied clauses)
    ms = sorted(seen, key=lambda m: bin(m).count("1"))
    kept = []
    for m in ms:
        if any((x & m) == x for x in kept):
            continue
        kept.append(m)
    out = []
    for m in kept:
        keys = []
        i = 0
        while m:
            if m & 1:
                keys.append(ivs[i][2])
            m >>= 1
            i += 1
        out.append(keys)
    return out


def all_clauses(L, A, betas, dens, qs=None, lit_budget=None):
    evens = list(range(2, L + 1, 2))
    odds = list(range(1, A + 1, 2))
    cl = {}
    lits = 0
    for q in (qs if qs is not None else evens):
        for k in rules.responsible_classes(q):
            c = pair_clauses(q, k, evens, odds, betas, dens)
            cl[(q, k)] = c
            lits += sum(len(x) for x in c)
            if lit_budget is not None and lits > lit_budget:
                return None, lits
    return cl, lits


def clauses_satisfied(rule, clauses):
    """Does a rule satisfy every clause of its touched q? (encoding completeness check)"""
    removed, reph, added = rules._norm_rule(rule)
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


def solve(L, A, betas, dens, time_limit, workers=2, min_gain=1, lit_budget=4_000_000,
          log=print):
    from ortools.sat.python import cp_model

    t0 = time.time()
    clauses, lits = all_clauses(L, A, betas, dens, lit_budget=lit_budget)
    info = {"L": L, "A": A, "n_betas": len(betas),
            "dens": sorted(dens) if dens is not None else "any", "literals": lits}
    if clauses is None:
        info["status"] = "too-big"
        return None, info
    info["n_clauses"] = sum(len(c) for c in clauses.values())
    info["build_seconds"] = round(time.time() - t0, 1)

    m = cp_model.CpModel()
    evens = list(range(2, L + 1, 2))
    rem = {w: m.NewBoolVar("rem%d" % w) for w in evens}
    unt = {w: m.NewBoolVar("unt%d" % w) for w in evens}
    opt = {}

    def lit(key):
        if key[0] == "u":
            return unt[key[1]]
        if key not in opt:
            opt[key] = m.NewBoolVar("o%d" % len(opt))
        return opt[key]

    for (q, k), cls in clauses.items():
        for keys in cls:
            m.AddBoolOr([lit(key) for key in keys] + [unt[q]])
    by_even = {w: [] for w in evens}
    by_odd = {}
    for key, var in opt.items():
        if key[0] == "e":
            by_even[key[1]].append(var)
        else:
            by_odd.setdefault(key[1], []).append(var)
    for w in evens:
        m.Add(rem[w] + unt[w] + sum(by_even[w]) == 1)
    for a, vs in by_odd.items():
        m.Add(sum(vs) <= 1)
    added_vars = [v for vs in by_odd.values() for v in vs]
    g = sum(rem.values()) - sum(added_vars)
    m.Add(g >= min_gain)
    touched = sum(rem.values()) + sum(v for w in evens for v in by_even[w]) + sum(added_vars)
    m.Maximize(64 * g - touched)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit)
    try:
        solver.parameters.num_workers = int(workers)
    except (AttributeError, ValueError):
        solver.parameters.num_search_workers = int(workers)
    st = solver.Solve(m)
    info["status"] = solver.StatusName(st)
    info["solve_seconds"] = round(time.time() - t0, 1)
    info["n_option_vars"] = len(opt)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, info
    rule = {"removed": [w for w in evens if solver.Value(rem[w])],
            "rephased": {}, "added": {}}
    for key, var in opt.items():
        if solver.Value(var):
            if key[0] == "e":
                rule["rephased"][key[1]] = (key[2], key[3])
            else:
                rule["added"][key[1]] = (key[2], key[3])
    info["gain"] = rules.gain(rule)
    info["objective_optimal"] = st == cp_model.OPTIMAL
    log("L=%d A=%d status=%s gain=%s" % (L, A, info["status"], info["gain"]))
    return rule, info
