# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 15 (PREREG_rules_j.md): neighbours of the two known structured covers.

The shifted Lonely Runner Conjecture fails for n = 63 (Callens, Zenodo 10.5281/zenodo.24051700)
and for every n >= 95 (Poliakova, arXiv:2609.23952); 58..62 and 64..94 are open. A configuration
of k runners whose OPEN arcs of radius R = 1/(n+1) cover the circle is a counterexample for n
as soon as k <= n (padding with new speeds at shift 0 keeps a cover).

Going DOWN from a k-runner cover at radius 1/(k+1) to n = k - d needs d fewer runners, but the
radius grows to 1/(k-d+1): every arc gets longer by about the measure the deleted runners held.
Going UP to n = k + 1 allows one more runner but shrinks the radius. Nobody has published either
search around these two covers (PREREG_rules_j.md lists the searches checked). This module asks,
exactly and for a finite menu only:

  Menu of a tier (source cover with speeds v_i and shifts S_i / Dg):
    * every source runner i is deleted, or kept with shift (S_i + j) / Dg for |j| <= J;
    * any number of added runners: speeds a <= max(v) (a <= 2 max(v) in the up tier uC64) that
      are {2,3,5}-smooth and not in the source, each with any shift S / Dg (one per speed);
    * (added) - (deleted) <= n - k, so the configuration has at most n runners.
  Question: does some configuration of the menu cover the circle with open arcs of radius
  1/(n+1)?

Decision procedure: point CEGAR with CP-SAT (as rule_search_g.cegar_g). The clause of a point t
lists EVERY menu option whose open arc contains t (cover_res is exact), so a covering
configuration of the menu satisfies every clause: INFEASIBLE on the collected clauses proves
that the finite menu has no cover. FOUND = padded to exactly n runners, distinct speeds, and both
global exact checkers of slr.py pass. Added options are created only when a clause names them;
a configuration using an unnamed add can drop it and keeps every clause and the count bound.
"""
import math
import multiprocessing
import os
import tempfile
import time
from fractions import Fraction as F

import rule_search_g as rg
import rule_search_s as rs
import slr

# Callens's n = 63 certificate (Zenodo 10.5281/zenodo.24051700, CC BY 4.0; file
# papers/slr_ext_n63/data/certificates/cert_n063.json of github.com/xaviercallens/AutoevolveAI):
# base 2, 4, ..., 128 with 4, 8, 32, 72, 96, 108 removed, seven speeds rephased, five odd speeds
# added; every shift is a / 520. The sanity tier sC63 re-checks it exactly.
C63_D = 520
C63_OFF = (4, 8, 12, 16, 24, 32, 36, 48, 64, 72, 96, 108)
C63_MOVED = ((12, 264), (16, 512), (24, 264), (36, 264), (48, 256), (64, 8), (128, 512),
             (1, 385), (3, 390), (9, 388), (27, 391), (81, 391))

# tag: (source, n). The source has k runners and covers at radius 1/(k+1).
TIERS_J = {
    "sC63": ("C", 63),   # sanity: the source itself, must be FOUND
    "sP95": ("P", 95),   # sanity: the source itself, must be FOUND
    "dC62": ("C", 62),   # delete >= 1 from Callens's cover, radius 1/63
    "dP94": ("P", 94),   # delete >= 1 from Poliakova's cover, radius 1/95
    "uC64": ("C", 64),   # at most one more runner than Callens's cover, radius 1/65
    "dC61": ("C", 61),
    "dP93": ("P", 93),
}
ORDER_J = ["sC63", "sP95", "dC62", "dP94", "uC64", "dC61", "dP93"]
J_OF = {"C": 8, "P": 12}  # J / Dg = 1/65 and 1/97: one base Dirichlet step either way
SLICE_S = 150
OPEN = set(range(58, 63)) | set(range(64, 95))


def c63():
    """(speeds, integer shifts S, Dg) of Callens's n = 63 cover."""
    plain = [w for w in range(2, 127, 2) if w not in C63_OFF]
    v = plain + [w for w, _a in C63_MOVED]
    S = [0] * len(plain) + [a for _w, a in C63_MOVED]
    return v, S, C63_D


def p95():
    """(speeds, integer shifts S, Dg) of Poliakova's rule on 2, 4, ..., 192 (95 runners)."""
    N = 96
    Md = rg.shift_unit(N)
    v, s = rg.config_of(rg.poliakova_cand(N), 2, N, Md)
    S = []
    for x in s:
        y = F(x) * Md
        if y.denominator != 1:
            raise ValueError("shift off the grid")
        S.append(int(y) % Md)
    return v, S, Md


def model_of(tag):
    src, n = TIERS_J[tag]
    v, S, Dg = c63() if src == "C" else p95()
    have = set(v)
    top = 2 * max(v) if n > len(v) else max(v)  # longer add pool only where adds are cheap
    adds = [a for a in range(1, top + 1) if a not in have and rs.smooth(a, rg.P5)]
    return {"tag": tag, "src": src, "n": n, "k": len(v), "v": v, "S": S, "Dg": Dg,
            "J": J_OF[src], "R": F(1, n + 1), "adds": adds, "slack": n - len(v)}


def cover_res(v, t, R, Dg):
    """Exact: the residues S mod Dg with ||v t + S/Dg|| < R."""
    x = (-v * F(t)) % 1
    lo = (x - R) * Dg
    hi = (x + R) * Dg
    first = math.floor(lo) + 1
    last = math.ceil(hi) - 1
    if last - first + 1 >= Dg:
        return set(range(Dg))
    return set(S % Dg for S in range(first, last + 1))


def point_keys(t, M):
    """Every menu option whose open arc of radius R contains t: 'x:i:j' (source runner i kept
    with shift (S_i + j)/Dg) and 'y:a:S' (speed a added with shift S/Dg)."""
    t = F(t) % 1
    Dg, J, R = M["Dg"], M["J"], M["R"]
    keys = []
    for i, (vi, Si) in enumerate(zip(M["v"], M["S"])):
        res = cover_res(vi, t, R, Dg)
        for j in range(-J, J + 1):
            if (Si + j) % Dg in res:
                keys.append("x:%d:%d" % (i, j))
    for a in M["adds"]:
        for S in sorted(cover_res(a, t, R, Dg)):
            keys.append("y:%d:%d" % (a, S))
    return keys


def hint_cand(M):
    return {"del": [], "j": {}, "add": {}}


def config_j(cand, M):
    """Speeds and exact shifts of a candidate {'del': [i], 'j': {i: j}, 'add': {a: S}}."""
    dl = set(cand["del"])
    v, s = [], []
    for i, (vi, Si) in enumerate(zip(M["v"], M["S"])):
        if i in dl:
            continue
        v.append(vi)
        s.append(F((Si + cand["j"].get(i, 0)) % M["Dg"], M["Dg"]))
    for a in sorted(cand["add"]):
        v.append(a)
        s.append(F(cand["add"][a] % M["Dg"], M["Dg"]))
    return v, s


def lits_j(cand, M):
    dl = set(cand["del"])
    out = set("x:%d:%d" % (i, cand["j"].get(i, 0)) for i in range(M["k"]) if i not in dl)
    out |= set("y:%d:%d" % (a, S) for a, S in cand["add"].items())
    return out


def certify_j(v, s, n):
    """Pad with new speeds at shift 0 to exactly n runners; both exact checkers at 1/(n+1)."""
    v, s = list(v), list(s)
    k = max(v) + 1
    while len(v) < n:
        while k in v:
            k += 1
        v.append(k)
        s.append(F(0))
        k += 1
    R = F(1, n + 1)
    a, _ = slr.covers_sweep(v, s, R)
    b, _ = slr.covers_endpoints(v, s, R) if a else (False, None)
    return {"n": len(v), "distinct": len(set(v)) == len(v), "sweep": a, "endpoints": b,
            "ok": bool(a and b and len(v) == n and len(set(v)) == len(v)),
            "speeds": v, "shifts": [str(x) for x in s]}


def measure(v, s, R):
    gaps, _t = rg.float_scan(v, s, float(R))
    return sum(b - a for a, b in gaps), len(gaps)


def scan_j(M, cap_per=4, cap_total=900):
    """Seeds and the no-reshift diagnostic. Down tiers: delete each source runner alone and
    measure what stays uncovered at radius R (no reshift). Other tiers: the source itself."""
    v = M["v"]
    s = [F(Si, M["Dg"]) for Si in M["S"]]
    n, R = M["n"], M["R"]
    pts = []
    if n < M["k"]:
        res = []
        for i in range(M["k"]):
            vv, ss = v[:i] + v[i + 1:], s[:i] + s[i + 1:]
            gaps, touches = rg.float_scan(vv, ss, float(R))
            res.append((sum(b - a for a, b in gaps), len(gaps), v[i]))
            pts += [x for x in rg.gap_points(gaps, cap_per) if rg.uncovered_exact(x, vv, ss, n)]
            pts += rg.touch_points(touches, vv, ss, n, cap_per)
        res.sort()
        diag = {"kind": "del1", "min": res[0][0], "gaps": res[0][1], "at": res[0][2],
                "zero": [w for m_, g, w in res if g == 0]}
    else:
        gaps, touches = rg.float_scan(v, s, float(R))
        pts += [x for x in rg.gap_points(gaps, cap_total) if rg.uncovered_exact(x, v, s, n)]
        pts += rg.touch_points(touches, v, s, n, cap_total)
        diag = {"kind": "self", "min": sum(b - a for a, b in gaps), "gaps": len(gaps), "at": 0,
                "zero": []}
    seen, out = set(), []
    for x in pts:
        x = F(x) % 1
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out[:cap_total], diag


def solve_j(clauses, M, time_limit, workers):
    """CP-SAT over the collected clauses. Returns (status name, candidate or None)."""
    from ortools.sat.python import cp_model
    md = cp_model.CpModel()
    nb = rs._m(md, "new_bool_var", "NewBoolVar")
    bor = rs._m(md, "add_bool_or", "AddBoolOr")
    add = rs._m(md, "add", "Add")
    J, k = M["J"], M["k"]
    dl = [nb("d%d" % i) for i in range(k)]
    x = {(i, j): nb("x%d_%d" % (i, j + J)) for i in range(k) for j in range(-J, J + 1)}
    for i in range(k):
        add(dl[i] + sum(x[i, j] for j in range(-J, J + 1)) == 1)
    y = {}

    def lit(key):
        kind, a, b = key.split(":")
        if kind == "x":
            return x[int(a), int(b)]
        kk = (int(a), int(b))
        if kk not in y:
            y[kk] = nb("y%d_%d" % kk)
        return y[kk]

    for c in clauses:
        bor([lit(kk) for kk in c])
    by = {}
    for (a, _S), var in y.items():
        by.setdefault(a, []).append(var)
    for _a, vs in by.items():
        add(sum(vs) <= 1)
    add(sum(y.values()) - sum(dl) <= M["slack"])
    ah = rs._m(md, "add_hint", "AddHint")
    for i in range(k):
        ah(dl[i], 0)
        for j in range(-J, J + 1):
            ah(x[i, j], 1 if j == 0 else 0)
    for var in y.values():
        ah(var, 0)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(max(time_limit, 1.0))
    try:
        solver.parameters.num_workers = int(workers)
    except (AttributeError, ValueError):
        solver.parameters.num_search_workers = int(workers)
    st = rs._m(solver, "solve", "Solve")(md)
    name = rs._m(solver, "status_name", "StatusName")(st)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return name, None
    val = rs._m(solver, "value", "Value")
    cand = {"del": [i for i in range(k) if val(dl[i])], "j": {}, "add": {}}
    for (i, j), var in x.items():
        if j and val(var):
            cand["j"][i] = j
    for (a, S), var in y.items():
        if val(var):
            cand["add"][a] = S
    return name, cand


def fmt_cand(cand, M):
    dl = sorted(M["v"][i] for i in cand["del"])
    mv = ";".join("%d:%+d" % (M["v"][i], j) for i, j in sorted(cand["j"].items()))
    ad = ";".join("%d:%d" % (a, S) for a, S in sorted(cand["add"].items()))
    return "del=%s mv={%s} add={%s} /Dg=%d" % (dl, mv, ad, M["Dg"])


def cegar_j(tag, deadline, workers=2, prev=None, pts_per_it=240):
    """Point CEGAR for one tier; prev: cached state. Status FOUND, INFEASIBLE, UNKNOWN or BUG."""
    t0 = time.time()
    M = model_of(tag)
    n, k = M["n"], M["k"]
    prev = prev or {}
    clauses = [list(c) for c in prev.get("clauses", [])]
    seen = set(frozenset(c) for c in clauses)
    info = {"tag": tag, "n": n, "k": k, "n_adds": len(M["adds"]), "status": "UNKNOWN",
            "diag": prev.get("diag")}

    def add_point(t):
        c = point_keys(t, M)
        fc = frozenset(c)
        if fc in seen:
            return 0
        seen.add(fc)
        clauses.append(sorted(fc))
        return 1

    if not clauses:
        pts, diag = scan_j(M)
        info["diag"] = diag
        for t in pts:
            add_point(t)
            if time.time() > deadline - 30:
                break
    info["seeded"] = prev.get("seeded", len(clauses))
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
        st, cand = solve_j(clauses, M, min(tl, left - 6), workers)
        if st == "INFEASIBLE":
            status = "INFEASIBLE"
            break
        if cand is None:
            tl = min(3 * tl, 600.0)
            continue
        v, s = config_j(cand, M)
        lits = lits_j(cand, M)
        gaps, touches = rg.float_scan(v, s, float(M["R"]))
        pts = [x for x in rg.gap_points(gaps, pts_per_it) if rg.uncovered_exact(x, v, s, n)]
        if len(pts) < pts_per_it:
            pts += rg.touch_points(touches, v, s, n, pts_per_it - len(pts))
        if not pts:
            ok, x0 = slr.covers_sweep(v, s, M["R"])
            if ok:
                cert = certify_j(v, s, n)
                info["cert"] = cert
                info["cand"] = {"del": cand["del"], "j": {str(i): j for i, j in cand["j"].items()},
                                "add": {str(a): S for a, S in cand["add"].items()}}
                info["rule"] = fmt_cand(cand, M)
                status = "FOUND" if cert["ok"] else "BUG"
                break
            pts = [F(x0) % 1]
        new = 0
        for x in pts:
            c = point_keys(x, M)
            if lits.intersection(c):
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
    info.update({"status": status, "iterations": it, "n_clauses": len(clauses), "tl": tl,
                 "seconds": round(time.time() - t0, 1), "clauses": clauses})
    return info


def _worker(tag, deadline, cache, workers):
    path = os.path.join(cache, "t_%s.json" % tag)
    try:
        ok, note = rs.ensure_ortools()
        if not ok:
            raise RuntimeError("ortools: " + note)
        prev = rs._load(path, {})
        info = cegar_j(tag, deadline, workers=workers, prev=prev)
        info["iterations_total"] = info["iterations"] + prev.get("iterations_total", 0)
        info["seconds_total"] = round(info["seconds"] + prev.get("seconds_total", 0), 1)
        info["turns"] = prev.get("turns", 0) + 1
        if info["status"] == "FOUND":
            rs._save(os.path.join(cache, "cert_%s.json" % tag), info["cert"])
        rs._save(path, info)
    except Exception as e:  # report it; the other tiers keep going
        import traceback
        with open(os.path.join(cache, "err_%s.txt" % tag), "w", encoding="utf-8") as f:
            f.write("%r\n%s" % (e, traceback.format_exc()[-600:]))


def line_j(tag, r):
    d = r.get("diag") or {}
    return "%s n=%s k=%s st=%s it=%s cls=%s tl=%s t=%ss turns=%s %s=%.3g/%sg@%s z=%s" % (
        tag, r.get("n"), r.get("k"), r.get("status"), r.get("iterations_total"),
        r.get("n_clauses"), int(r.get("tl", 0)), round(r.get("seconds_total", 0)),
        r.get("turns"), d.get("kind"), d.get("min") or 0.0, d.get("gaps"), d.get("at"),
        len(d.get("zero") or []))


def r14_line(idir):
    """Route 14's cached state in one line (its probe reports get cut or lost)."""
    try:
        names = sorted(os.listdir(idir))
    except Exception:
        return "R14 none"
    out = []
    for fn in names:
        if fn.startswith("t_") and fn.endswith(".json"):
            r = rs._load(os.path.join(idir, fn), {})
            out.append("%s=%s/%s/%s" % (fn[2:-5], (r.get("status") or "?")[:3],
                                        r.get("iterations_total"), r.get("n_clauses")))
        elif fn.startswith("err_"):
            out.append("ERR:" + fn[4:-4])
        elif fn.startswith("cert_"):
            out.append("CERT:" + fn[5:-5])
    return "R14 " + " ".join(out)


def probe_j(tiers=ORDER_J, budget=520, cache=None, procs=3, workers=2, slice_s=SLICE_S):
    """Run the open tiers in turns until the budget ends; report with the summary last."""
    t_end = time.time() + budget
    cache = cache or os.path.join(tempfile.gettempdir(), "mv2-slr-rules-j1")
    os.makedirs(cache, exist_ok=True)
    lines = []
    ok, note = rs.ensure_ortools()
    lines.append("ortools ok=%s %s" % (ok, note[:60]))
    decided = ("FOUND", "INFEASIBLE", "BUG")
    turns = 0

    def state(tag):
        return rs._load(os.path.join(cache, "t_%s.json" % tag), {})

    def crashed(tag):
        return os.path.exists(os.path.join(cache, "err_%s.txt" % tag))

    if ok:
        ctx = multiprocessing.get_context("spawn")
        q = []
        for i, tag in enumerate(tiers):
            r = state(tag)
            if r.get("status") not in decided and not crashed(tag):
                q.append((r.get("seconds_total", 0.0), i, tag))
        pending = [t for _s, _i, t in sorted(q)]
        running = []
        while time.time() < t_end:
            alive = []
            for t, p in running:
                if p.is_alive():
                    alive.append((t, p))
                elif state(t).get("status") not in decided and not crashed(t):
                    pending.append(t)
            running = alive
            busy = set(t for t, _p in running)
            while pending and len(running) < procs and t_end - time.time() > 60:
                tag = pending.pop(0)
                if tag in busy:
                    continue
                dl = min(t_end - 25, time.time() + slice_s)
                p = ctx.Process(target=_worker, args=(tag, dl, cache, workers))
                p.start()
                running.append((tag, p))
                busy.add(tag)
                turns += 1
            if not running and (not pending or t_end - time.time() <= 60):
                break
            time.sleep(1.0)
        for tag, p in running:
            p.join(max(0.5, t_end - time.time()))
            if p.is_alive():
                p.terminate()
                lines.append("killed %s" % tag)
    lines.append("turns=%d" % turns)
    states = {t: state(t) for t in tiers}
    for tag in tiers:
        ep = os.path.join(cache, "err_%s.txt" % tag)
        if os.path.exists(ep):
            with open(ep, encoding="utf-8") as f:
                lines.append("ERROR %s %s" % (tag, f.read()[-240:].replace("\n", " | ")))
    for tag in tiers:
        if states[tag]:
            lines.append(line_j(tag, states[tag]))
    for tag in tiers:
        r = states[tag]
        if r.get("status") == "BUG":
            lines.append("BUG %s %s" % (tag, r.get("stuck_on")))
        if r.get("why"):
            lines.append("WHY %s %s" % (tag, r["why"]))
        if r.get("status") == "FOUND":
            c = r.get("cert", {})
            lines.append("RULE %s n=%s sweep=%s endpoints=%s open=%s %s" % (
                tag, c.get("n"), c.get("sweep"), c.get("endpoints"), c.get("n") in OPEN,
                r.get("rule")))
    lines.append(r14_line(os.path.join(tempfile.gettempdir(), "mv2-slr-rules-i1")))
    lines.append("STATUS " + " ".join("%s=%s" % (t, states[t].get("status"))
                                      for t in tiers if states[t]))
    return "\n".join(lines)


def job_main(argv=None):
    """Compete driver: every tier in turns, report to --out-dir."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--minutes", type=float, default=180)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    rep = probe_j(budget=60.0 * a.minutes, cache=os.path.join(a.out_dir, "cache"))
    with open(os.path.join(a.out_dir, "report_j.txt"), "w", encoding="utf-8") as f:
        f.write(rep + "\n")
    print(rep)
    return rep


if __name__ == "__main__":
    job_main()
