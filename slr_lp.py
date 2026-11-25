# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 6: minimax polish of the loneliness by sequential difference-constraint programs.

Shifted Lonely Runner problem: for speeds v_i and shifts s_i, the loneliness is
    gamma(v; s) = max_t min_i ||v_i t + s_i||,
and a configuration with gamma < 1/(n+1) is a counterexample for n runners. Open range
(2026-11-25): 55 <= n <= 94 (5..17 Blanco-Criado-Santos arXiv:2603.24784; 18..54 aadrianvv,
github.com/1337isnot1337/solved-conjectures, unrefereed; n >= 95 Poliakova arXiv:2609.23952).

The search used so far in this repository (best response, slr_br/slr_sbr) moves one runner at a
time and stalls at 55 runners near 1/gamma - 56 = -0.26. At a local optimum the loneliness is
held up by many holes at once, so all shifts have to move together. This module does that.

Key observation. Changing the shift of runner i by Delta moves ALL of its bad arcs rigidly in
time by x_i = -Delta / v_i. A hole of radius r (a gap between the end of an arc of runner L at a
and the start of an arc of runner R at b) has peak height at most
    h = r + (b - a) * w,   w = v_L v_R / (v_L + v_R),
(exact when no third runner dips inside it), and after the move
    h' = h + w (x_R - x_L).
So "every hole at most z" is a system of DIFFERENCE constraints x_R - x_L <= (z - h)/w, plus a
trust box |x_i| <= rho_i. Feasibility is a shortest-path problem (Bellman-Ford), the smallest
feasible z is found by bisection, and no LP solver is needed. The box rho_i = kappa*gamma/(2 v_i)
guarantees that no point below r_low = gamma (1 - kappa) can rise above gamma (1 - kappa/2).
Every step is accepted only if the loneliness, recomputed from scratch by bisection on exact
coverage tests, really drops. Nothing is claimed unless slr_sbr.certify (exact rational check)
and the two independent checkers of slr.py accept the rounded certificate.
"""
import math
import random
import time
from fractions import Fraction as F

import slr_br


# ---------------------------------------------------------------- holes and loneliness
def arcs(speeds, shifts, r):
    """Closed bad arcs of radius r as (start, end, runner), start in [0, 1), sorted."""
    out = []
    for i, (v, s) in enumerate(zip(speeds, shifts)):
        h = r / v
        w = 2.0 * h
        for m in range(v):
            st = ((m - s) / v - h) % 1.0
            out.append((st, st + w, i))
    out.sort()
    return out


def holes(speeds, shifts, r):
    """Gaps of the closed arcs of radius r on the circle, as (a, b, L, R), a < b.

    L is the runner whose arc ends at a, R the runner whose arc starts at b. Coordinates are
    on a lap starting at the smallest arc start x0 (so a, b lie in [x0, x0 + 1]).
    """
    A = arcs(speeds, shifts, r)
    x0, cur, own = A[0]
    for st, en, i in A:
        if en - 1.0 > cur:
            cur, own = en - 1.0, i
    g = []
    for st, en, i in A[1:]:
        if st > cur:
            g.append((cur, st, own, i))
            cur, own = en, i
        elif en > cur:
            cur, own = en, i
    if cur < x0 + 1.0:
        g.append((cur, x0 + 1.0, own, A[0][2]))
    return g


def hole_heights(speeds, holes_list, r):
    """(L, R, h, w) for every hole; w = 0 marks a hole bounded by one runner on both sides."""
    out = []
    for a, b, L, R in holes_list:
        if L == R:
            out.append((L, R, r + (b - a) * speeds[L] / 2.0, 0.0))
        else:
            w = speeds[L] * speeds[R] / (speeds[L] + speeds[R])
            out.append((L, R, r + (b - a) * w, w))
    return out


def gamma(speeds, shifts, lo=None, hi=None, tol=1e-15):
    """Loneliness max_t min_i ||v_i t + s_i|| by bisection on exact float coverage tests."""
    n = len(speeds)
    if lo is None or not holes(speeds, shifts, lo):
        lo = 0.999 / (2.0 * n)  # 2 n r < 1: the arcs cannot cover
    if hi is None or holes(speeds, shifts, hi):
        hi = 0.5
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if holes(speeds, shifts, mid):
            lo = mid
        else:
            hi = mid
    return hi


def gamma_near(speeds, shifts, g_ref, kappa=0.02):
    """Loneliness, bracketed from the holes at g_ref (1 - kappa) (faster than gamma())."""
    r_low = g_ref * (1.0 - kappa)
    hl = holes(speeds, shifts, r_low)
    if not hl:
        return gamma(speeds, shifts, hi=r_low)
    hi = max(h for _, _, h, _ in hole_heights(speeds, hl, r_low)) * (1.0 + 1e-12)
    return gamma(speeds, shifts, lo=r_low, hi=hi)


# ---------------------------------------------------------------- difference constraints
def feasible(n, cons, rho, z):
    """x with x_R - x_L <= (z - h)/w for (L, R, h, w) in cons and |x_i| <= rho_i, or None.

    Bellman-Ford from a source S with edges S->i (rho_i), i->S (rho_i), L->R ((z-h)/w).
    """
    d = list(rho)
    E = [(L, R, (z - h) / w) for L, R, h, w in cons]
    for _ in range(n + 2):
        changed = False
        for L, R, c in E:
            t = d[L] + c
            if t < d[R]:
                d[R] = t
                changed = True
        for i in range(n):
            if d[i] + rho[i] < 0.0:
                return None
        if not changed:
            return d
    return None


def min_z(n, cons, rho, z_lo, z_hi, iters=36):
    """Smallest z in [z_lo, z_hi] (bisection) with a feasible x. Returns (x, z) or (None, None)."""
    x = feasible(n, cons, rho, z_hi)
    if x is None:
        return None, None
    best = (x, z_hi)
    lo, hi = z_lo, z_hi
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        y = feasible(n, cons, rho, mid)
        if y is None:
            lo = mid
        else:
            hi = mid
            best = (y, mid)
        if hi - lo <= 1e-16:
            break
    return best


def slp_polish(speeds, shifts, g=None, seconds=60.0, max_iter=10 ** 9, kappa=0.01,
               kappa_max=0.05, kappa_min=1e-7):
    """Lower the loneliness of (speeds, shifts) by sequential difference-constraint steps.

    Returns (shifts, gamma, stats). gamma never increases (every step is re-checked).
    """
    n = len(speeds)
    shifts = list(shifts)
    if g is None:
        g = gamma(speeds, shifts)
    deadline = time.time() + seconds
    st = {"iters": 0, "accepted": 0, "pinned": False}
    while st["iters"] < max_iter and kappa > kappa_min and time.time() < deadline:
        st["iters"] += 1
        r_low = g * (1.0 - kappa)
        hh = hole_heights(speeds, holes(speeds, shifts, r_low), r_low)
        z_lo = r_low
        cons = []
        for L, R, h, w in hh:
            if w == 0.0:
                z_lo = max(z_lo, h)
            else:
                cons.append((L, R, h, w))
        if z_lo >= g:
            st["pinned"] = True
            break
        z_hi = max([h for _, _, h, _ in cons] + [z_lo])
        rho = [kappa * g / (2.0 * v) for v in speeds]
        x, z = min_z(n, cons, rho, z_lo, z_hi)
        if x is None or z >= g * (1.0 - 1e-13):
            kappa *= 0.5
            continue
        new = [(s - v * xi) % 1.0 for s, v, xi in zip(shifts, speeds, x)]
        g_new = gamma_near(speeds, new, g, kappa=2.0 * kappa)
        if g_new < g * (1.0 - 1e-13):
            shifts, g = new, g_new
            st["accepted"] += 1
            kappa = min(kappa_max, kappa * 1.6)
        else:
            kappa *= 0.5
    return shifts, g, st


# ---------------------------------------------------------------- speed moves
def unused(speeds, vmax):
    used = set(speeds)
    return [u for u in range(1, vmax + 1) if u not in used]


def gaps_except(speeds, shifts, r, skip):
    iv = []
    for j, (v, s) in enumerate(zip(speeds, shifts)):
        if j != skip:
            slr_br.float_intervals(v, s, r, iv)
    return slr_br.gaps_of(iv)


def rank_new_runner(speeds, shifts, r, rng, vmax):
    """All unused speeds u <= vmax with their best shift against the gaps at radius r,
    sorted by the measure left uncovered: [(left, u, shift), ...]."""
    g = gaps_except(speeds, shifts, r, -1)
    tot = sum(b - a for a, b in g)
    out = []
    for u in unused(speeds, vmax):
        if not g:
            out.append((0.0, u, rng.random()))
            continue
        su, mu = slr_br.best_shift(u, g, r, rng)
        out.append((tot - mu, u, su))
    out.sort()
    return out


def swap_search(speeds, shifts, g, rng, deadline, vmax, pool=None, n_cand=24,
                polish_iter=25, p_rigid=0.25):
    """Greedy speed-swap / rigid-shift search, each move followed by a short polish.

    Move A (prob 1 - p_rigid): runner k takes the speed u (from n_cand random unused speeds,
    or `pool`) and shift that best cover the gaps the others leave at radius 0.999 g.
    Move B (prob p_rigid): a random subset of runners moves rigidly in time,
    s_k -> s_k - v_k tau (aadrianvv's untried "unpinning" move).
    A move is kept only if the polished loneliness is lower.
    """
    n = len(speeds)
    speeds, shifts = list(speeds), list(shifts)
    st = {"moves": 0, "kept": 0}
    while time.time() < deadline:
        st["moves"] += 1
        sp, sh = speeds[:], shifts[:]
        if rng.random() < p_rigid:
            tau = (rng.random() - 0.5) * 2.0 * g / max(sp)
            for k in range(n):
                if rng.random() < 0.3:
                    sh[k] = (sh[k] - sp[k] * tau) % 1.0
        else:
            k = rng.randrange(n)
            r = 0.999 * g
            gp = gaps_except(sp, sh, r, k)
            cands = [sp[k]]
            pl = [u for u in (pool or unused(sp, vmax)) if u not in sp]
            cands += rng.sample(pl, min(n_cand, len(pl)))
            best = None
            for u in cands:
                if not gp:
                    best = (1.0, u, sh[k])
                    break
                su, mu = slr_br.best_shift(u, gp, r, rng)
                if best is None or mu > best[0] + 1e-13:
                    best = (mu, u, su)
            sp[k], sh[k] = best[1], best[2]
        g1 = gamma(sp, sh)
        rem = deadline - time.time()
        if rem <= 0:
            break
        sh, g1, _ = slp_polish(sp, sh, g=g1, seconds=min(rem, 30.0), max_iter=polish_iter)
        if g1 < g * (1.0 - 1e-12):
            speeds, shifts, g = sp, sh, g1
            st["kept"] += 1
    return speeds, shifts, g, st


# ---------------------------------------------------------------- one worker
def worker(task):
    """task: dict(n, base_speeds, base_shifts (floats), add (list of speeds to add or None),
    seed, seconds, vmax, pool). Returns a dict with the best configuration found."""
    t0 = time.time()
    deadline = t0 + task["seconds"]
    rng = random.Random(task["seed"])
    n = task["n"]
    vmax = task["vmax"]
    speeds = list(task["base_speeds"])
    shifts = list(task["base_shifts"])
    r_t = 0.999 / (n + 1)
    adds = list(task.get("add") or [])
    while len(speeds) < n:
        if adds:
            u = adds.pop(0)
            gp = gaps_except(speeds, shifts, r_t, -1)
            su = slr_br.best_shift(u, gp, r_t, rng)[0] if gp else rng.random()
        else:
            _, u, su = rank_new_runner(speeds, shifts, r_t, rng, vmax)[0]
        speeds.append(u)
        shifts.append(su)
    g0 = gamma(speeds, shifts)
    third = max(5.0, (deadline - time.time()) / 3.0)
    shifts, g1, st1 = slp_polish(speeds, shifts, g=g0, seconds=third)
    speeds, shifts, g2, st2 = swap_search(speeds, shifts, g1, rng, deadline, vmax,
                                          pool=task.get("pool"))
    return {"n": n, "seed": task["seed"], "add": task.get("add"),
            "E0": 1.0 / g0 - (n + 1), "E1": 1.0 / g1 - (n + 1), "E2": 1.0 / g2 - (n + 1),
            "slp": st1, "swap": st2, "speeds": speeds, "shifts": shifts, "gamma": g2,
            "seconds": round(time.time() - t0)}


def run_tasks(tasks, workers, deadline):
    """Run worker() over tasks with a spawn pool; if the pool fails, run the first task alone
    in this process for the time that is left."""
    if workers > 1:
        try:
            import multiprocessing as mp
            ctx = mp.get_context("spawn")
            with ctx.Pool(workers) as p:
                return p.map(worker, tasks), "pool%d" % workers
        except Exception as e:  # pragma: no cover - depends on the host
            note = "serial(%s:%s)" % (type(e).__name__, str(e)[:60])
    else:
        note = "serial"
    t = dict(tasks[0])
    t["seconds"] = max(5.0, deadline - time.time())
    return [worker(t)], note


# ---------------------------------------------------------------- gate probe
def probe(n=55, base_n=54, seed=1, seconds=470, workers=4, vmax=240, pool=None, src=None,
          polish_base=True):
    """Warm start from the published certificate for base_n, add runners, polish, swap.

    Returns a text report; the best configuration (certificate if any) comes last.
    """
    import os
    import slr
    import slr_sbr
    t0 = time.time()
    certs, sha = slr_sbr.load_external(src or slr_sbr.EXT_URL)
    b = certs[base_n]
    sp = list(b["speeds"])
    sh = [float(x) for x in b["shifts"]]
    gb = gamma(sp, sh)
    lines = ["lp n=%d base=%d seed=%d vmax=%d sha=%s E_pub=%.5f (recorded %.5f)"
             % (n, base_n, seed, vmax, sha[:12], 1 / gb - (base_n + 1),
                float(1 / b["gamma"]) - (base_n + 1))]
    if polish_base:
        sh, gb2, stb = slp_polish(sp, sh, g=gb, seconds=40)
        lines.append("base polish E=%.5f iters=%d acc=%d pinned=%s"
                     % (1 / gb2 - (base_n + 1), stb["iters"], stb["accepted"], stb["pinned"]))
    cpu = os.cpu_count() or 1
    workers = max(1, min(workers, cpu - 2))
    rng = random.Random(seed)
    # worker w starts from the w-th best new speed (diversity); further runners greedily
    ranked = rank_new_runner(sp, sh, 0.999 / (n + 1), rng, vmax)
    off = (seed - 1) * workers
    adds = [[ranked[(off + w) % len(ranked)][1]] for w in range(workers)]
    deadline = t0 + seconds - 15
    left = deadline - time.time()
    tasks = [{"n": n, "base_speeds": sp, "base_shifts": sh, "add": adds[w],
              "seed": seed * 100 + w, "seconds": left, "vmax": vmax, "pool": pool}
             for w in range(workers)]
    res, mode = run_tasks(tasks, workers, deadline)
    lines.append("mode=%s cpu=%d" % (mode, cpu))
    for r in res:
        lines.append("w%d add=%s E0=%.4f E_slp=%.4f E_swap=%.4f it=%d swaps=%d/%d t=%d"
                     % (r["seed"] % 100, r["add"], r["E0"], r["E1"], r["E2"], r["slp"]["iters"],
                        r["swap"]["kept"], r["swap"]["moves"], r["seconds"]))
    best = min(res, key=lambda r: r["gamma"])
    E = 1 / best["gamma"] - (n + 1)
    lines.append("BEST n=%d E=%.5f ratio=%.6f" % (n, E, best["gamma"] * (n + 1)))
    if best["gamma"] < 1.0 / (n + 1):
        import slr_sbr as S
        cert = S.certify(best["speeds"], best["shifts"])
        if cert is None:
            lines.append("n=%d exact check FAILED" % n)
        else:
            ex = [F(k, cert["shift_den"]) for k in cert["shift_num"]]
            a = slr.covers_sweep(cert["speeds"], ex, F(1, n + 1))[0]
            bb = slr.covers_endpoints(cert["speeds"], ex, F(1, n + 1))[0]
            lines.append("n=%d CERTIFIED sweep=%d endpoints=%d" % (n, a, bb))
            lines.append("C%d V:%s" % (n, ",".join(str(x) for x in cert["speeds"])))
            lines.append("C%d S/%d:%s" % (n, cert["shift_den"],
                                          ",".join(str(x) for x in cert["shift_num"])))
            return "\n".join(lines)
    lines.append("B%d V:%s" % (n, ",".join(str(x) for x in best["speeds"])))
    lines.append("B%d S/1e9:%s" % (n, ",".join(str(int(round(s * 1e9)) % 10 ** 9)
                                              for s in best["shifts"])))
    return "\n".join(lines)
