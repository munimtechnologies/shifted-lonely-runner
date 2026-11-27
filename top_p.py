# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 19b (PREREG_rules_p.md): route 19 (top_o.py) with a feasibility-only solver.

Route 19's gate probes O1 and O2 re-found a gain-1 rule at N = 96 (menu h) and at N = 64 (menus
x and h) but decided none of its 37 targets: they got one to three CEGAR iterations each. The
reason is in rule_search_c.build_and_solve: every call MINIMISES the number of touched speeds,
so CP-SAT keeps searching until its time limit (20-45 s) even after it has a candidate, and a
45 s turn holds about two iterations. A CEGAR only needs some candidate, or a proof that none
exists. `solve_feas` builds exactly the same model without the objective, so CP-SAT returns at
its first solution, and INFEASIBLE means the same as before (no rule of gain >= g in the finite
menu satisfies the collected clauses, hence none passes `top_o.fixed_check`).

Everything else is top_o's: the exact fixed-N closed-cover criterion `fixed_check` at the slack
radius, the clauses `class_clauses_o`, the menus, the tiers, and `certify` (both global exact
checkers of slr.py at R = 1/(n+1)). Collected classes from route 19's cache (%TEMP%/mv2-slr-o1)
seed each target: a class's clauses depend only on (N, g, menu), so they stay valid.
"""
import json
import os
import tempfile
import time

import rules_m
import rule_search_s as rs
import top_o as to

SANITY = {"pf64x": "f64x", "ph64": "h64"}  # re-found from scratch with the new solver
TARGETS = ["x64g2", "x72", "x81"] + ["x%d" % N for N in range(59, 96) if N not in (64, 72, 81)]
ORDER = list(SANITY) + TARGETS


def tier(tag):
    """(N, g, P, beta kind, dens) of a tag (sanity tags reuse their route-19 tier)."""
    N, g, P, kind, dens, _cap = to.TIERS[SANITY.get(tag, tag)]
    return N, g, P, kind, dens


def solve_feas(clauses, touch, min_gain, time_limit, workers):
    """rule_search_c.build_and_solve without the objective. Returns (status name, rule|None).
    Model: for each touchable w exactly one of removed / untouched / one rephasing; each added
    speed at most one shift; removed - added >= min_gain; every clause (keys of a class, or q
    untouched) holds."""
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

    for (q, _k), cls in clauses.items():
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
    for _a, vs in by_added.items():
        add(sum(vs) <= 1)
    added_vars = [v for vs in by_added.values() for v in vs]
    add(sum(rem.values()) - sum(added_vars) >= min_gain)
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
    rule = {"m": 2, "removed": [w for w in touch if val(rem[w])], "rephased": {}, "added": {}}
    for key, var in opt.items():
        if val(var):
            if key[0] == "e":
                rule["rephased"][key[1]] = (key[2], key[3])
            else:
                rule["added"][key[1]] = (key[2], key[3])
    return name, rule


def cegar_p(N, g, P, kind, dens, deadline, workers=8, seed_classes=None, per_q=16,
            seed_per_q=3):
    """top_o.cegar_o with solve_feas. Status FOUND (info['rule']), INFEASIBLE, UNKNOWN or BUG."""
    t0 = time.time()
    rho = to.rho_of(N, g)
    touch, fixed, added = to.pools_o(N, P)
    s0s = to.s0_menu(dens)
    betas = to.betas_of(kind)
    clauses = {}

    def add_class(q, k):
        if (q, k) in clauses:
            return False
        clauses[(q, k)] = to.class_clauses_o(q, k, N, rho, touch, fixed, added, s0s, betas)
        return True

    for q in touch:
        for k in to._spread(rules_m.responsible_classes(q, 2), seed_per_q):
            add_class(q, k)
    for qk in seed_classes or []:
        add_class(int(qk[0]), int(qk[1]))
    it = 0
    solve_s = 0.0
    status = "UNKNOWN"
    info = {}
    while True:
        left = deadline - time.time()
        if left < 6:
            break
        it += 1
        ts = time.time()
        st, cand = solve_feas(clauses, touch, g, left - 3, workers)
        solve_s += time.time() - ts
        if st == "INFEASIBLE":
            status = "INFEASIBLE"
            break
        if cand is None:
            break  # time ran out inside the solver
        ok, fails = to.fixed_check(cand, N, g=g, rho=rho)
        if ok:
            status = "FOUND"
            info["rule"] = rules_m.rule_to_json(cand)
            info["gain"] = rules_m.gain(cand)
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
            for k in to._spread(ks, per_q):
                new += add_class(q, k)
        if new == 0:
            status = "BUG"
            info["why"] = ["no new class", str(fails[:2])]
            break
    info.update({"status": status, "iterations": it, "n_classes": len(clauses),
                 "seconds": round(time.time() - t0, 1), "solve_seconds": round(solve_s, 1),
                 "n_touch": len(touch), "classes": sorted([list(x) for x in clauses])})
    return info


def short_rule(rj):
    """Compact one-line rule: R=removed S=w@s0,beta A=a@s0,beta (shift s0 + beta delta)."""
    s = " ".join("%s@%s,%s" % (w, s0, b) for w, (s0, b) in rj["rephased"].items())
    a = " ".join("%s@%s,%s" % (w, s0, b) for w, (s0, b) in rj["added"].items())
    return "R=%s S=%s A=%s" % (",".join(str(x) for x in rj["removed"]), s, a)


def _tok(tag, st):
    if not st:
        return "%s:-" % tag
    return "%s:%s%d/%d" % (tag, st["status"][0], st.get("it_total", 0), st.get("sec_total", 0))


def old_lines(o1_state):
    """Route-19 results kept in its cache: the rules it found and its status counts."""
    out = []
    for t in ("h64", "f64x"):
        st = o1_state.get(t, {})
        if st.get("status") == "FOUND":
            out.append(("OLD %s %s" % (t, short_rule(st["rule"])))[:420])
    cnt = {}
    for t in to.ORDER:
        s = o1_state.get(t, {}).get("status", "-")
        cnt[s] = cnt.get(s, 0) + 1
    out.append("O1STATE " + " ".join("%s=%d" % (k, v) for k, v in sorted(cnt.items())))
    return out


def probe_p(budget=520, workers=8, cache=None, o1_cache=None, cap=60, cap_sanity=150):
    """Run pending tiers (fewest turns first), certify any FOUND target, return a short report
    whose last lines matter most."""
    t_end = time.time() + budget
    tmp = tempfile.gettempdir()
    cache = cache or os.path.join(tmp, "mv2-slr-p1")
    o1_cache = o1_cache or os.path.join(tmp, "mv2-slr-o1")
    os.makedirs(cache, exist_ok=True)
    state_path = os.path.join(cache, "state.json")
    state = rs._load(state_path, {})
    o1 = rs._load(os.path.join(o1_cache, "state.json"), {})
    head = []
    tail = []
    ok, note = rs.ensure_ortools()
    head.append("ortools=%s %s o1=%d" % (ok, note[:40], len(o1)))
    head.extend(old_lines(o1))
    while ok:
        pend = [t for t in ORDER if state.get(t, {}).get("status") not in
                ("FOUND", "INFEASIBLE", "BUG")]
        if not pend:
            break
        pend.sort(key=lambda t: (state.get(t, {}).get("turns", 0), ORDER.index(t)))
        tag = pend[0]
        N, g, P, kind, dens = tier(tag)
        left = t_end - time.time()
        if left < 25:
            break
        prev = state.get(tag, {})
        seeds = prev.get("classes")
        if seeds is None and tag not in SANITY:
            seeds = o1.get(tag, {}).get("classes")
        c = cap_sanity if tag in SANITY else cap
        try:
            info = cegar_p(N, g, P, kind, dens, time.time() + min(c, left - 12),
                           workers=workers, seed_classes=seeds)
        except Exception as e:
            info = {"status": "BUG", "why": [repr(e)[:160]], "iterations": 0, "seconds": 0,
                    "solve_seconds": 0, "classes": prev.get("classes", [])}
        info["turns"] = prev.get("turns", 0) + 1
        info["it_total"] = prev.get("it_total", 0) + info.get("iterations", 0)
        info["sec_total"] = prev.get("sec_total", 0) + info.get("seconds", 0)
        info["solve_total"] = prev.get("solve_total", 0) + info.get("solve_seconds", 0)
        if info["status"] == "FOUND":
            full = to.certify(rules_m.rule_from_json(info["rule"]), N, n=N - g)
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
    toks = [_tok(t, state.get(t)) for t in ORDER]
    body = [" ".join(toks[i:i + 9]) for i in range(0, len(toks), 9)]
    its = sum(state.get(t, {}).get("it_total", 0) for t in ORDER)
    sol = sum(state.get(t, {}).get("solve_total", 0) for t in ORDER)
    body.append("PIT iterations=%d solve_s=%d per_it=%.1f" % (its, sol, sol / its if its else 0))
    for t in ORDER:
        st = state.get(t, {})
        if st.get("status") == "BUG":
            tail.append("BUG %s %s" % (t, " | ".join(st.get("why", []))[:200]))
    new = []
    for t in ORDER:
        st = state.get(t, {})
        if st.get("status") != "FOUND":
            continue
        N, g = tier(t)[0], tier(t)[1]
        if t in SANITY or N - g == to.KNOWN_N or N - g >= 95:
            tail.append(("SANE %s %s" % (t, short_rule(st["rule"])))[:420])
            continue
        new.append(N - g)
        tail.append(("RULE %s n=%d %s" % (t, N - g, short_rule(st["rule"])))[:700])
        tail.append("CERT %s %s" % (t, json.dumps(st.get("cert"))[:200]))
    cnt = {}
    for t in ORDER:
        s = state.get(t, {}).get("status", "-")
        cnt[s] = cnt.get(s, 0) + 1
    tail.append("STATUS new_n=%s %s" % (new or "-", " ".join(
        "%s=%d" % (k, v) for k, v in sorted(cnt.items()))))
    return "\n".join(head + body + tail)
