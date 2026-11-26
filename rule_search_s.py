# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 10 (PREREG_rules_s.md): local shifted-Lonely-Runner rules aimed at threshold 58.

A local rule of modulus m (criterion and proof in rules_m.py) with gain g >= 1 that touches base
speeds <= L and uses untouched helpers <= U gives a counterexample to the shifted Lonely Runner
Conjecture for every n >= ceil(max(L, U)/m) - g. The open range is 58 <= n <= 94 (2026-11-26),
so a gain-1 rule with L = U = 59 m would close it.

This module searches only at that size, with the speed pools restricted to P-smooth numbers
(all prime factors in P). The encoder is rule_search_m.pair_clauses. The CP-SAT model is that
of rule_search_m.solve with the pools as parameters. Every solver answer is re-checked by
rules_m.local_check (exact, independent of the encoding). Every n it reaches is then certified
by the two global exact checkers of slr.py on the full configuration.

`probe` is the driver used by the test-gate probes and by job_rules_s.py. It keeps its state
(the rule found, the certificates done) in a cache folder, so later probes continue where
earlier ones stopped.
"""
import importlib
import json
import os
import subprocess
import sys
import tempfile
import time
from fractions import Fraction as F

import rules_m
import rule_search_m
import slr

TARGET_N = 58  # smallest open n (2026-11-26)
NMAX = 94  # largest open n

DENS_A = frozenset({1, 2, 3, 4, 6})
DENS_B = frozenset({1, 2, 3, 4, 6, 8, 12})
DENS_C = frozenset({1, 2, 3, 4, 5, 6, 8, 9, 10, 12})

# tag: (m, P or None for all speeds, beta menu 'h' halves / 'q' quarters, dens, seconds)
TIERS = {
    "s5A2": (2, (2, 3, 5), "h", DENS_A, 60),
    "s5B2": (2, (2, 3, 5), "q", DENS_B, 90),
    "s5A6": (6, (2, 3, 5), "h", DENS_A, 90),
    "s7B2": (2, (2, 3, 5, 7), "q", DENS_B, 120),
    "s5B6": (6, (2, 3, 5), "q", DENS_B, 150),
    "s7A6": (6, (2, 3, 5, 7), "h", DENS_A, 150),
    "allA2": (2, None, "h", DENS_A, 150),
    "s7B6": (6, (2, 3, 5, 7), "q", DENS_B, 200),
    "s5C12": (12, (2, 3, 5), "q", DENS_C, 200),
    # sensitivity check, not a search: at L = 192 a rule is known to exist (Poliakova's)
    "chk192": (2, (2, 3), "h", DENS_A, 120),
}
ORDER = ["s5A2", "s5B2", "s5A6", "s7B2", "s5B6", "s7A6", "allA2", "s7B6", "s5C12"]
SIZE_OVERRIDE = {"chk192": (2, 192, 27)}


def smooth(x, P):
    """True iff every prime factor of the positive integer x lies in P (P None: always)."""
    if P is None:
        return True
    for p in P:
        while x % p == 0:
            x //= p
    return x == 1


def pools_s(L, A, m, P):
    """Base speeds (multiples of m up to L) and added speeds (non-multiples of m up to A),
    both P-smooth."""
    base = [w for w in range(m, L + 1, m) if smooth(w, P)]
    added = [a for a in range(1, A + 1) if a % m and smooth(a, P)]
    return base, added


def tier_size(tag):
    """(m, L, A) of a tier: L = m (TARGET_N + 1), so a gain-1 rule has threshold TARGET_N."""
    if tag in SIZE_OVERRIDE:
        return SIZE_OVERRIDE[tag]
    m = TIERS[tag][0]
    L = m * (TARGET_N + 1)
    return m, L, 2 * L + 1


def betas_of(kind):
    return rule_search_m.halves() if kind == "h" else rule_search_m.quarters()


def all_clauses_s(base, added, m, betas, dens, qs=None, lit_budget=None, deadline=None):
    """Clauses for every class (q, k) of every q in qs (default: the whole base pool).
    Returns (clauses, literals), or (None, literals) past the budget or the deadline."""
    cl = {}
    lits = 0
    for q in (qs if qs is not None else base):
        for k in rules_m.responsible_classes(q, m):
            c = rule_search_m.pair_clauses(q, k, base, added, betas, dens)
            cl[(q, k)] = c
            lits += sum(len(x) for x in c)
            if lit_budget is not None and lits > lit_budget:
                return None, lits
        if deadline is not None and time.time() > deadline:
            return None, -lits
    return cl, lits


def _m(obj, snake, camel):
    f = getattr(obj, snake, None)
    return f if f is not None else getattr(obj, camel)


def solve_s(base, added, m, betas, dens, deadline, time_limit, workers=2, min_gain=1,
            lit_budget=2_500_000):
    """CP-SAT over the given pools (same model as rule_search_m.solve). Returns (rule, info)."""
    from ortools.sat.python import cp_model

    t0 = time.time()
    info = {"m": m, "n_base": len(base), "n_added": len(added), "n_betas": len(betas),
            "dens": sorted(dens)}
    clauses, lits = all_clauses_s(base, added, m, betas, dens, lit_budget=lit_budget,
                                  deadline=deadline - 30)
    info["literals"] = lits
    info["build_seconds"] = round(time.time() - t0, 1)
    if clauses is None:
        info["status"] = "too-big" if lits > 0 else "no-time-build"
        return None, info
    tl = min(float(time_limit), deadline - time.time() - 15)
    if tl < 5:
        info["status"] = "no-time"
        return None, info

    md = cp_model.CpModel()
    nb = _m(md, "new_bool_var", "NewBoolVar")
    bor = _m(md, "add_bool_or", "AddBoolOr")
    add = _m(md, "add", "Add")
    rem = {w: nb("rem%d" % w) for w in base}
    unt = {w: nb("unt%d" % w) for w in base}
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
    by_base = {w: [] for w in base}
    by_added = {}
    for key, var in opt.items():
        if key[0] == "e":
            by_base[key[1]].append(var)
        else:
            by_added.setdefault(key[1], []).append(var)
    for w in base:
        add(rem[w] + unt[w] + sum(by_base[w]) == 1)
    for a, vs in by_added.items():
        add(sum(vs) <= 1)
    added_vars = [v for vs in by_added.values() for v in vs]
    g = sum(rem.values()) - sum(added_vars)
    add(g >= min_gain)
    touched = sum(rem.values()) + sum(v for w in base for v in by_base[w]) + sum(added_vars)
    _m(md, "maximize", "Maximize")(64 * g - touched)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = tl
    try:
        solver.parameters.num_workers = int(workers)
    except (AttributeError, ValueError):
        solver.parameters.num_search_workers = int(workers)
    st = _m(solver, "solve", "Solve")(md)
    info["status"] = _m(solver, "status_name", "StatusName")(st)
    info["solve_seconds"] = round(time.time() - t0, 1)
    info["n_option_vars"] = len(opt)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, info
    val = _m(solver, "value", "Value")
    rule = {"m": m, "removed": [w for w in base if val(rem[w])], "rephased": {}, "added": {}}
    for key, var in opt.items():
        if val(var):
            if key[0] == "e":
                rule["rephased"][key[1]] = (key[2], key[3])
            else:
                rule["added"][key[1]] = (key[2], key[3])
    info["gain"] = rules_m.gain(rule)
    return rule, info


def run_tier(tag, deadline, workers=2, tl_scale=1.0):
    m, P, kind, dens, secs = TIERS[tag]
    m, L, A = tier_size(tag)
    base, added = pools_s(L, A, m, P)
    rule, info = solve_s(base, added, m, betas_of(kind), dens, deadline, secs * tl_scale,
                         workers=workers)
    info.update({"tag": tag, "L": L, "A": A, "P": list(P) if P else "all"})
    if rule is not None:
        ok, fails = rules_m.local_check(rule, untouched_upto=L)
        info["local_ok"] = ok
        info["local_fails"] = [list(map(str, f)) for f in fails[:3]]
        info["rule"] = rules_m.rule_to_json(rule)
        info["threshold"] = rules_m.threshold(rule, untouched_upto=L) if ok else None
    return info


def certify_n(rule, U, n):
    """Full configuration for n runners (N = n + g) and both global exact checks."""
    g = rules_m.gain(rule)
    N = n + g
    v, s, delta, nn = rules_m.build_config(rule, N)
    if U and U > rules_m.modulus(rule) * N:
        raise ValueError("helpers above m N")
    R = F(2, 2 * N + 1)
    t0 = time.time()
    a, _ = slr.covers_endpoints(v, s, R)
    b, _ = slr.covers_sweep(v, s, R)
    return {"n": nn, "N": N, "R": str(R), "R_ok": R < F(1, nn + 1),
            "distinct": len(set(v)) == nn, "endpoints": a, "sweep": b,
            "ok": bool(a and b and R < F(1, nn + 1) and len(set(v)) == nn and nn == n),
            "seconds": round(time.time() - t0, 2),
            "speeds": v, "shifts": [str(x) for x in s]}


def ensure_ortools(timeout=300, target=None):
    """Import OR-Tools; if missing, pip-install it into a temp folder. Returns (ok, note)."""
    try:
        importlib.import_module("ortools.sat.python.cp_model")
        return True, "preinstalled"
    except Exception:
        pass
    target = target or os.path.join(tempfile.gettempdir(), "mv2-ortools")
    if target not in sys.path:
        sys.path.insert(0, target)
    importlib.invalidate_caches()
    try:
        importlib.import_module("ortools.sat.python.cp_model")
        return True, "cached"
    except Exception:
        pass
    t0 = time.time()
    cmd = [sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
           "--no-warn-script-location", "--upgrade", "--target", target, "ortools>=9.10"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                           timeout=timeout)
        note = "pip rc=%d %ds %s" % (p.returncode, time.time() - t0,
                                     (p.stderr or p.stdout or "")[-240:].replace("\n", " "))
    except Exception as e:  # pragma: no cover - depends on the host
        return False, "pip failed: %r" % (e,)
    importlib.invalidate_caches()
    for name in [k for k in sys.modules if k == "ortools" or k.startswith("ortools.")]:
        del sys.modules[name]
    try:
        importlib.import_module("ortools.sat.python.cp_model")
        return True, note
    except Exception as e:  # pragma: no cover
        return False, note + " import: %r" % (e,)


def fmt_rule(rj):
    rp = ";".join("%s:%s,%s" % (w, s0, b) for w, (s0, b) in rj["rephased"].items())
    ad = ";".join("%s:%s,%s" % (a, s0, b) for a, (s0, b) in rj["added"].items())
    return "m=%d R=%s S={%s} A={%s}" % (rj["m"], rj["removed"], rp, ad)


def _ranges(ns):
    out, ns = [], sorted(ns)
    i = 0
    while i < len(ns):
        j = i
        while j + 1 < len(ns) and ns[j + 1] == ns[j] + 1:
            j += 1
        out.append("%d" % ns[i] if i == j else "%d-%d" % (ns[i], ns[j]))
        i = j + 1
    return ",".join(out) or "-"


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def probe(tags, budget=540, workers=6, cache=None, tl_scale=1.0, nmax=NMAX):
    """Search the tiers in order until a verified rule is found, then certify every n from its
    threshold to nmax. State is kept in `cache`. Returns a short text report."""
    t_end = time.time() + budget
    cache = cache or os.path.join(tempfile.gettempdir(), "mv2-slr-rules-s")
    os.makedirs(cache, exist_ok=True)
    rule_path = os.path.join(cache, "rule.json")
    cert_path = os.path.join(cache, "certs.json")
    calls_path = os.path.join(cache, "calls.jsonl")
    lines = []
    found = _load(rule_path, None)
    done_tags = [c.get("tag") for c in
                 (json.loads(x) for x in _read_lines(calls_path))]
    if found is None:
        ok, note = ensure_ortools()
        lines.append("ortools ok=%s %s" % (ok, note[:240]))
        if ok:
            for tag in tags:
                if tag in done_tags:
                    continue
                if t_end - time.time() < 60:
                    lines.append("stop: no time for %s" % tag)
                    break
                info = run_tier(tag, t_end, workers=workers, tl_scale=tl_scale)
                with open(calls_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(info, default=str) + "\n")
                lines.append("%s m=%d L=%d P=%s base=%d add=%d lits=%s st=%s gain=%s local=%s "
                             "thr=%s build=%ss t=%ss" % (
                                 tag, info["m"], info["L"], info["P"], info["n_base"],
                                 info["n_added"], info.get("literals"), info.get("status"),
                                 info.get("gain"), info.get("local_ok"), info.get("threshold"),
                                 info.get("build_seconds"), info.get("solve_seconds")))
                if info.get("rule") is not None and not info.get("local_ok"):
                    lines.append("S3 ENCODING BUG %s fails=%s" % (tag, info["local_fails"]))
                if info.get("rule") is not None and tag.startswith("chk"):
                    lines.append("CHECK %s found %s" % (tag, fmt_rule(info["rule"])))
                    continue
                if info.get("local_ok") and info.get("threshold") is not None:
                    found = {"tag": tag, "L": info["L"], "rule": info["rule"],
                             "threshold": info["threshold"]}
                    _save(rule_path, found)
                    break
    else:
        lines.append("cached rule from %s" % found["tag"])
    if found is not None:
        rule = rules_m.rule_from_json(found["rule"])
        lines.append("RULE gain=%d thr=%d L=%d %s" % (rules_m.gain(rule), found["threshold"],
                                                       found["L"], fmt_rule(found["rule"])))
        certs = _load(cert_path, {})
        for n in range(found["threshold"], nmax + 1):
            if str(n) in certs:
                continue
            if t_end - time.time() < 25:
                break
            rec = certify_n(rule, found["L"], n)
            certs[str(n)] = {k: rec[k] for k in ("ok", "endpoints", "sweep", "R_ok",
                                                  "distinct", "seconds", "N")}
            _save(cert_path, certs)
            with open(os.path.join(cache, "certificates.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
        good = [int(n) for n, r in certs.items() if r["ok"]]
        bad = [int(n) for n, r in certs.items() if not r["ok"]]
        dis = [int(n) for n, r in certs.items() if r["endpoints"] != r["sweep"]]
        lines.append("CERTIFIED n=%s FAILED=%s S4_disagree=%s missing_58_94=%s" % (
            _ranges(good), _ranges(bad), _ranges(dis),
            _ranges([n for n in range(TARGET_N, NMAX + 1) if n not in good])))
    return "\n".join(lines)


def _read_lines(path):
    try:
        with open(path, encoding="utf-8") as f:
            return [x for x in f.read().splitlines() if x.strip()]
    except Exception:
        return []
