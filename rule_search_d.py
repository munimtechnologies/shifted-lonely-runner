# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 11b (PREREG_rules_d.md): the route-11 search (rule_search_c.py) with three changes.

Route 11 decided c2chk (FOUND, Poliakova's rule) and c3A58 (INFEASIBLE: no gain-1 rule with
threshold 58 on the base of multiples of 3 in menu A), but c6A58 stayed UNKNOWN for 816 s:
CP-SAT, asked to minimise the number of touched speeds, returned no candidate at all.

  1. Feasibility mode. The model has the same clauses and the same constraints (one state per
     touchable base speed, at most one shift per added speed, gain >= 1) but no objective, and
     the last candidate is given to CP-SAT as a hint. Any rule of gain >= 1 is as good as any
     other for the threshold, so the objective was never needed. INFEASIBLE still proves that
     the finite menu has no rule (the clauses of a subset of classes are necessary conditions).
  2. A time cap per tier and per probe, so one hard tier no longer takes every probe.
  3. A sanity tier for modulus 6: c6chk = Poliakova's rule scaled by 3 (m = 6, L = 576, primes
     {2, 3}) lies in its menu, so the search must end FOUND there. It checks the m = 6
     encoding and solver path the way c2chk checked m = 2.

Tier states are kept in a cache folder. A tier that route 11 already decided in the same cache
area (%TEMP%/mv2-slr-rules-c1/tiers.json) is reported as decided; an UNKNOWN one resumes from
the classes route 11 collected (any collected class gives valid necessary clauses).
"""
import json
import os
import tempfile
import time

import rules_m
import rule_search_c as rc
import rule_search_s as rs

NMAX = 94

TIERS_D = dict(rc.TIERS)
# sanity for m = 6: Poliakova's rule scaled by 3 (touched 24..576, added 9 and 27) is in menu A
TIERS_D["c6chk"] = (6, 576, (2, 3), "h", rc.DENS_A, "find")

ORDER_D = ["c6chk", "c4A58", "c2neg", "c3A94", "c6A58", "c4A94", "c6A94", "c3B58", "c4B58",
           "c6B58", "c12A58"]

# per-probe plans for the publish gate (tag, cap in seconds); 530 s per probe in total
PLAN_D1 = [("c6chk", 170), ("c4A58", 200), ("c2neg", 140)]
PLAN_D2 = [("c6A58", 500)]
PLAN_D3 = [("c3A94", 230), ("c4A94", 230), ("c4A58", 60)]


def hint_values(cand, touch, opt_keys):
    """0/1 hint for every variable of the model from a candidate rule (pure function).
    Returns (rem, unt, opt) dicts: rem[w], unt[w] for touchable w, opt[key] for option keys."""
    removed = set(cand.get("removed", []))
    reph = cand.get("rephased", {})
    added = cand.get("added", {})
    rem = {w: int(w in removed) for w in touch}
    unt = {w: int(w not in removed and w not in reph) for w in touch}
    opt = {}
    for key in opt_keys:
        if key[0] == "e":
            opt[key] = int(tuple(reph.get(key[1], ())) == (key[2], key[3]))
        else:
            opt[key] = int(tuple(added.get(key[1], ())) == (key[2], key[3]))
    return rem, unt, opt


def solve_d(clauses, touch, min_gain, time_limit, workers, hint=None, objective=False):
    """One CP-SAT call over the collected clauses. Returns (status name, rule or None)."""
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
    if objective:
        touched = (sum(rem.values()) + sum(v for w in touch for v in by_base[w])
                   + sum(added_vars))
        _m(md, "minimize", "Minimize")(touched)
    if hint is not None:
        ah = _m(md, "add_hint", "AddHint")
        hr, hu, ho = hint_values(hint, touch, list(opt))
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


def cegar_d(m, L, P, betas, dens, deadline, workers=6, min_gain=1, seed_classes=None,
            per_q=16, seed_per_q=4, it_time=30.0, objective=False, log=None):
    """Counterexample-guided search as rc.cegar, in feasibility mode with hints.
    Status FOUND (info['rule'] passes local_check), INFEASIBLE (no rule in the menu),
    UNKNOWN (time ran out) or BUG (encoding error)."""
    t0 = time.time()
    touch, fixed, added = rc.pools_c(m, L, P)
    info = {"m": m, "L": L, "P": list(P), "n_touch": len(touch), "n_fixed": len(fixed),
            "n_added": len(added), "n_betas": len(betas), "dens": sorted(dens),
            "mode": "opt" if objective else "feas"}
    clauses = {}
    lits = 0

    def add_class(q, k):
        nonlocal lits
        if (q, k) in clauses:
            return False
        c = rc.class_clauses(q, k, touch, fixed, added, betas, dens)
        clauses[(q, k)] = c
        lits += sum(len(x) for x in c) + len(c)
        return True

    for q in touch:
        for k in rc._spread(rules_m.responsible_classes(q, m), seed_per_q):
            add_class(q, k)
    for qk in seed_classes or []:
        q, k = int(qk[0]), int(qk[1])
        if q in touch:
            add_class(q, k)
    it = 0
    tl = it_time
    status = "UNKNOWN"
    hint = None
    last_touched = None
    while True:
        left = deadline - time.time()
        if left < 8:
            break
        it += 1
        st, cand = solve_d(clauses, touch, min_gain, min(tl, left - 4), workers, hint=hint,
                           objective=objective)
        if st == "INFEASIBLE":
            status = "INFEASIBLE"
            break
        if cand is None:
            tl = min(4 * tl, 1200.0)
            if log:
                log("  %s it=%d %s classes=%d lits=%d t=%.0f" % (
                    info.get("tag", ""), it, st, len(clauses), lits, time.time() - t0))
            continue
        rule = {"m": m, "removed": cand["removed"], "rephased": cand["rephased"],
                "added": cand["added"]}
        hint = rule
        last_touched = len(rule["removed"]) + len(rule["rephased"]) + len(rule["added"])
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
            for k in rc._spread(ks, per_q):
                new += add_class(q, k)
        if log and (it <= 2 or it % 10 == 0):
            log("  it=%d touched=%d fails=%d new=%d classes=%d t=%.0f" % (
                it, last_touched, len(fails), new, len(clauses), time.time() - t0))
        if new == 0:
            status = "BUG"
            info["stuck_on"] = [list(map(str, f)) for f in fails[:3]]
            break
    info.update({"status": status, "iterations": it, "n_classes": len(clauses),
                 "literals": lits, "seconds": round(time.time() - t0, 1),
                 "last_touched": last_touched,
                 "classes": sorted([list(x) for x in clauses])})
    return info


def seed_state(state, c_state):
    """Copy route-11 results into an empty route-11b state: decided tiers keep their status
    (marked from_c), UNKNOWN tiers pass on their collected classes. Returns the state."""
    for tag, rec in (c_state or {}).items():
        if tag in state or tag not in TIERS_D:
            continue
        if rec.get("status") in ("FOUND", "INFEASIBLE", "BUG"):
            keep = {k: rec[k] for k in rec if k != "classes"}
            keep["from_c"] = True
            state[tag] = keep
        else:
            state[tag] = {"status": "UNKNOWN", "classes": rec.get("classes", []),
                          "iterations_total": rec.get("iterations_total", 0),
                          "seconds_total": rec.get("seconds_total", 0), "from_c": True}
    return state


def _summary(tag, info):
    return ("%s m=%d L=%d P=%s mode=%s touch=%d fixed=%d add=%d st=%s it=%d classes=%d "
            "lits=%d last=%s t=%ss" % (
                tag, info["m"], info["L"], "".join(str(p) for p in info["P"]), info["mode"],
                info["n_touch"], info["n_fixed"], info["n_added"], info["status"],
                info["iterations_total"], info["n_classes"], info["literals"],
                info.get("last_touched"), round(info["seconds_total"])))


def certify(found, cache, t_end, nmax=NMAX):
    """Certify every n from the rule's threshold to nmax with both global checkers."""
    rule = rules_m.rule_from_json(found["rule"])
    cert_path = os.path.join(cache, "certs.json")
    certs = rs._load(cert_path, {})
    for n in range(found["threshold"], nmax + 1):
        if str(n) in certs:
            continue
        if t_end - time.time() < 25:
            break
        rec = rs.certify_n(rule, found["L"], n)
        certs[str(n)] = {k: rec[k] for k in ("ok", "endpoints", "sweep", "R_ok", "distinct",
                                              "seconds", "N")}
        rs._save(cert_path, certs)
        with open(os.path.join(cache, "certificates.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    good = [int(n) for n, r in certs.items() if r["ok"]]
    bad = [int(n) for n, r in certs.items() if not r["ok"]]
    return "CERTIFIED n=%s FAILED=%s missing_58_94=%s" % (
        rs._ranges(good), rs._ranges(bad),
        rs._ranges([n for n in range(58, NMAX + 1) if n not in good]))


def probe_d(plan, budget=530, workers=6, cache=None, c_cache=None, nmax=NMAX, verbose=True,
            objective=False):
    """Run the (tag, cap) plan in order. Returns the report: the verbose log first and the
    summary last, so that a short output tail still shows the summary."""
    t_end = time.time() + budget
    cache = cache or os.path.join(tempfile.gettempdir(), "mv2-slr-rules-d1")
    if c_cache is None:
        c_cache = os.path.join(tempfile.gettempdir(), "mv2-slr-rules-c1")
    os.makedirs(cache, exist_ok=True)
    state_path = os.path.join(cache, "tiers.json")
    rule_path = os.path.join(cache, "rule.json")
    state = rs._load(state_path, {})
    state = seed_state(state, rs._load(os.path.join(c_cache, "tiers.json"), {}) if c_cache
                       else {})
    rs._save(state_path, state)
    found = rs._load(rule_path, None)
    vlog, lines = [], []
    ok = False
    if plan and found is None:
        ok, note = rs.ensure_ortools()
        lines.append("ortools ok=%s %s" % (ok, note[:120]))
    if ok:
        for tag, cap in plan:
            rec = state.get(tag, {})
            if rec.get("status") in ("FOUND", "INFEASIBLE", "BUG"):
                lines.append("%s decided earlier: %s%s" % (tag, rec["status"],
                                                          " (route 11)" if rec.get("from_c")
                                                          else ""))
                continue
            if found is not None:
                break
            left = t_end - time.time()
            if left < 40:
                lines.append("stop: no time for %s" % tag)
                break
            m, L, P, kind, dens, _exp = TIERS_D[tag]
            deadline = time.time() + min(cap, left - 15)
            info = cegar_d(m, L, P, rs.betas_of(kind), dens, deadline, workers=workers,
                           seed_classes=rec.get("classes"), objective=objective,
                           log=vlog.append if verbose else None)
            info["tag"] = tag
            info["iterations_total"] = info["iterations"] + rec.get("iterations_total", 0)
            info["seconds_total"] = info["seconds"] + rec.get("seconds_total", 0)
            state[tag] = info
            rs._save(state_path, state)
            lines.append(_summary(tag, info))
            if info["status"] == "BUG":
                lines.append("BUG %s %s" % (tag, info.get("stuck_on") or
                                            info.get("shape_problems")))
            if info["status"] == "FOUND":
                lines.append("RULE %s gain=%d thr=%d %s" % (
                    tag, info["gain"], info["threshold"], rs.fmt_rule(info["rule"])))
                if info["threshold"] <= nmax and found is None:
                    found = {"tag": tag, "L": info["L"], "rule": info["rule"],
                             "threshold": info["threshold"]}
                    rs._save(rule_path, found)
    if found is not None:
        lines.append("rule from %s thr=%d" % (found["tag"], found["threshold"]))
        lines.append(certify(found, cache, t_end, nmax))
    lines.append("STATUS " + " ".join("%s=%s" % (t, state[t]["status"]) for t in ORDER_D + [
        "c2chk", "c3A58"] if t in state))
    return "\n".join(vlog[-14:] + lines)
