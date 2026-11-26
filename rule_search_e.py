# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 11c (PREREG_rules_e.md): the route-11b rule search split into cubes by the largest
touched speed, with the mirror symmetry broken at that speed, the cubes solved in parallel.

Criterion and proof: rules_m.py. A rule of modulus m with gain g >= 1, touched base speeds <= L
and untouched helpers <= L gives counterexamples for every n >= L/m - g. Menus and tiers are
those of rule_search_c.py / rule_search_d.py (c2neg, c4A58, c6A58, c3A94, ...).

Route 11b (feasibility mode, one CP-SAT model per tier) left c4A58, c6A58 and the control
c2neg UNKNOWN: CP-SAT returned no candidate on models of 0.05 to 0.7 million literals.

1. Cubes. Every rule touches some base speed, so it has a largest touched speed T, which it
   either removes ('R') or rephases ('S'). Cube (T, R) adds unt[w] = 1 for every touchable
   w > T and rem[T] = 1; cube (T, S) adds unt[w] = 1 for w > T and rem[T] = unt[T] = 0. The
   clauses are those of the whole menu (rule_search_c.class_clauses with the full pools), so
   every clause collected in any cube is valid in every other. The menu has a rule iff some
   cube does; INFEASIBLE on every cube proves the menu has none.
2. Mirror. If a rule passes the local criterion, so does its mirror (every shift (s0, b)
   replaced by (-s0 mod 1, -b)): class k of q and point z map to class -k and point -z, and
   c(-k) - s0 = -(ck + s0), |c(-z) - b| = |cz + b|. The menus are closed under the mirror, and
   the mirror keeps T and its state. So in cube (T, S) the shift of T may be restricted to
   canonical options, (s0, b) <= (-s0 mod 1, -b) as pairs of fractions.
   Completeness with lazily collected clauses: let a rule pass local_check. Take it or its
   mirror, whichever has T canonical. It satisfies every clause of every class. If one of its
   options occurs in no collected clause, replace that rephase by a removal or drop that added
   speed: no satisfied clause is lost (the option was in none of them, and the escape literal
   unt[q] is false either way) and the gain does not fall. If T's own option was replaced, the
   result lies in cube (T, R); otherwise in cube (T, S). So INFEASIBLE in both cubes of every T
   still rules out every rule of the menu.
3. Frontier. If every cube with T <= T0 is INFEASIBLE, no rule of the menu has all its touched
   speeds <= T0. This is reported even when the tier is not decided.

The cubes of a tier run in a spawn pool (default 3 processes x 2 CP-SAT workers). Results and
collected classes are kept in a cache folder, so later probes resume.
"""
import json
import os
import sys
import tempfile
import time
import traceback
from fractions import Fraction as F

import rules_m
import rule_search_c as rc
import rule_search_d as rd
import rule_search_s as rs

NMAX = 94
TIERS_E = dict(rd.TIERS_D)
ORDER_E = ["c2neg", "c4A58", "c6A58", "c3A94", "c4A94", "c6A94", "c3B58", "c4B58", "c6B58",
           "c12A58", "c6chk"]
KINDS = ("R", "S")

# gate plans: (tag, wall seconds for the tier); a tier decided earlier passes its time on
PLAN_E1 = [("c2neg", 230), ("c4A58", 230)]
PLAN_E2 = [("c6A58", 470)]
PLAN_E3 = [("c3A94", 260), ("c4A94", 260)]
# sanity cubes (tag, T, kind, seconds): each holds the mirror of Poliakova's rule (scaled by 3
# for m = 6), so the cube search must end FOUND there with threshold 95
SANITY_E1 = [("c2chk", 192, "R", 50)]
SANITY_E2 = [("c6chk", 576, "R", 50)]


def mirror_opt(s0, b):
    return ((-F(s0)) % 1, -F(b))


def canonical(s0, b):
    """True iff the shift (s0, b) is not larger than its mirror (pairs of fractions)."""
    s0 = F(s0) % 1
    return (s0, F(b)) <= mirror_opt(s0, b)


def mirror_rule(rule):
    """The mirror of a rule (pure function)."""
    m, removed, reph, added = rules_m._norm_rule(rule)
    return {"m": m, "removed": list(removed),
            "rephased": {w: mirror_opt(s0, b) for w, (s0, b) in reph.items()},
            "added": {a: mirror_opt(s0, b) for a, (s0, b) in added.items()}}


def cube_of(rule):
    """(T, kind) of a rule: its largest touched speed and whether it is removed or rephased."""
    _, removed, reph, _ = rules_m._norm_rule(rule)
    T = max(list(removed) + list(reph))
    return T, ("R" if T in removed else "S")


def cubes_of(touch):
    return [(T, k) for T in sorted(touch) for k in KINDS]


def ckey(T, kind):
    return "%d%s" % (T, kind)


def frontier(touch, cube_status):
    """Largest T0 such that every cube with T <= T0 is INFEASIBLE (0 if none)."""
    best = 0
    for T in sorted(touch):
        if all(cube_status.get(ckey(T, k)) == "INFEASIBLE" for k in KINDS):
            best = T
        else:
            break
    return best


def tier_status(touch, cube_status):
    sts = [cube_status.get(ckey(T, k)) for T, k in cubes_of(touch)]
    if "FOUND" in sts:
        return "FOUND"
    if "BUG" in sts:
        return "BUG"
    if sts and all(s == "INFEASIBLE" for s in sts):
        return "INFEASIBLE"
    return "UNKNOWN"


def solve_e(clauses, touch, cube, min_gain, time_limit, workers, hint=None):
    """CP-SAT over the collected clauses inside one cube. Returns (status name, rule or None)."""
    from ortools.sat.python import cp_model
    _m = rs._m
    T, kind = cube
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
        if q > T:
            continue  # q is untouched in this cube: its clauses hold through unt[q]
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
        if w > T:
            add(unt[w] == 1)
    add(unt[T] == 0)
    add(rem[T] == (1 if kind == "R" else 0))
    if kind == "S":
        for key, var in opt.items():
            if key[0] == "e" and key[1] == T and not canonical(key[2], key[3]):
                add(var == 0)
    for a, vs in by_added.items():
        add(sum(vs) <= 1)
    added_vars = [v for vs in by_added.values() for v in vs]
    add(sum(rem.values()) - sum(added_vars) >= min_gain)
    if hint is not None:
        ah = _m(md, "add_hint", "AddHint")
        hr, hu, ho = rd.hint_values(hint, touch, list(opt))
        for w in touch:
            ah(rem[w], hr[w])
            ah(unt[w], hu[w])
        for key, var in opt.items():
            ah(var, ho[key])
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
    rule = {"removed": [w for w in touch if val(rem[w])], "rephased": {}, "added": {}}
    for key, var in opt.items():
        if val(var):
            if key[0] == "e":
                rule["rephased"][key[1]] = (key[2], key[3])
            else:
                rule["added"][key[1]] = (key[2], key[3])
    return name, rule


def cegar_e(m, L, P, betas, dens, cube, deadline, workers=2, min_gain=1, seed_classes=None,
            per_q=16, seed_per_q=4, top_classes=64, it_time=20.0):
    """Counterexample-guided search inside one cube. Status FOUND (info['rule'] passes
    local_check), INFEASIBLE (no rule of the menu in this cube), UNKNOWN or BUG."""
    t0 = time.time()
    T, kind = cube
    touch, fixed, added = rc.pools_c(m, L, P)
    info = {"m": m, "L": L, "T": T, "kind": kind, "status": "UNKNOWN", "iterations": 0,
            "classes": [], "seconds": 0.0}
    if T not in touch or deadline - time.time() < 12:
        info["status"] = "SKIPPED" if T in touch else "BUG"
        return info
    clauses = {}

    def add_class(q, k):
        if q > T or (q, k) in clauses:
            return False
        clauses[(q, k)] = rc.class_clauses(q, k, touch, fixed, added, betas, dens)
        return True

    for k in rc._spread(rules_m.responsible_classes(T, m), top_classes):
        add_class(T, k)
    for q in touch:
        if q < T:
            for k in rc._spread(rules_m.responsible_classes(q, m), seed_per_q):
                add_class(q, k)
    for qk in seed_classes or []:
        add_class(int(qk[0]), int(qk[1]))
    it = 0
    tl = it_time
    status = "UNKNOWN"
    hint = None
    while True:
        left = deadline - time.time()
        if left < 6:
            break
        it += 1
        st, cand = solve_e(clauses, touch, cube, min_gain, min(tl, left - 3), workers,
                           hint=hint)
        if st == "INFEASIBLE":
            status = "INFEASIBLE"
            break
        if cand is None:
            tl = min(4 * tl, 1200.0)
            continue
        rule = {"m": m, "removed": cand["removed"], "rephased": cand["rephased"],
                "added": cand["added"]}
        hint = rule
        ok, fails = rules_m.local_check(rule, untouched_upto=L)
        if ok:
            status = "FOUND"
            info["rule"] = rules_m.rule_to_json(rule)
            info["gain"] = rules_m.gain(rule)
            info["threshold"] = rules_m.threshold(rule, untouched_upto=L)
            break
        if fails and not isinstance(fails[0], tuple):
            info["shape_problems"] = [str(x) for x in fails]
            status = "BUG"
            break
        byq = {}
        for q, k, _z in fails:
            byq.setdefault(q, []).append(k)
        new = 0
        for q, ks in byq.items():
            for k in rc._spread(ks, per_q):
                new += add_class(q, k)
        if new == 0:
            status = "BUG"
            info["stuck_on"] = [list(map(str, f)) for f in fails[:3]]
            break
    info.update({"status": status, "iterations": it, "n_classes": len(clauses),
                 "seconds": round(time.time() - t0, 1),
                 "classes": sorted([list(x) for x in clauses])})
    return info


def run_cube(task):
    """Pool entry point. task = (tag, T, kind, cap, t_end, workers, seed, extra_path)."""
    tag, T, kind, cap, t_end, workers, seed, extra = task
    try:
        if extra and extra not in sys.path:
            sys.path.insert(0, extra)
        m, L, P, bk, dens, _exp = TIERS_E[tag]
        deadline = min(time.time() + cap, t_end)
        info = cegar_e(m, L, P, rs.betas_of(bk), dens, (T, kind), deadline, workers=workers,
                       seed_classes=seed)
    except Exception:  # reported, never counted as decided
        info = {"T": T, "kind": kind, "status": "ERROR", "classes": [], "iterations": 0,
                "seconds": 0.0, "error": traceback.format_exc()[-400:]}
    info["tag"] = tag
    return info


def _decided_before(tag, caches):
    for name, path in caches:
        st = rs._load(os.path.join(path, "tiers.json"), {}) if path else {}
        rec = st.get(tag, {})
        if rec.get("status") in ("FOUND", "INFEASIBLE", "BUG"):
            return name, rec
    return None, None


def _old_classes(tag, caches):
    out = set()
    for _name, path in caches:
        st = rs._load(os.path.join(path, "tiers.json"), {}) if path else {}
        for qk in st.get(tag, {}).get("classes", []) or []:
            out.add((int(qk[0]), int(qk[1])))
    return out


def run_tier_e(tag, wall, state, nproc=3, workers=2, first_cap=90.0, extra_path=None,
               log=None):
    """Work on the open cubes of one tier for `wall` seconds. Updates state[tag]."""
    import multiprocessing as mp
    t_end = time.time() + wall
    m, L, P, bk, dens, _exp = TIERS_E[tag]
    touch, _fixed, _added = rc.pools_c(m, L, P)
    rec = state.setdefault(tag, {"cubes": {}, "pool": []})
    cubes = rec["cubes"]
    pool_cls = set((int(a), int(b)) for a, b in rec.get("pool", []))
    todo = [(T, k) for T, k in cubes_of(touch)
            if cubes.get(ckey(T, k), {}).get("status") not in ("INFEASIBLE", "FOUND", "BUG")]
    todo.sort(key=lambda c: (cubes.get(ckey(*c), {}).get("seconds_total", 0), c[0]))
    tasks = []
    for T, k in todo:
        prev = cubes.get(ckey(T, k), {}).get("seconds_total", 0)
        cap = max(first_cap, 2.0 * prev)
        seed = sorted(x for x in pool_cls if x[0] <= T)
        tasks.append((tag, T, k, cap, t_end, workers, seed, extra_path))
    ctx = mp.get_context("spawn")
    pool = ctx.Pool(processes=max(1, nproc))
    try:
        handles = [pool.apply_async(run_cube, (t,)) for t in tasks]
        for h in handles:
            try:
                info = h.get(timeout=max(0.5, t_end + 12 - time.time()))
            except Exception as e:  # a cube still running at the end: it stays open
                if log:
                    log("  pool: %r" % (e,))
                continue
            key = ckey(info["T"], info["kind"])
            old = cubes.get(key, {})
            if info["status"] == "SKIPPED":
                continue
            for qk in info.get("classes", []):
                pool_cls.add((int(qk[0]), int(qk[1])))
            cubes[key] = {
                "status": "UNKNOWN" if info["status"] == "ERROR" else info["status"],
                "iterations_total": old.get("iterations_total", 0) + info.get("iterations", 0),
                "seconds_total": round(old.get("seconds_total", 0) + info.get("seconds", 0), 1),
                "n_classes": info.get("n_classes", 0)}
            for extra in ("rule", "gain", "threshold", "stuck_on", "shape_problems", "error"):
                if extra in info:
                    cubes[key][extra] = info[extra]
            rec["pool"] = sorted([list(x) for x in pool_cls])
            if info["status"] in ("FOUND", "BUG", "ERROR") and log:
                log("  cube %s %s %s" % (key, info["status"],
                                         info.get("error", "")[-200:].replace("\n", " ")))
            if info["status"] == "FOUND":
                break
    finally:
        pool.terminate()
        pool.join()
    cst = {k: v.get("status") for k, v in cubes.items()}
    rec["status"] = tier_status(touch, cst)
    rec["frontier"] = frontier(touch, cst)
    rec["n_cubes"] = 2 * len(touch)
    rec["n_infeasible"] = sum(1 for v in cst.values() if v == "INFEASIBLE")
    rec["open"] = [ckey(T, k) for T, k in cubes_of(touch)
                   if cst.get(ckey(T, k)) != "INFEASIBLE"]
    rec["m"], rec["L"] = m, L
    return rec


def _tier_line(tag, rec):
    sec = sum(c.get("seconds_total", 0) for c in rec.get("cubes", {}).values())
    op = rec.get("open", [])
    return ("%s m=%s L=%s st=%s cubes=%s/%s infeasible frontier=%s open=%s%s t=%.0fs" % (
        tag, rec.get("m"), rec.get("L"), rec.get("status"), rec.get("n_infeasible"),
        rec.get("n_cubes"), rec.get("frontier"), ",".join(op[:12]),
        "..(+%d)" % (len(op) - 12) if len(op) > 12 else "", sec))


def sanity_e(checks, workers=6):
    """Run single sanity cubes in this process. Returns report lines."""
    out = []
    for tag, T, kind, secs in checks:
        m, L, P, bk, dens, _exp = TIERS_E[tag]
        info = cegar_e(m, L, P, rs.betas_of(bk), dens, (T, kind), time.time() + secs,
                       workers=workers)
        out.append("SANITY %s %s st=%s thr=%s it=%s t=%ss" % (
            tag, ckey(T, kind), info["status"], info.get("threshold"), info["iterations"],
            info["seconds"]))
    return out


def probe_e(plan, budget=530, nproc=3, workers=2, cache=None, d_cache=None, c_cache=None,
            nmax=NMAX, first_cap=90.0, sanity=None):
    """Run the sanity cubes, then the (tag, seconds) plan. Report: details first, summary
    lines last."""
    t_end = time.time() + budget
    tmp = tempfile.gettempdir()
    cache = cache or os.path.join(tmp, "mv2-slr-rules-e1")
    d_cache = os.path.join(tmp, "mv2-slr-rules-d1") if d_cache is None else d_cache
    c_cache = os.path.join(tmp, "mv2-slr-rules-c1") if c_cache is None else c_cache
    os.makedirs(cache, exist_ok=True)
    state_path = os.path.join(cache, "tiers.json")
    rule_path = os.path.join(cache, "rule.json")
    state = rs._load(state_path, {})
    found = rs._load(rule_path, None)
    olds = [("11b", d_cache), ("11", c_cache)]
    vlog, lines = [], []
    ok = False
    if plan and found is None:
        ok, note = rs.ensure_ortools()
        lines.append("ortools ok=%s %s" % (ok, note[:100]))
    extra = os.path.join(tmp, "mv2-ortools")
    carry = 0.0
    sanity_lines = sanity_e(sanity) if (ok and sanity) else []
    if ok:
        for tag, secs in plan:
            src, old = _decided_before(tag, olds)
            if old is not None:
                lines.append("%s decided earlier (route %s): %s" % (tag, src, old["status"]))
                carry += secs
                continue
            if state.get(tag, {}).get("status") in ("FOUND", "INFEASIBLE", "BUG"):
                carry += secs
                continue
            if found is not None:
                break
            wall = min(secs + carry, t_end - time.time() - 20)
            carry = 0.0
            if wall < 40:
                lines.append("stop: no time for %s" % tag)
                break
            rec = state.setdefault(tag, {"cubes": {}, "pool": []})
            if not rec.get("pool"):
                rec["pool"] = sorted([list(x) for x in _old_classes(tag, olds)])
            run_tier_e(tag, wall, state, nproc=nproc, workers=workers, first_cap=first_cap,
                       extra_path=extra, log=vlog.append)
            rs._save(state_path, state)
            for key, c in sorted(state[tag]["cubes"].items()):
                if c.get("status") == "FOUND":
                    rule = rules_m.rule_from_json(c["rule"])
                    ok2, _f = rules_m.local_check(rule, untouched_upto=TIERS_E[tag][1])
                    thr = rules_m.threshold(rule, untouched_upto=TIERS_E[tag][1])
                    lines.append("RULE %s cube %s recheck=%s gain=%d thr=%d %s" % (
                        tag, key, ok2, rules_m.gain(rule), thr, rs.fmt_rule(c["rule"])))
                    if ok2 and thr <= nmax and found is None:
                        found = {"tag": tag, "L": TIERS_E[tag][1], "rule": c["rule"],
                                 "threshold": thr}
                        rs._save(rule_path, found)
    if found is not None:
        lines.append("rule from %s thr=%d" % (found["tag"], found["threshold"]))
        lines.append(rd.certify(found, cache, t_end, nmax))
    for tag in ORDER_E:
        if tag in state and "cubes" in state[tag]:
            lines.append(_tier_line(tag, state[tag]))
    dst = rs._load(os.path.join(d_cache, "tiers.json"), {}) if d_cache else {}
    if dst:
        lines.append("11b " + " ".join("%s=%s/%s/%ss" % (
            t, r.get("status"), r.get("iterations_total"), round(r.get("seconds_total", 0)))
            for t, r in sorted(dst.items())))
    lines += sanity_lines
    lines.append("STATUS " + " ".join("%s=%s" % (t, state[t].get("status"))
                                      for t in ORDER_E if t in state))
    return "\n".join(vlog[-8:] + lines)
