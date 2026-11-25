# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 9: a slack-carrying chain on consecutive speeds 1, 2, ..., n.

Shifted Lonely Runner problem: speeds v_i and shifts s_i form a counterexample for n runners
when every time t has some runner with ||v_i t + s_i|| < 1/(n+1). Write the loneliness as
gamma = 1/(n + 1 + E); a counterexample needs E > 0.

Why consecutive speeds. Blanco, Criado and Santos (arXiv:2603.24784, Table 2) computed the
exact optimum for the speeds 1..n up to n = 15. It has E = 1 at n = 8 and E = 2 at n = 11, 13
and 15 (1/gamma = 10, 14, 16, 18). The published annealed counterexamples for 18 <= n <= 56
have E between 0.015 and 0.98, and upward chains stall at n = 57 because every added runner
costs about one unit of E. This route keeps the speeds fixed at 1..n. It starts from the exact
n = 11 optimum (E = 2) and adds runner n + 1 at each step, then raises E as far as it can
(target `e_stop`) before moving on. If E stays near its small-n optimum, every step starts
with slack.

Each step runs `workers` processes. Each one places runner n against the gaps of the others,
polishes all shifts together (route 6, slr_lp.slp_polish), then anneals the bitset grid of
route 8 (slr_grid) with the speeds frozen. Its radius rises in a ladder: whenever the grid is
covered, the configuration is polished in continuous time, its true E is recorded, and the grid
radius shrinks. A step counts only if slr_sbr.certify (exact rational check at
1/(n+1) - 10^-11 of the rounded shifts) and both exact checkers of slr.py accept it.
Certified steps are kept in a state file in the system temp folder, so the next probe on
the same machine continues from them. Anything read back from that file is re-checked exactly
before it is used.
"""
import json
import os
import random
import tempfile
import time
from fractions import Fraction as F

import slr_br
import slr_chain
import slr_grid as SG
import slr_lp
import slr_sbr

STATE = os.path.join(tempfile.gettempdir(), "mv2-slr-consec", "consec.json")

# Blanco-Criado-Santos, repository criado/shifted_lonely_runner_conjecture_counterexample,
# output/consecutive.out: speeds 1..11, loneliness 1/14 (E = 2).
BCS11 = ["0", "244337/355740", "160527/237160", "55/84", "127/336", "39/56", "3649/40656",
         "2/21", "79/112", "163/168", "52727/64680"]
# arXiv:2603.24784, Figure 1: speeds 1..5, shifts (0, 46, 38, 47, 72)/94, loneliness 15/94.
BCS5 = [0, 46, 38, 47, 72]


def grid_size(n):
    """Power of two G >= 300 n^2 (about 2^20 at n = 56, as in route 8)."""
    G = 1 << 12
    while G < 300 * n * n:
        G <<= 1
    return G


def E_of(g, n):
    return 1.0 / g - (n + 1)


def bcs_checks():
    """(bcs5_exact, bcs11_closed_cover_at_1/14): exact checks of the published values."""
    v5 = [1, 2, 3, 4, 5]
    s5 = [F(k, 94) for k in BCS5]
    ok5 = (slr_br.exact_cover(v5, s5, F(15, 94))
           and not slr_br.exact_cover(v5, s5, F(15, 94) - F(1, 10 ** 7)))
    ok11 = slr_br.exact_cover(list(range(1, 12)), [F(x) for x in BCS11], F(1, 14))
    return bool(ok5), bool(ok11)


# ---------------------------------------------------------------- state file
def load_state(path=STATE):
    """{n: (cert, E)} for the consecutive-speed certificates saved by earlier probes."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    out = {}
    for c in data if isinstance(data, list) else []:
        try:
            n = int(c["n"])
            cert = {"n": n, "speeds": list(range(1, n + 1)), "shift_den": int(c["shift_den"]),
                    "shift_num": [int(x) for x in c["shift_num"]]}
            out[n] = (cert, float(c.get("E", 0.0)))
        except (KeyError, TypeError, ValueError):
            continue
    return out


def save_state(cert, E, path=STATE):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        old = load_state(path)
        if cert["n"] in old and old[cert["n"]][1] >= E:
            return True
        old[cert["n"]] = (cert, E)
        rows = [{"n": n, "shift_den": c["shift_den"], "shift_num": c["shift_num"], "E": e}
                for n, (c, e) in sorted(old.items())]
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(rows, fh)
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def certify_consec(n, shifts):
    """Exact certificate for speeds 1..n with these float shifts, or None."""
    c = slr_sbr.certify(list(range(1, n + 1)), shifts)
    if c is None:
        return None
    cert = {"n": n, "speeds": list(range(1, n + 1)), "shift_den": c["shift_den"],
            "shift_num": list(c["shift_num"])}
    return cert if slr_chain.exact_ok(cert, full=True) else None


# ---------------------------------------------------------------- one worker
def worker(task):
    """task: n, shifts (n - 1 or n floats), seed, seconds, e_stop, e_prev, [G, T_hi, reserve].
    Returns the best E found (continuous, float) and its shifts."""
    t0 = time.time()
    n, seed = task["n"], task["seed"]
    deadline = t0 + task["seconds"]
    reserve = task.get("reserve", 5.0)
    e_stop = task["e_stop"]
    G = task.get("G") or grid_size(n)
    rng = random.Random(seed)
    speeds = list(range(1, n + 1))
    sh = [float(x) % 1.0 for x in task["shifts"]]
    if len(sh) < n:
        e_prev = max(0.0, float(task.get("e_prev", 0.0)))
        r0 = 1.0 / (n + e_prev + 0.2 + 0.15 * (seed % 7))
        gp = slr_lp.gaps_except(speeds[:-1], sh, r0, -1)
        sh.append(slr_br.best_shift(n, gp, r0, rng)[0] if gp else rng.random())
    g = slr_lp.gamma(speeds, sh)
    left = deadline - reserve - time.time()
    sh, g, _ = slr_lp.slp_polish(speeds, sh, g=g,
                                 seconds=max(0.5, min(task.get("polish0", 10.0), left)))
    best = [E_of(g, n), list(sh)]
    E0 = best[0]
    st = {"it": 0, "zeros": 0}
    e_g = [max(best[0] + 0.1, 0.05)]
    if best[0] < e_stop and deadline - reserve - time.time() > 2.0:
        grid = SG.Grid(G, 1.0 / (n + 1 + e_g[0]))
        cov = SG.Cover(grid, speeds, [SG.to_off(v, s, G) for v, s in zip(speeds, sh)])

        def on_zero(c):
            st["zeros"] += 1
            lft = deadline - reserve - time.time()
            shf = [float(x) for x in c.shifts()]
            gt = slr_lp.gamma(c.sp, shf)
            sht, gt, _ = slr_lp.slp_polish(c.sp, shf, g=gt, seconds=max(0.2, min(8.0, lft)))
            Et = E_of(gt, n)
            if Et > best[0]:
                best[0], best[1] = Et, list(sht)
            if best[0] >= e_stop or lft < 1.0:
                return True
            e_g[0] = max(Et + 0.1, e_g[0] + 0.05)
            c.g = SG.Grid(G, 1.0 / (n + 1 + e_g[0]))
            c.__init__(c.g, c.sp, [SG.to_off(v, s, G) for v, s in zip(c.sp, sht)])
            return False

        a = SG.anneal_loop(cov, rng, deadline - reserve, n, T_hi=task.get("T_hi", 8.0),
                           T_lo=0.3, cycle=task.get("cycle", 6000), p=(0.6, 0.25, 0.15, 0.0),
                           on_zero=on_zero)
        st["it"] = a["it"]
        lft = deadline - time.time() - 1.0
        if best[0] < e_stop and lft > 1.0:
            shf = [float(x) for x in cov.shifts()]
            gt = slr_lp.gamma(speeds, shf)
            sht, gt, _ = slr_lp.slp_polish(speeds, shf, g=gt, seconds=min(lft, 4.0))
            if E_of(gt, n) > best[0]:
                best[0], best[1] = E_of(gt, n), list(sht)
    return {"n": n, "seed": seed, "E0": E0, "E": best[0], "shifts": best[1], "it": st["it"],
            "zeros": st["zeros"], "e_g": e_g[0], "seconds": round(time.time() - t0)}


def run_pool(tasks, workers, e_stop):
    """Run worker() over tasks; stop as soon as one reaches e_stop. Falls back to one task
    in this process if the pool cannot start."""
    if workers > 1:
        try:
            import multiprocessing as mp
            ctx = mp.get_context("spawn")
            out = []
            with ctx.Pool(workers) as p:
                for r in p.imap_unordered(worker, tasks):
                    out.append(r)
                    if r["E"] >= e_stop:
                        break
            return out, "pool%d" % workers
        except Exception as e:  # pragma: no cover - depends on the host
            note = "serial(%s)" % type(e).__name__
    else:
        note = "serial"
    return [worker(tasks[0])], note


# ---------------------------------------------------------------- gate probe
def chain(seconds=470, workers=6, seed=1, e_stop=1.0, step_max=120, state=STATE, max_fails=2):
    """Continue the consecutive-speed chain from the highest certified n in the state file
    (or from the exact n = 11 optimum of Blanco-Criado-Santos). Returns a text report whose
    last line is the top certificate (speeds 1..n implicit; shifts numerators in base 36)."""
    t0 = time.time()
    cpu = os.cpu_count() or 1
    workers = max(1, min(workers, cpu - 2))
    ok5, ok11 = bcs_checks()
    base = None
    saved = load_state(state)
    for m in sorted(saved, reverse=True):
        cert, _ = saved[m]
        if slr_chain.exact_ok(cert):
            base = (m, [float(F(k, cert["shift_den"])) for k in cert["shift_num"]], "state")
            break
    if base is None and ok11:
        base = (11, [float(F(x)) for x in BCS11], "bcs11")
    if base is None:
        base = (4, [0.0] * 4, "zero")
    n, sh, src = base
    E_prev = E_of(slr_lp.gamma(list(range(1, n + 1)), sh), n)
    lines = ["consec seed=%d bcs5=%s bcs11=%s start n=%d from %s E=%.3f states=%s cpu=%d "
             "workers=%d e_stop=%.2f step_max=%d"
             % (seed, ok5, ok11, n, src, E_prev, len(saved), cpu, workers, e_stop, step_max)]
    top = None
    fails = 0
    while fails < max_fails:
        left = t0 + seconds - 10 - time.time()
        if left < 20:
            break
        n_new = n + 1
        sec = min(step_max, left)
        tasks = [{"n": n_new, "shifts": sh, "seed": seed * 100000 + n_new * 100 + fails * 10 + w,
                  "seconds": sec, "e_stop": e_stop, "e_prev": E_prev,
                  "T_hi": (4.0, 8.0, 16.0)[w % 3]} for w in range(workers)]
        res, mode = run_pool(tasks, workers, e_stop)
        best = max(res, key=lambda r: r["E"])
        cert = certify_consec(n_new, best["shifts"]) if best["E"] > 0 else None
        lines.append("n=%d E=%.3f E0=%.2f Es=[%s] it=%dk %s t=%d %s"
                     % (n_new, best["E"], best["E0"], ",".join("%.2f" % r["E"] for r in res),
                        max(r["it"] for r in res) // 1000, mode, round(time.time() - t0),
                        "C" if cert else "no"))
        if cert:
            save_state(cert, best["E"], state)
            top = (cert, best["E"])
            n, sh, E_prev = n_new, best["shifts"], best["E"]
            fails = 0
        else:
            fails += 1
    lines.append("CONSEC top=%s" % (top[0]["n"] if top else None))
    if top:
        c, E = top
        lines.append("K%d E=%.4f D:%d S36:%s" % (c["n"], E, c["shift_den"],
                                                 slr_chain.encode_shifts(c["shift_num"],
                                                                         c["shift_den"])))
    return "\n".join(lines)


def show(ns, state=STATE):
    """Report saved certificates for the given n (each re-checked exactly)."""
    saved = load_state(state)
    out = ["state has n=%s" % sorted(saved)]
    for m in ns:
        if m not in saved:
            out.append("n=%d missing" % m)
            continue
        c, E = saved[m]
        if not slr_chain.exact_ok(c, full=True):
            out.append("n=%d FAILS exact check" % m)
        else:
            out.append("K%d E=%.4f D:%d S36:%s" % (m, E, c["shift_den"],
                                                   slr_chain.encode_shifts(c["shift_num"],
                                                                           c["shift_den"])))
    return "\n".join(out)
