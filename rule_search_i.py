# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 14 (PREREG_rules_i.md): fixed-n searches for shifted Lonely Runner counterexamples at
smooth N inside the open range (n = 58..62, 64..94), on bases of multiples of m = 2, 3, 4, 6.

Route 13b (rule_search_h.py) asked the same question with an incremental SAT solver; it made no
CEGAR iteration in about 300 s per tier and failed its sanity tier (RESULTS_rules_h.md). Route 14
goes back to route 13's CP-SAT CEGAR (rule_search_g.cegar_g: same menu, same point clauses, same
exact checks and certification), which did make progress, and changes three things:

* New tiers: smooth N in or next to the open range (Callens's n = 63, Zenodo 24051700, uses
  N = 64), bases of multiples of 2, 3, 4 and 6, all with P = {2, 3, 5}.
* Solver hint for even m: Poliakova's 9 -> 8 rule (arXiv:2609.23952) scaled by k = m/2.
  Multiplying every speed of a cover by k keeps it a cover with the same shifts (v k t + s at
  time t equals v t' + s at t' = k t), so at N = 96 the scaled rule is a 95-runner cover on the
  base m, 2m, ..., 96m; at smaller N it is only a starting point. A hint never changes what the
  solver may answer, so it cannot affect soundness.
* Tiers take turns of SLICE_S seconds in up to 3 processes with 2 CP-SAT workers each,
  least-searched first; each tier's clauses and time limit are cached between turns and probes.
"""
import multiprocessing
import os
import tempfile
import time

import rule_search_g as rg
import rule_search_s as rs

_POLIAKOVA = rg.poliakova_cand  # the m = 2 rule; kept before any per-process override

# tag: (m, n, N, P, scaled Poliakova hint?)
TIERS_I = {
    "s4H": (4, 95, 96, rg.P5, True),     # sanity: scaled Poliakova is a cover here; must be FOUND
    "e6N72": (6, 71, 72, rg.P5, True),
    "e4N72": (4, 71, 72, rg.P5, True),
    "e2N72": (2, 71, 72, rg.P5, True),
    "e4N80": (4, 79, 80, rg.P5, True),
    "e2N80": (2, 79, 80, rg.P5, True),
    "e3N81": (3, 80, 81, rg.P5, False),
    "e6N90": (6, 89, 90, rg.P5, True),
    "e6N75": (6, 74, 75, rg.P5, True),
    "e6N60": (6, 59, 60, rg.P5, True),
    "e4N60": (4, 59, 60, rg.P5, True),
    "e3N72": (3, 71, 72, rg.P5, False),
    "e2G64": (2, 62, 64, rg.P5, True),   # gain 2 at N = 64
}
ORDER_I = ["s4H", "e6N72", "e4N80", "e6N90", "e6N60", "e4N72", "e2N72", "e2N80", "e3N81",
           "e6N75", "e4N60", "e3N72", "e2G64"]
SLICE_S = 150
OPEN = set(range(58, 63)) | set(range(64, 95))


def scaled_poliakova(m, N):
    """Poliakova's rule (rule_search_g.poliakova_cand) with every speed multiplied by m/2."""
    if m % 2:
        raise ValueError("only even m")
    k = m // 2
    c = _POLIAKOVA(N)
    return {"removed": [k * w for w in c["removed"]],
            "rephased": {k * w: S for w, S in c["rephased"].items()},
            "added": {k * a: S for a, S in c["added"].items()}}


def hint_in_menu(m, N, P):
    """Which parts of the scaled hint lie in the tier's menu (for the tests and the report)."""
    touch, _fixed, added = rg.pools_g(m, N, P)
    _Md, shifts = rg.shift_menu(N)
    h = scaled_poliakova(m, N)
    sh = set(shifts)
    return {"removed": [w for w in h["removed"] if w in touch],
            "rephased": {w: S for w, S in h["rephased"].items() if w in touch and S in sh},
            "added": {a: S for a, S in h["added"].items() if a in added and S in sh}}


def _register(tag):
    """Make rule_search_g see the tier (in this process only)."""
    m, n, N, P, hint = TIERS_I[tag]
    rg.TIERS_G[tag] = (m, n, N, P, "poliakova" if hint else None, "search")
    if hint:
        rg.poliakova_cand = lambda N_, _m=m: scaled_poliakova(_m, N_)


def _worker(tag, deadline, cache, workers):
    path = os.path.join(cache, "t_%s.json" % tag)
    try:
        ok, note = rs.ensure_ortools()
        if not ok:
            raise RuntimeError("ortools: " + note)
        _register(tag)
        prev = rs._load(path, {})
        info = rg.cegar_g(tag, deadline, workers=workers, prev=prev)
        info["iterations_total"] = info["iterations"] + prev.get("iterations_total", 0)
        info["seconds_total"] = round(info["seconds"] + prev.get("seconds_total", 0), 1)
        info["turns"] = prev.get("turns", 0) + 1
        info["seeded"] = prev.get("seeded", info.get("seeded"))
        if info["status"] == "FOUND":
            rs._save(os.path.join(cache, "cert_%s.json" % tag), info["cert"])
        rs._save(path, info)
    except Exception as e:  # report it; the other tiers keep going
        import traceback
        with open(os.path.join(cache, "err_%s.txt" % tag), "w", encoding="utf-8") as f:
            f.write("%r\n%s" % (e, traceback.format_exc()[-600:]))


def line_i(tag, r):
    return "%s n=%s N=%s m=%s st=%s it=%s cls=%s tl=%s t=%ss turns=%s" % (
        tag, r.get("n"), r.get("N"), r.get("m"), r.get("status"), r.get("iterations_total"),
        r.get("n_clauses"), int(r.get("tl", 0)), round(r.get("seconds_total", 0)),
        r.get("turns"))


def h_cache_line(hdir):
    """One line with route 13b's cached state (probe H3's report was lost)."""
    out = []
    solver = None
    try:
        names = sorted(os.listdir(hdir))
    except Exception:
        return "13b none"
    for fn in names:
        if fn.startswith("s_") and fn.endswith(".json"):
            r = rs._load(os.path.join(hdir, fn), {})
            solver = solver or r.get("solver")
            out.append("%s=%s/%s/%ss" % (fn[2:-5], (r.get("status") or "?")[:3],
                                        r.get("iterations_total"),
                                        round(r.get("seconds_total") or 0)))
        elif fn.startswith("err_"):
            out.append("ERR:" + fn[4:-4])
    return "13b solver=%s %s" % (solver, " ".join(out))


def probe_i(tiers=ORDER_I, budget=520, cache=None, procs=3, workers=2, slice_s=SLICE_S):
    """Run the open tiers in turns until the budget ends; report with the summary last."""
    t_end = time.time() + budget
    cache = cache or os.path.join(tempfile.gettempdir(), "mv2-slr-rules-i1")
    os.makedirs(cache, exist_ok=True)
    lines = [h_cache_line(os.path.join(tempfile.gettempdir(), "mv2-slr-rules-h1"))]
    ok, note = rs.ensure_ortools()
    lines.append("ortools ok=%s %s" % (ok, note[:80]))
    decided = ("FOUND", "INFEASIBLE", "BUG")
    turns = 0
    if ok:
        ctx = multiprocessing.get_context("spawn")

        def state(tag):
            return rs._load(os.path.join(cache, "t_%s.json" % tag), {})

        def crashed(tag):
            return os.path.exists(os.path.join(cache, "err_%s.txt" % tag))

        def queue():
            q = []
            for i, tag in enumerate(tiers):
                r = state(tag)
                if r.get("status") not in decided and not crashed(tag):
                    q.append((r.get("seconds_total", 0.0), i, tag))
            return [t for _s, _i, t in sorted(q)]

        pending = queue()
        running = []
        while time.time() < t_end:
            alive = []
            for t, p in running:
                if p.is_alive():
                    alive.append((t, p))
                elif state(t).get("status") not in decided and not crashed(t):
                    pending.append(t)  # its turn is over: back of the queue
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
    states = {t: rs._load(os.path.join(cache, "t_%s.json" % t), {}) for t in tiers}
    for tag in tiers:
        ep = os.path.join(cache, "err_%s.txt" % tag)
        if os.path.exists(ep):
            with open(ep, encoding="utf-8") as f:
                lines.append("ERROR %s %s" % (tag, f.read()[-300:].replace("\n", " | ")))
    for tag in tiers:  # details first; the gate keeps only the end of the output
        if states[tag]:
            lines.append(line_i(tag, states[tag]))
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
    rep = probe_i(budget=60.0 * a.minutes, cache=os.path.join(a.out_dir, "cache"))
    with open(os.path.join(a.out_dir, "report_i.txt"), "w", encoding="utf-8") as f:
        f.write(rep + "\n")
    print(rep)
    return rep


if __name__ == "__main__":
    job_main()
