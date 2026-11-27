# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 13b (PREREG_rules_h.md): the route-13 question (rule_search_g.py, PREREG_rules_g.md),
is there ONE shifted Lonely Runner counterexample with n = 94 runners on a base of multiples
of m, decided with an incremental SAT solver instead of CP-SAT.

Same menu, same point clauses (rule_search_g.point_clause), same exact checks. What changes:

* The CEGAR loop keeps ONE incremental SAT solver (PySAT; CaDiCaL 1.9.5 or Glucose 4) and only
  adds clauses, so learned clauses survive between iterations (CP-SAT rebuilt the model each
  time and needed 400-600 s per call on g6N).
* Every exactly uncovered point t also adds the clause of -t. Both are necessary conditions on
  any cover, so this is sound.
* The runner count is encoded in CNF. Per base speed w: at most one of removed / untouched /
  each rephase option. Per added speed a: at most one shift, and every option of a implies y_a.
  Gain: two upward sequential counters, b_j = [#(not removed) >= j] and a_k = [#y >= k], with
  clauses a_k -> not b_{T-k-need+1} and not b_{T-need+1} (T = number of touchable speeds), i.e.
  #removed - #added >= need. A base speed with no chosen literal is read as removed (this only
  raises the gain), so every real configuration of the menu that covers the collected points
  gives a satisfying assignment: UNSAT is a proof for the finite menu, as in route 13.
* Tiers take 160 s turns in up to 6 processes, least-searched first; route-13 tiers resume
  from the route-13 clause cache. New tiers search smooth N inside the open range (Callens's
  n = 63, Zenodo 24051700, uses N = 64), on bases of multiples of 3, 4 and 6.
"""
import importlib
import json
import multiprocessing
import os
import subprocess
import sys
import tempfile
import time
from fractions import Fraction as F

import rule_search_g as rg
import rule_search_s as rs
import slr

TIERS_H = dict(rg.TIERS_G)
TIERS_H.update({
    "g12N": (12, 94, 95, rg.P5, None, "search"),   # twelfths, n = 94
    # Callens (Zenodo 24051700, 2026-11-08): a Poliakova-type move on 2, 4, ..., 128 gives
    # n = 63. Re-finding it in our menu is a second sanity check (only if it lies in the menu).
    "c63": (2, 63, 64, rg.P5, None, "find?"),
    # smooth N inside the open range, bases Callens and aadrianvv did not search
    "e2G64": (2, 62, 64, rg.P5, None, "search"),   # gain 2 at N = 64 -> n = 62
    "e4G64": (4, 62, 64, rg.P5, None, "search"),
    "e3N81": (3, 80, 81, rg.P5, None, "search"),
    "e6N72": (6, 71, 72, rg.P5, None, "search"),
    "e3N72": (3, 71, 72, rg.P5, None, "search"),
    "e4N80": (4, 79, 80, rg.P5, None, "search"),
    "e6N90": (6, 89, 90, rg.P5, None, "search"),
    "e6N60": (6, 59, 60, rg.P5, None, "search"),
    "e4N60": (4, 59, 60, rg.P5, None, "search"),
})
ORDER_H = ["g2H", "c63", "e2G64", "e3N81", "e6N72", "e4N80", "e6N90", "e3N72", "e6N60",
           "e4N60", "e4G64", "g6N", "g3N", "g4N", "g12N", "g6G2", "g2N"]
SLICE_S = 160  # seconds per tier per turn; tiers take turns, least-searched first
SOLVERS = ("cadical195", "glucose4", "glucose3", "minisat22")


# ------------------------------------------------------------------ CNF encoding (stdlib)

def counter(lits, cap, enc):
    """Upward sequential counter: returns outs (length cap) with outs[k-1] forced true whenever
    at least k of `lits` are true (None: never, the count cannot reach k)."""
    prev = []
    for i, L in enumerate(lits):
        size = min(i + 1, cap)
        cur = [enc.new() for _ in range(size)]
        enc.cls.append([-L, cur[0]])
        for k in range(size):
            if k < len(prev):
                enc.cls.append([-prev[k], cur[k]])
            if k >= 1 and k - 1 < len(prev):
                enc.cls.append([-L, -prev[k - 1], cur[k]])
        prev = cur
    return prev + [None] * (cap - len(prev))


class Enc:
    """CNF for one tier: primary variables (rem, unt, y, options) and the gain constraint."""

    def __init__(self, touch, added, need):
        self.nv = 0
        self.cls = []
        self.sent = 0
        self.touch = list(touch)
        self.added = list(added)
        self.need = need
        self.rem = {w: self.new() for w in self.touch}
        self.unt = {w: self.new() for w in self.touch}
        self.y = {a: self.new() for a in self.added}
        self.primary = set(self.rem.values()) | set(self.unt.values()) | set(self.y.values())
        self.opt = {}
        self.grp = {}
        for w in self.touch:
            self.grp[("b", w)] = [self.rem[w], self.unt[w]]
            self.cls.append([-self.rem[w], -self.unt[w]])
        T = len(self.touch)
        cap = max(T, 1)
        b = counter([-self.rem[w] for w in self.touch], cap, self)
        a = counter([self.y[x] for x in self.added], cap, self) if self.added else []
        self.b, self.a = b, a
        if need > 0:
            j0 = T - need + 1
            if j0 <= 0:
                self.cls.append([])
            elif b[j0 - 1] is not None:
                self.cls.append([-b[j0 - 1]])
        for k in range(1, len(a) + 1):
            if a[k - 1] is None:
                continue
            j = T - k - need + 1
            if j <= 0:
                self.cls.append([-a[k - 1]])
            elif j <= T and b[j - 1] is not None:
                self.cls.append([-a[k - 1], -b[j - 1]])

    def new(self):
        self.nv += 1
        return self.nv

    def var(self, key):
        if key.startswith("u:"):
            return self.unt[int(key[2:])]
        v = self.opt.get(key)
        if v is not None:
            return v
        kind, w, _S = key.split(":")
        w = int(w)
        v = self.new()
        self.opt[key] = v
        self.primary.add(v)
        if kind == "e":
            g = self.grp[("b", w)]
        else:
            g = self.grp.setdefault(("a", w), [])
            self.cls.append([-v, self.y[w]])
        for u in g:
            self.cls.append([-u, -v])
        g.append(v)
        return v

    def clause(self, keys):
        c = [self.var(k) for k in keys]
        self.cls.append(c)
        return c

    def flush(self, solver):
        for c in self.cls[self.sent:]:
            solver.add_clause(c)
        self.sent = len(self.cls)

    def decode(self, pos):
        """Candidate of a model (pos: set of true variables)."""
        reph, add = {}, {}
        for key, v in self.opt.items():
            if v in pos:
                kind, w, S = key.split(":")
                (reph if kind == "e" else add)[int(w)] = int(S)
        cand = {"removed": [], "rephased": {}, "added": add}
        for w in self.touch:
            if self.unt[w] in pos:
                continue
            if w in reph and self.rem[w] not in pos:
                cand["rephased"][w] = reph[w]
            else:
                cand["removed"].append(w)
        return cand

    def assignment_of(self, cand):
        """Satisfying-assignment candidate of a real configuration: primary variables from the
        candidate (options without a variable are read as removed / dropped), counter variables
        by least fixpoint. Returns the set of true variables."""
        pos = set()
        for w in self.touch:
            if w in cand["removed"]:
                pos.add(self.rem[w])
            elif w in cand["rephased"] and cand["rephased"][w]:
                key = "e:%d:%d" % (w, cand["rephased"][w])
                pos.add(self.opt[key] if key in self.opt else self.rem[w])
            else:
                pos.add(self.unt[w])
        for a, S in cand["added"].items():
            key = "o:%d:%d" % (a, S)
            if key in self.opt:
                pos.add(self.opt[key])
                pos.add(self.y[a])
        changed = True
        while changed:
            changed = False
            for c in self.cls:
                if any((l > 0 and l in pos) or (l < 0 and -l not in pos) for l in c):
                    continue
                aux = [l for l in c if l > 0 and l not in self.primary]
                if len(aux) == 1:
                    pos.add(aux[0])
                    changed = True
        return pos

    def satisfied(self, pos):
        """Index of the first clause the assignment violates, or None."""
        for i, c in enumerate(self.cls):
            if not any((l > 0 and l in pos) or (l < 0 and -l not in pos) for l in c):
                return i
        return None


# ------------------------------------------------------------------ SAT solver (PySAT)

def ensure_pysat(timeout=240, target=None):
    """Import PySAT; if missing, pip-install a binary wheel into a temp folder."""
    target = target or os.path.join(tempfile.gettempdir(), "mv2-pysat")

    def ok():
        try:
            importlib.import_module("pysat.solvers")
            return True
        except Exception:
            return False

    if ok():
        return True, "preinstalled"
    if target not in sys.path:
        sys.path.insert(0, target)
    importlib.invalidate_caches()
    if ok():
        return True, "cached"
    t0 = time.time()
    cmd = [sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
           "--no-warn-script-location", "--pre", "--only-binary=:all:", "--target", target,
           "python-sat"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                           timeout=timeout)
        note = "pip rc=%d %ds %s" % (p.returncode, time.time() - t0,
                                     (p.stderr or p.stdout or "")[-160:].replace("\n", " "))
    except Exception as e:  # pragma: no cover - depends on the host
        return False, "pip failed: %r" % (e,)
    for name in [k for k in sys.modules if k == "pysat" or k.startswith("pysat.")]:
        del sys.modules[name]
    importlib.invalidate_caches()
    return ok(), note


def pick_solver(prefer=SOLVERS):
    """First solver name that supports add_clause, conflict budgets and solve_limited."""
    from pysat.solvers import Solver
    for name in prefer:
        try:
            s = Solver(name=name, bootstrap_with=[[1, 2], [-1, 2]])
            s.conf_budget(100)
            r = s.solve_limited()
            s.add_clause([-2, 3])
            r2 = s.solve()
            s.delete()
            if r is True and r2 is True:
                return name
        except Exception:
            continue
    return None


def solve_until(s, deadline, budget=[20000]):
    """solve_limited in conflict-budget slices until a verdict or the deadline (None)."""
    while time.time() < deadline:
        t1 = time.time()
        s.conf_budget(budget[0])
        r = s.solve_limited()
        dt = time.time() - t1
        if r is not None:
            return r
        if dt < 2.0:
            budget[0] = min(budget[0] * 2, 2_000_000)
        elif dt > 10.0:
            budget[0] = max(budget[0] // 2, 2000)
    return None


# ------------------------------------------------------------------ CEGAR

def cegar_h(tag, deadline, cache, solver_name, g_cache=None, pts_per_it=100):
    """Point-CEGAR with one incremental SAT solver. Writes h_<tag>.json (clauses) and
    s_<tag>.json (summary) in cache. Status FOUND, INFEASIBLE, UNKNOWN or BUG."""
    from pysat.solvers import Solver
    t0 = time.time()
    m, n, N, P, hint_kind, _e = TIERS_H[tag]
    touch, fixed, added = rg.pools_g(m, N, P)
    Md, shifts = rg.shift_menu(N)
    need = N - n
    big = os.path.join(cache, "h_%s.json" % tag)
    small = os.path.join(cache, "s_%s.json" % tag)
    prev = rs._load(small, {})
    clauses = rs._load(big, {}).get("clauses") or []
    src = prev.get("src", "h")
    if not clauses and g_cache:
        g = rs._load(g_cache, {}).get(tag, {})
        if g.get("clauses"):
            clauses = [list(c) for c in g["clauses"]]
            src = "g%d" % len(clauses)
    info = {"tag": tag, "m": m, "n": n, "N": N, "src": src, "solver": solver_name,
            "status": "UNKNOWN", "n_touch": len(touch), "n_added": len(added),
            "best_unc": prev.get("best_unc"), "best_rule": prev.get("best_rule")}
    seen = set(frozenset(c) for c in clauses)
    enc = Enc(touch, added, need)
    status = "UNKNOWN"
    for c in clauses:
        if not c:
            status = "INFEASIBLE"
            info["why"] = "a point no option covers"
        enc.clause(c)

    def add(c):
        if c is None:
            return 0
        fc = frozenset(c)
        if fc in seen:
            return 0
        seen.add(fc)
        clauses.append(sorted(fc))
        enc.clause(clauses[-1])
        return 1

    if not clauses:
        for t in rg.seed_points(m, n, N, touch):
            add(rg.point_clause(t, n, touch, fixed, added, Md, shifts))
            if time.time() > deadline - 30:
                break
    info["start_clauses"] = len(clauses)
    s = Solver(name=solver_name)
    hint = rg.poliakova_cand(N) if hint_kind == "poliakova" else None
    if hint is not None:
        hl = rg.lits_of(hint, touch)
        ph = [enc.var(k) for k in sorted(hl)]
        ph += [enc.rem[w] for w in hint["removed"]]
        try:
            s.set_phases(ph)
        except Exception:
            pass
    if status == "UNKNOWN" and any(not c for c in clauses):
        status = "INFEASIBLE"
        info["why"] = "a point no option covers"
    if status == "UNKNOWN":
        enc.flush(s)
    it = 0
    last_save = time.time()

    def save(final=False):  # noqa: ARG001 - same call shape for the periodic and final save
        info.update({"status": status, "iterations": it,
                     "iterations_total": it + prev.get("iterations_total", 0),
                     "seconds_total": round(time.time() - t0 + prev.get("seconds_total", 0), 1),
                     "n_clauses": len(clauses), "literals": sum(len(c) for c in clauses)})
        if hint is not None:
            hl2 = rg.lits_of(hint, touch)
            info["hint_ok"] = all(hl2.intersection(c) for c in clauses)
        rs._save(big, {"clauses": clauses})
        rs._save(small, info)

    while status == "UNKNOWN":
        if deadline - time.time() < 12:
            break
        r = solve_until(s, deadline - 10)
        if r is None:
            break
        if r is False:
            status = "INFEASIBLE"
            break
        it += 1
        pos = set(x for x in s.get_model() if x > 0)
        cand = enc.decode(pos)
        v, sh = rg.config_of(cand, m, N, Md)
        lits = rg.lits_of(cand, touch)
        gaps, touches = rg.float_scan(v, sh, 1.0 / (n + 1))
        unc = sum(b - a for a, b in gaps)
        if info["best_unc"] is None or unc < info["best_unc"]:
            info["best_unc"] = unc
            info["best_rule"] = rg.fmt_cand(cand, Md)
        pts = [x for x in rg.gap_points(gaps, pts_per_it) if rg.uncovered_exact(x, v, sh, n)]
        if len(pts) < pts_per_it:
            pts += rg.touch_points(touches, v, sh, n, pts_per_it - len(pts))
        if not pts:
            ok, x = slr.covers_sweep(v, sh, F(1, n + 1))
            if ok:
                cert = rg.certify_g(cand, m, n, N, Md)
                info["cert"] = cert
                info["rule"] = rg.fmt_cand(cand, Md)
                info["cand"] = {"removed": cand["removed"],
                                "rephased": {str(w): S for w, S in cand["rephased"].items()},
                                "added": {str(a): S for a, S in cand["added"].items()}}
                status = "FOUND" if cert["ok"] else "BUG"
                if status == "FOUND":
                    rs._save(os.path.join(cache, "cert_%s.json" % tag), cert)
                break
            pts = [F(x) % 1]
        new = 0
        for x in pts:
            c = rg.point_clause(x, n, touch, fixed, added, Md, shifts)
            if c is not None and lits.intersection(c):
                status = "BUG"
                info["stuck_on"] = "clause covers %s, exact check does not" % x
                break
            new += add(c)
            new += add(rg.point_clause((-x) % 1, n, touch, fixed, added, Md, shifts))
        if status == "BUG":
            break
        if new == 0:
            status = "BUG"
            info["stuck_on"] = "no new clause"
            break
        if any(not c for c in clauses[-new:]):
            status = "INFEASIBLE"
            info["why"] = "a point no option covers"
            break
        enc.flush(s)
        if time.time() - last_save > 90:
            save()
            last_save = time.time()
    save(final=True)
    try:
        s.delete()
    except Exception:
        pass
    return info


def _worker(tag, deadline, cache, solver_name, g_cache):
    try:
        cegar_h(tag, deadline, cache, solver_name, g_cache)
    except Exception as e:  # report it; the other tiers keep going
        import traceback
        with open(os.path.join(cache, "err_%s.txt" % tag), "w", encoding="utf-8") as f:
            f.write("%r\n%s" % (e, traceback.format_exc()[-600:]))


def _line(tag, r):
    bu = r.get("best_unc")
    return "%s n=%s st=%s it=%s cls=%s best=%s src=%s t=%ss" % (
        tag, r.get("n"), r.get("status"), r.get("iterations_total"), r.get("n_clauses"),
        "%.2e" % bu if bu is not None else "-", r.get("src"), round(r.get("seconds_total", 0)))


def g_cache_line(path):
    st = rs._load(path, {})
    out = []
    for tag in rg.ORDER_G:
        r = st.get(tag)
        if r:
            out.append("%s=%s/%s/%ss" % (tag, r.get("status"), r.get("iterations_total"),
                                         round(r.get("seconds_total", 0))))
            if r.get("status") == "FOUND" and tag != "g2H":
                c = r.get("cert", {})
                out.append("[G-RULE %s n=%s sweep=%s endpoints=%s %s]" % (
                    tag, c.get("n"), c.get("sweep"), c.get("endpoints"), r.get("rule")))
    return "13cache " + " ".join(out)


def probe_h(tiers=ORDER_H, budget=520, cache=None, g_cache=None, max_procs=6,
            slice_s=SLICE_S):
    """Run every open tier in its own process until the budget ends; report (summary last)."""
    t_end = time.time() + budget
    cache = cache or os.path.join(tempfile.gettempdir(), "mv2-slr-rules-h1")
    g_cache = g_cache or os.path.join(tempfile.gettempdir(), "mv2-slr-rules-g1", "tiers.json")
    os.makedirs(cache, exist_ok=True)
    lines = []
    ok, note = ensure_pysat()
    lines.append("pysat ok=%s %s" % (ok, note[:160]))
    name = pick_solver() if ok else None
    lines.append("solver=%s" % name)
    try:
        lines.append(g_cache_line(g_cache))
    except Exception as e:
        lines.append("13cache error %r" % (e,))
    if name:
        ctx = multiprocessing.get_context("spawn")
        decided = ("FOUND", "INFEASIBLE", "BUG")

        def queue_order():
            q = []
            for i, tag in enumerate(tiers):
                r = rs._load(os.path.join(cache, "s_%s.json" % tag), {})
                if r.get("status") not in decided:
                    q.append((r.get("seconds_total", 0.0), i, tag))
            return [t for _s, _i, t in sorted(q)]

        pending = queue_order()
        running = []
        turns = 0
        while time.time() < t_end:
            alive = []
            for t, p in running:
                if p.is_alive():
                    alive.append((t, p))
                else:
                    r = rs._load(os.path.join(cache, "s_%s.json" % t), {})
                    crashed = os.path.exists(os.path.join(cache, "err_%s.txt" % t))
                    if r.get("status") not in decided and t not in pending and not crashed:
                        pending.append(t)  # its turn is over: back of the queue
            running = alive
            busy = set(t for t, _p in running)
            while pending and len(running) < max_procs and t_end - time.time() > 60:
                tag = pending.pop(0)
                if tag in busy:
                    continue
                dl = min(t_end - 25, time.time() + slice_s)
                p = ctx.Process(target=_worker, args=(tag, dl, cache, name, g_cache))
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
    else:  # no SAT solver here: resume route 13 (CP-SAT) on its open tiers instead
        left = t_end - time.time() - 20
        if left > 60:
            rep = rg.probe_g([("g3N", left / 2), ("g4N", left / 2)], budget=left)
            lines.append("FALLBACK-13 " + rep.replace("\n", " | ")[-700:])
    for tag in tiers:
        ep = os.path.join(cache, "err_%s.txt" % tag)
        if os.path.exists(ep):
            with open(ep, encoding="utf-8") as f:
                lines.append("ERROR %s %s" % (tag, f.read()[-300:].replace("\n", " | ")))
    states = {t: rs._load(os.path.join(cache, "s_%s.json" % t), {}) for t in tiers}
    for tag in tiers:  # details first; the gate keeps only the end of the output
        if states[tag]:
            lines.append(_line(tag, states[tag]))
    for tag in tiers:
        r = states[tag]
        if r.get("status") == "BUG":
            lines.append("BUG %s %s" % (tag, r.get("stuck_on")))
        if "hint_ok" in r:
            lines.append("S4 %s poliakova satisfies every clause: %s" % (tag, r["hint_ok"]))
    for tag in tiers:
        r = states[tag]
        if r.get("status") == "FOUND":
            c = r.get("cert", {})
            lines.append("RULE %s n=%s sweep=%s endpoints=%s %s" % (
                tag, c.get("n"), c.get("sweep"), c.get("endpoints"), r.get("rule")))
    lines.append("STATUS " + " ".join("%s=%s" % (t, states[t].get("status"))
                                      for t in tiers if states[t]))
    return "\n".join(lines)


def job_main(argv=None):
    """Compete driver (route-13 clauses are not available there, so it seeds from scratch)."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--minutes", type=float, default=180)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    rep = probe_h(budget=60.0 * a.minutes, cache=os.path.join(a.out_dir, "cache"),
                  g_cache=os.path.join(a.out_dir, "no-g-cache.json"))
    with open(os.path.join(a.out_dir, "report_h.txt"), "w", encoding="utf-8") as f:
        f.write(rep + "\n")
    print(rep)
    return rep


if __name__ == "__main__":
    job_main()
