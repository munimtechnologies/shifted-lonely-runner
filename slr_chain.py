# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 7: a warm chain n -> n + 1 -> ... from the exact n = 55 certificate (certs_lp.json).

Each step adds one runner to the best certified configuration, then lowers the loneliness with
route 6's minimax polish (slr_lp.slp_polish: all shifts move together, difference constraints)
and speed-swap / rigid-time-shift moves, in parallel worker processes that start from different
new speeds. A worker stops as soon as its loneliness is below 1/(n + 1 + e_stop). A step counts
only if slr_sbr.certify (exact, closed arcs of radius 1/(n+1) - 10^-11, shifts rounded to
10^-6) and both exact checkers of slr.py (open arcs of radius 1/(n+1)) accept it.

Certificates are printed compactly: speeds in decimal, shifts as numerators over D written in
base 36 with a fixed width (decode_shifts). Every certified step is also appended to a state
file in the system temp folder, so a later probe on the same machine continues from the highest
certified n; every configuration read from there is re-checked exactly before it is used.
Nothing read from the state file is ever reported as new without passing the exact checks.
"""
import json
import os
import random
import tempfile
import time
from fractions import Fraction as F

import slr
import slr_br
import slr_lp
import slr_sbr

B36 = "0123456789abcdefghijklmnopqrstuvwxyz"
HERE = os.path.dirname(os.path.abspath(__file__))
CERTS = os.path.join(HERE, "certs_lp.json")
STATE = os.path.join(tempfile.gettempdir(), "mv2-slr-chain", "certs.json")


# ---------------------------------------------------------------- compact encoding
def width_for(den):
    w = 1
    while 36 ** w < den:
        w += 1
    return w


def encode_shifts(nums, den):
    w = width_for(den)
    out = []
    for k in nums:
        if not 0 <= k < den:
            raise ValueError("numerator out of range")
        d = []
        for _ in range(w):
            k, r = divmod(k, 36)
            d.append(B36[r])
        out.append("".join(reversed(d)))
    return "".join(out)


def decode_shifts(text, den, n):
    w = width_for(den)
    if len(text) != w * n:
        raise ValueError("expected %d characters, got %d" % (w * n, len(text)))
    nums = [int(text[i * w:(i + 1) * w], 36) for i in range(n)]
    if any(k >= den for k in nums):
        raise ValueError("numerator out of range")
    return nums


def cert_lines(c):
    return ["C%d V:%s" % (c["n"], ",".join(str(x) for x in c["speeds"])),
            "C%d D:%d S36:%s" % (c["n"], c["shift_den"],
                                 encode_shifts(c["shift_num"], c["shift_den"]))]


# ---------------------------------------------------------------- certificates on disk
def _norm(c):
    n = int(c["n"])
    den = int(c["shift_den"])
    if "shift_num" in c:
        nums = [int(x) for x in c["shift_num"]]
    else:
        nums = decode_shifts(c["shift_b36"], den, n)
    return {"n": n, "speeds": [int(x) for x in c["speeds"]], "shift_den": den,
            "shift_num": nums}


def read_certs(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return [_norm(c) for c in json.load(fh)]
    except (OSError, ValueError, KeyError, TypeError):
        return []


def exact_ok(c, full=False):
    """Exact check that c is a counterexample for its n (open arcs of radius 1/(n+1) cover)."""
    n, v, den, nums = c["n"], c["speeds"], c["shift_den"], c["shift_num"]
    if len(v) != n or len(nums) != n or len(set(v)) != n or min(v) < 1:
        return False
    if not all(0 <= k < den for k in nums):
        return False
    s = [F(k, den) for k in nums]
    R = F(1, n + 1)
    if not slr.covers_sweep(v, s, R)[0]:
        return False
    return slr.covers_endpoints(v, s, R)[0] if full else True


def best_base(paths):
    """Highest-n configuration among the files that passes the exact check, and its file."""
    pool = []
    for p in paths:
        for c in read_certs(p):
            pool.append((c["n"], p, c))
    pool.sort(key=lambda x: -x[0])
    for n, p, c in pool:
        if exact_ok(c):
            return c, p
    return None, None


def save_state(c, path=STATE):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        old = read_certs(path)
        old = [x for x in old if x["n"] != c["n"]] + [c]
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(old, fh)
        os.replace(tmp, path)
        return True
    except OSError:
        return False


# ---------------------------------------------------------------- one worker
def worker(task):
    """task: n, base_speeds, base_shifts (floats), add (speeds to add first), seed, seconds,
    vmax, pool, g_stop. Stops early once the loneliness is at most g_stop."""
    t0 = time.time()
    deadline = t0 + task["seconds"]
    rng = random.Random(task["seed"])
    n, vmax, g_stop = task["n"], task["vmax"], task["g_stop"]
    speeds = list(task["base_speeds"])
    shifts = list(task["base_shifts"])
    r_t = 0.999 / (n + 1)
    adds = list(task.get("add") or [])
    while len(speeds) < n:
        if adds:
            u = adds.pop(0)
            gp = slr_lp.gaps_except(speeds, shifts, r_t, -1)
            su = slr_br.best_shift(u, gp, r_t, rng)[0] if gp else rng.random()
        else:
            _, u, su = slr_lp.rank_new_runner(speeds, shifts, r_t, rng, vmax)[0]
        speeds.append(u)
        shifts.append(su)
    g = g0 = slr_lp.gamma(speeds, shifts)
    st = {"calls": 0, "acc": 0, "moves": 0, "kept": 0}
    polish_until = t0 + task["seconds"] * task.get("polish_frac", 0.45)
    while g > g_stop and time.time() < polish_until:
        sh, g1, s1 = slr_lp.slp_polish(speeds, shifts, g=g, max_iter=6,
                                       seconds=max(1.0, min(60.0, polish_until - time.time())))
        st["calls"] += 1
        st["acc"] += s1["accepted"]
        better = g1 < g
        shifts, g = sh, g1
        if not better or s1["pinned"]:
            break
    g1_end = g
    pool = task.get("pool")
    while g > g_stop and time.time() < deadline:
        st["moves"] += 1
        sp, sh = speeds[:], shifts[:]
        if rng.random() < 0.25:
            tau = (rng.random() - 0.5) * 2.0 * g / max(sp)
            for k in range(n):
                if rng.random() < 0.3:
                    sh[k] = (sh[k] - sp[k] * tau) % 1.0
        else:
            k = rng.randrange(n)
            r = 0.999 * g
            gp = slr_lp.gaps_except(sp, sh, r, k)
            cands = [sp[k]]
            pl = [u for u in (pool or slr_lp.unused(sp, vmax)) if u not in sp]
            cands += rng.sample(pl, min(24, len(pl)))
            best = None
            for u in cands:
                if not gp:
                    best = (1.0, u, sh[k])
                    break
                su, mu = slr_br.best_shift(u, gp, r, rng)
                if best is None or mu > best[0] + 1e-13:
                    best = (mu, u, su)
            sp[k], sh[k] = best[1], best[2]
        g2 = slr_lp.gamma(sp, sh)
        rem = deadline - time.time()
        if rem <= 0:
            break
        sh, g2, _ = slr_lp.slp_polish(sp, sh, g=g2, seconds=min(rem, 30.0), max_iter=25)
        if g2 < g * (1.0 - 1e-12):
            speeds, shifts, g = sp, sh, g2
            st["kept"] += 1
    return {"n": n, "seed": task["seed"], "add": task.get("add"),
            "E0": 1.0 / g0 - (n + 1), "E1": 1.0 / g1_end - (n + 1), "E": 1.0 / g - (n + 1),
            "st": st, "speeds": speeds, "shifts": shifts, "gamma": g,
            "seconds": round(time.time() - t0)}


def run_workers(tasks, workers):
    """Run tasks in a spawn pool; return as soon as one worker reaches its g_stop.
    Falls back to the first task alone in this process if the pool cannot start."""
    if workers > 1:
        try:
            import multiprocessing as mp
            ctx = mp.get_context("spawn")
            out = []
            with ctx.Pool(workers) as p:
                for r in p.imap_unordered(worker, tasks):
                    out.append(r)
                    if r["gamma"] <= tasks[0]["g_stop"]:
                        break
            return out, "pool%d" % workers
        except Exception as e:  # pragma: no cover - depends on the host
            note = "serial(%s:%s)" % (type(e).__name__, str(e)[:50])
    else:
        note = "serial"
    return [worker(tasks[0])], note


# ---------------------------------------------------------------- one chain step
def step(base, n_new, seconds, workers, seed, vmax=240, pool=None, e_stop=0.15, offset=0):
    """Try to certify n_new from the certified configuration `base`. Returns (cert|None, info).
    Worker w starts from the (offset + w + 1)-th best-ranked new speed."""
    sp = list(base["speeds"])
    sh = [float(F(k, base["shift_den"])) for k in base["shift_num"]]
    rng = random.Random(seed)
    ranked = slr_lp.rank_new_runner(sp, sh, 0.999 / (n_new + 1), rng, vmax)
    off = offset % max(1, len(ranked))
    tasks = [{"n": n_new, "base_speeds": sp, "base_shifts": sh,
              "add": [ranked[(off + w) % len(ranked)][1]], "seed": seed * 100 + w,
              "seconds": seconds, "vmax": vmax, "pool": pool,
              "g_stop": 1.0 / (n_new + 1 + e_stop)} for w in range(workers)]
    res, mode = run_workers(tasks, workers)
    best = min(res, key=lambda r: r["gamma"])
    info = {"mode": mode, "n": n_new, "E": best["E"], "res": res}
    if best["gamma"] >= 1.0 / (n_new + 1):
        return None, info
    c = slr_sbr.certify(best["speeds"], best["shifts"])
    if c is None:
        info["fail"] = "certify"
        return None, info
    cert = {"n": n_new, "speeds": list(c["speeds"]), "shift_den": c["shift_den"],
            "shift_num": list(c["shift_num"])}
    if not exact_ok(cert, full=True):
        info["fail"] = "slr checkers"
        return None, info
    return cert, info


# ---------------------------------------------------------------- gate probe
def chain(seconds=470, workers=4, seed=1, vmax=240, pool=None, e_stop=0.15, step_max=240,
          max_steps=4, paths=None, state=STATE):
    """Continue the chain from the highest certified n; return a text report whose last lines
    are the new certificates (compact form)."""
    import os as _os
    t0 = time.time()
    paths = paths or [CERTS, state]
    base, src = best_base(paths)
    if base is None:
        return "chain: no valid base certificate in %s" % paths
    cpu = _os.cpu_count() or 1
    workers = max(1, min(workers, cpu - 2))
    lines = ["chain seed=%d base n=%d from %s cpu=%d workers=%d e_stop=%.2f"
             % (seed, base["n"], "repo" if src == paths[0] else "state", cpu, workers, e_stop)]
    found = []
    tries = 0
    fails = 0  # failed attempts at the current n: the next attempt starts from lower-ranked speeds
    while len(found) < max_steps:
        left = t0 + seconds - 12 - time.time()
        if left < 45:
            break
        tries += 1
        n_new = base["n"] + 1
        cert, info = step(base, n_new, min(step_max, left), workers, seed * 10 + tries, vmax,
                          pool, e_stop, offset=fails * workers)
        Es = ",".join("%.3f" % r["E"] for r in info["res"])
        lines.append("step n=%d %s E_best=%.4f Es=[%s] %s t=%d"
                     % (n_new, info["mode"], info["E"], Es,
                        "CERTIFIED" if cert else "no" + ("(" + info.get("fail", "") + ")"
                                                         if info.get("fail") else ""),
                        round(time.time() - t0)))
        if cert:
            saved = save_state(cert, state)
            found.append(cert)
            base = cert
            fails = 0
            if not saved:
                lines.append("state not saved")
        else:
            fails += 1
    hi = found[-1]["n"] if found else None
    lines.append("CHAIN new=%d highest=%s" % (len(found), hi))
    for c in found:
        lines.extend(cert_lines(c))
    return "\n".join(lines)


def show(ns, state=STATE):
    """Report the state-file certificates for the given n (each re-checked exactly)."""
    out = []
    certs = {c["n"]: c for c in read_certs(state)}
    out.append("state %s has n=%s" % (state, sorted(certs)))
    for n in ns:
        c = certs.get(n)
        if c is None:
            out.append("n=%d missing" % n)
        elif not exact_ok(c, full=True):
            out.append("n=%d FAILS exact check" % n)
        else:
            out.extend(cert_lines(c))
    return "\n".join(out)
