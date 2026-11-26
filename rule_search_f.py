# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 12 (PREREG_rules_f.md): can Poliakova's gadget be finished below 96, or doubled, when
the added runners may sit at thirds, quarters or sixths?

Criterion and proof: rules_m.py. A rule of modulus m with gain g >= 1, touched base speeds <= L
and untouched helpers <= L gives counterexamples for every n >= L/m - g.

Poliakova's 9 -> 8 rule (arXiv:2609.23952, rules_m.POLIAKOVA_9_8) has modulus 2 and, in the time
scale of the base 1, 2, 3, ..., removes 4, 16 and 96, rephases 6, 12, 24, 48 at (1/2, 1/2) and
8, 32 at (0, -1), and adds 3/2 and 9/2. Its threshold is 96 - 1 = 95. Exact searches with halves
only (tomdif, aadrianvv) found no gain-1 rule with top below 96 and no gain-2 rule below 120.

Route 12 fixes part of Poliakova's rule, scaled to modulus m (m even), and asks CP-SAT for the
rest. Everything not fixed is free within menu A (touched and added speeds 5-smooth, every other
multiple of m up to L an untouched helper, beta in halves on [-2, 2], shift denominators
{1, 2, 3, 4, 6}).

  fix 'all':  the whole rule is fixed (its removal of the top 96 m included).
  fix 'core': only the gadget below the top is fixed: removals of 4 m/2 and 16 m/2 and the
              rephases of 6..48 and 8, 32 (times m/2). The added runners are free.

Tiers (thresholds in the last column):
  sanity  f2S, f6S:   fix all, gain >= 1, L = 96 m (must be FOUND; threshold 95).
  control f2G2:       m = 2, fix all, gain >= 2, L = 192 (tomdif: gain 2 needs L = 240).
          f2C:        m = 2, fix core, gain >= 1, L = 190 (tomdif/aadrianvv: none below 192).
  target  f6G2, f4G2: fix all, gain >= 2, L = 96 m   -> threshold 94.
          f6C2, f4C2: fix core, gain >= 2, L = 96 m  -> threshold 94.
          f6C, f4C:   fix core, gain >= 1, L = 95 m  -> threshold 94.

A rule FOUND passes rules_m.local_check exactly and is then certified for n = threshold..94 by
the two global checkers of slr.py (rule_search_d.certify). INFEASIBLE means no rule of the menu
extends the fixed part (lazily collected clauses, as in rule_search_c: every rule of the menu
that passes local_check satisfies every clause, so INFEASIBLE on a subset is a proof for the
menu). Forced options that occur in no collected clause are still created and forced, so the
argument is unchanged.
"""
import json
import os
import tempfile
import time
from fractions import Fraction as F

import rules_m
import rule_search_c as rc
import rule_search_d as rd
import rule_search_s as rs

NMAX = 94
P5 = (2, 3, 5)

# tag: (m, L, fix, min_gain, expectation)
TIERS_F = {
    "f2S": (2, 192, "all", 1, "find"),
    "f6S": (6, 576, "all", 1, "find"),
    "f2G2": (2, 192, "all", 2, "none?"),
    "f2C": (2, 190, "core", 1, "none?"),
    "f6G2": (6, 576, "all", 2, "search"),
    "f6C2": (6, 576, "core", 2, "search"),
    "f6C": (6, 570, "core", 1, "search"),
    "f4G2": (4, 384, "all", 2, "search"),
    "f4C2": (4, 384, "core", 2, "search"),
    "f4C": (4, 380, "core", 1, "search"),
}
ORDER_F = ["f2S", "f6S", "f2G2", "f6G2", "f6C", "f6C2", "f2C", "f4G2", "f4C", "f4C2"]

# gate plans: (tag, seconds); unused time of a quick tier passes on to the next
PLAN_F1 = [("f2S", 40), ("f6S", 60), ("f2G2", 90), ("f6G2", 330)]
PLAN_F2 = [("f6C", 260), ("f6C2", 260)]
PLAN_F3 = [("f2C", 130), ("f4G2", 130), ("f4C", 130), ("f4C2", 130)]


def menu(tag):
    """(m, L, touch, fixed helpers, added pool, betas, dens, fix, min_gain)."""
    m, L, fix, g, _e = TIERS_F[tag]
    touch, fixed, added = rc.pools_c(m, L, P5)
    return m, L, touch, fixed, added, rs.betas_of("h"), rc.DENS_A, fix, g


def fixed_part(m, fix):
    """The fixed part of Poliakova's rule scaled to modulus m (m even), normalised:
    {'removed': [...], 'rephased': {w: (s0, b)}, 'added': {a: (s0, b)}}."""
    if m % 2:
        raise ValueError("Poliakova's rule needs an even modulus")
    sc = rules_m.scale(rules_m.POLIAKOVA_9_8, m // 2)
    _m, removed, reph, added = rules_m._norm_rule(sc)
    if fix == "all":
        return {"removed": list(removed), "rephased": dict(reph), "added": dict(added)}
    if fix == "core":
        top = max(removed + list(reph))
        return {"removed": [w for w in removed if w < top],
                "rephased": {w: sb for w, sb in reph.items() if w < top},
                "added": {}}
    raise ValueError("fix must be 'all' or 'core'")


def forced_keys(fx):
    """Clause keys the fixed part makes true (same format as rule_search_c.class_clauses)."""
    keys = [("e", w, F(s0) % 1, F(b)) for w, (s0, b) in sorted(fx["rephased"].items())]
    keys += [("o", a, F(s0) % 1, F(b)) for a, (s0, b) in sorted(fx["added"].items())]
    return keys


def check_menu(tag):
    """Shape problems of a tier: every fixed speed must be in the menu (empty list = fine)."""
    m, L, touch, _fixed, added, betas, dens, fix, _g = menu(tag)
    fx = fixed_part(m, fix)
    probs = []
    for w in fx["removed"] + list(fx["rephased"]):
        if w not in touch:
            probs.append("fixed base speed %d not touchable" % w)
    for a in fx["added"]:
        if a not in added:
            probs.append("fixed added speed %d not in the added pool" % a)
    for key in forced_keys(fx):
        if key[3] not in betas:
            probs.append("beta %s not in the menu" % key[3])
        if key[2].denominator not in dens:
            probs.append("shift %s not in the menu" % key[2])
    if fix == "all" and max(fx["removed"] + list(fx["rephased"])) > L:
        probs.append("fixed top above L")
    return probs


def solve_f(clauses, touch, fx, min_gain, time_limit, workers):
    """CP-SAT feasibility over the collected clauses with the fixed part forced.
    Returns (status name, rule or None)."""
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
    forced = [lit(key) for key in forced_keys(fx)]
    by_base = {w: [] for w in touch}
    by_added = {}
    for key, var in opt.items():
        if key[0] == "e":
            by_base[key[1]].append(var)
        else:
            by_added.setdefault(key[1], []).append(var)
    for w in touch:
        add(rem[w] + unt[w] + sum(by_base[w]) == 1)
    for w in fx["removed"]:
        add(rem[w] == 1)
    for v in forced:
        add(v == 1)
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
    rule = {"removed": [w for w in touch if val(rem[w])], "rephased": {}, "added": {}}
    for key, var in opt.items():
        if val(var):
            if key[0] == "e":
                rule["rephased"][key[1]] = (key[2], key[3])
            else:
                rule["added"][key[1]] = (key[2], key[3])
    return name, rule


def cegar_f(tag, deadline, workers=6, seed_classes=None, per_q=16, seed_per_q=4,
            it_time=20.0):
    """Counterexample-guided search for one tier. Status FOUND (info['rule'] passes
    local_check with gain >= the tier's), INFEASIBLE, UNKNOWN or BUG."""
    t0 = time.time()
    m, L, touch, fixed, added, betas, dens, fix, min_gain = menu(tag)
    fx = fixed_part(m, fix)
    info = {"tag": tag, "m": m, "L": L, "fix": fix, "min_gain": min_gain, "status": "UNKNOWN",
            "iterations": 0, "n_touch": len(touch), "n_added": len(added)}
    probs = check_menu(tag)
    if probs:
        info["status"] = "BUG"
        info["shape_problems"] = probs
        return info
    clauses = {}
    lits = [0]

    def add_class(q, k):
        if (q, k) in clauses:
            return False
        c = rc.class_clauses(q, k, touch, fixed, added, betas, dens)
        clauses[(q, k)] = c
        lits[0] += sum(len(x) for x in c) + len(c)
        return True

    for q in touch:
        for k in rc._spread(rules_m.responsible_classes(q, m), seed_per_q):
            add_class(q, k)
    for qk in seed_classes or []:
        add_class(int(qk[0]), int(qk[1]))
    it = 0
    tl = it_time
    status = "UNKNOWN"
    while True:
        left = deadline - time.time()
        if left < 8:
            break
        it += 1
        st, cand = solve_f(clauses, touch, fx, min_gain, min(tl, left - 4), workers)
        if st == "INFEASIBLE":
            status = "INFEASIBLE"
            break
        if cand is None:
            tl = min(4 * tl, 900.0)
            continue
        rule = {"m": m, "removed": cand["removed"], "rephased": cand["rephased"],
                "added": cand["added"]}
        ok, fails = rules_m.local_check(rule, untouched_upto=L)
        if ok:
            if rules_m.gain(rule) < min_gain:
                status = "BUG"
                info["stuck_on"] = ["gain %d below %d" % (rules_m.gain(rule), min_gain)]
                break
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
                 "literals": lits[0], "seconds": round(time.time() - t0, 1),
                 "classes": sorted([list(x) for x in clauses])})
    return info


def _line(tag, rec):
    return "%s m=%s L=%s fix=%s g>=%s st=%s it=%s cls=%s lits=%s t=%ss" % (
        tag, rec.get("m"), rec.get("L"), rec.get("fix"), rec.get("min_gain"),
        rec.get("status"), rec.get("iterations_total"), rec.get("n_classes"),
        rec.get("literals"), round(rec.get("seconds_total", 0)))


def e_summary(e_cache=None):
    """One compact line on the route-11c cube cache (kept by earlier gate probes)."""
    e_cache = e_cache or os.path.join(tempfile.gettempdir(), "mv2-slr-rules-e1")
    st = rs._load(os.path.join(e_cache, "tiers.json"), {})
    if not st:
        return "11c none"
    parts = []
    for tag in sorted(st):
        r = st[tag]
        parts.append("%s=%s/%s/%s/fr%s" % (tag, r.get("status"), r.get("n_infeasible"),
                                           r.get("n_cubes"), r.get("frontier")))
    return "11c " + " ".join(parts)


def probe_f(plan, budget=530, workers=6, cache=None, nmax=NMAX, e_cache=None):
    """Run the (tag, seconds) plan in order; decided tiers are skipped, open ones resume from
    their collected classes. A rule with threshold <= nmax is certified. Report: details
    first, summary lines last."""
    t_end = time.time() + budget
    cache = cache or os.path.join(tempfile.gettempdir(), "mv2-slr-rules-f1")
    os.makedirs(cache, exist_ok=True)
    state_path = os.path.join(cache, "tiers.json")
    rule_path = os.path.join(cache, "rule.json")
    state = rs._load(state_path, {})
    found = rs._load(rule_path, None)
    lines = []
    ok = False
    if plan:
        ok, note = rs.ensure_ortools()
        lines.append("ortools ok=%s %s" % (ok, note[:100]))
    carry = 0.0
    if ok:
        for tag, secs in plan:
            if state.get(tag, {}).get("status") in ("FOUND", "INFEASIBLE", "BUG"):
                carry += secs
                continue
            wall = min(secs + carry, t_end - time.time() - 20)
            if wall < 30:
                lines.append("stop: no time for %s" % tag)
                break
            t1 = time.time()
            prev = state.get(tag, {})
            info = cegar_f(tag, time.time() + wall, workers=workers,
                           seed_classes=prev.get("classes"))
            carry = max(0.0, secs + carry - (time.time() - t1))
            info["iterations_total"] = info.get("iterations", 0) + prev.get("iterations_total", 0)
            info["seconds_total"] = info.get("seconds", 0) + prev.get("seconds_total", 0)
            state[tag] = info
            rs._save(state_path, state)
            if info["status"] == "BUG":
                lines.append("BUG %s %s" % (tag, info.get("stuck_on") or info.get("shape_problems")))
            if info["status"] == "FOUND":
                lines.append("RULE %s gain=%s thr=%s %s" % (tag, info["gain"], info["threshold"],
                                                         rs.fmt_rule(info["rule"])))
                if info["threshold"] <= nmax and found is None:
                    found = {"tag": tag, "L": info["L"], "rule": info["rule"],
                             "threshold": info["threshold"]}
                    rs._save(rule_path, found)
    if found is not None:
        lines.append("rule from %s thr=%d" % (found["tag"], found["threshold"]))
        lines.append(rd.certify(found, cache, t_end, nmax))
    lines.append(e_summary(e_cache))
    for tag in ORDER_F:
        if tag in state:
            lines.append(_line(tag, state[tag]))
    lines.append("STATUS " + " ".join("%s=%s" % (t, state[t].get("status"))
                                      for t in ORDER_F if t in state))
    return "\n".join(lines)


def job_main(argv=None):
    """Compete driver: every tier of ORDER_F, then write the state to --out-dir."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--minutes", type=float, default=120)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    cache = os.path.join(a.out_dir, "cache")
    per = 60.0 * a.minutes / len(ORDER_F)
    rep = probe_f([(t, per) for t in ORDER_F], budget=60.0 * a.minutes, workers=a.workers,
                  cache=cache, e_cache=os.path.join(a.out_dir, "no-e-cache"))
    with open(os.path.join(a.out_dir, "report_f.txt"), "w", encoding="utf-8") as f:
        f.write(rep + "\n")
    print(rep)
    return rep


if __name__ == "__main__":
    job_main()
