# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 8: simulated annealing of whole-circle coverage on a bitset time grid.

Shifted Lonely Runner problem: speeds v_i and shifts s_i form a counterexample for n runners
when the open bad arcs {t : ||v_i t + s_i|| < 1/(n+1)} cover the time circle R/Z.

Route 7 (slr_chain.py) added one runner to the n = 55 certificate and polished; it stalled at
E = 1/gamma - 57 = -0.76 for n = 56. aadrianvv's annealer (issue 110 of
1337isnot1337/solved-conjectures) reached n = 54 by annealing a grid count of uncovered
cells with speed moves. This module does that in standard-library Python, fast enough for the
publish test gate, by storing each runner's bad set as one big integer of G bits:

- the time circle is cut into G cells; cell c is "covered" by a runner if its centre
  (c + 1/2)/G is inside one of the runner's arcs of radius r (the search radius);
- runner i with speed v and integer offset k covers rot(B_v, k), where B_v is the mask of
  speed v at offset 0, i.e. ||v (t - k/G)|| < r; so its shift is s = -v k / G (mod 1);
- coverage counts are kept bit-sliced in NB big integers (a ripple-carry counter), so a
  move's change in the number U of uncovered cells costs a handful of big-integer
  operations (implemented in C inside Python).

Search moves: push (move the runner whose arc edge is nearest to a random uncovered cell just
far enough to cover it), small jitter, random-runner push, and speed swap (a new unused speed
aimed at an uncovered cell). Metropolis acceptance on U with a cyclic geometric temperature.
When U = 0 the grid solution is converted to exact shifts, its true loneliness is computed
(slr_lp.gamma), polished (slr_lp.slp_polish), and certified (slr_sbr.certify, then both exact
checkers of slr.py via slr_chain.exact_ok). If the float loneliness is still not below
1/(n+1), the search radius is tightened and the annealing continues.

Nothing found on the grid is ever claimed; only the exact checks count.
"""
import math
import random
import time
from fractions import Fraction as F

import slr_chain
import slr_lp
import slr_sbr

NB = 7  # counter planes: coverage counts up to 127 (more than any n in the open range)

try:
    (1).bit_count()

    def popcount(x):
        return x.bit_count()
except AttributeError:  # pragma: no cover - Python < 3.10
    def popcount(x):
        return bin(x).count("1")


# ---------------------------------------------------------------- masks
def base_mask(v, r, G):
    """Bits c (0 <= c < G) with ||v (c + 1/2) / G|| < r (float arithmetic; search only)."""
    M = 0
    for m in range(v):
        lo = math.floor(G * (m - r) / v - 0.5) + 1
        hi = math.ceil(G * (m + r) / v - 0.5) - 1
        if hi < lo:
            continue
        if lo < 0:
            M |= (1 << (hi + 1)) - 1
            M |= ((1 << (-lo)) - 1) << (G + lo)
        elif hi >= G:
            M |= ((1 << (G - lo)) - 1) << lo
            M |= (1 << (hi - G + 1)) - 1
        else:
            M |= ((1 << (hi - lo + 1)) - 1) << lo
    return M


class Grid:
    """Grid of G cells at search radius r, with a cache of offset-0 masks per speed."""

    def __init__(self, G, r):
        self.G = G
        self.r = r
        self.FULL = (1 << G) - 1
        self.cache = {}

    def base(self, v):
        M = self.cache.get(v)
        if M is None:
            M = base_mask(v, self.r, self.G)
            self.cache[v] = M
        return M

    def mask(self, v, k):
        M = self.base(v)
        k %= self.G
        if k == 0:
            return M
        return ((M << k) | (M >> (self.G - k))) & self.FULL


def to_off(v, s, G):
    """Grid offset k whose shift -v k / G is closest to s (mod 1) among multiples of 1/G."""
    return int(round(G * ((-s) % 1.0) / v)) % G


def to_shift(v, k, G):
    """Exact shift of a runner of speed v at grid offset k."""
    return F((-v * k) % G, G)


# ---------------------------------------------------------------- bit-sliced coverage counts
class Cover:
    def __init__(self, grid, speeds, offs):
        self.g = grid
        self.sp = list(speeds)
        self.k = [int(x) % grid.G for x in offs]
        self.P = [0] * NB
        self.M = [grid.mask(v, k) for v, k in zip(self.sp, self.k)]
        for M in self.M:
            self._add(M)
        self._refresh()

    def _add(self, c):
        P = self.P
        for j in range(NB):
            if not c:
                return
            t = P[j] & c
            P[j] ^= c
            c = t
        if c:
            raise OverflowError("coverage count above 2^NB - 1")

    def _sub(self, b):
        P = self.P
        for j in range(NB):
            if not b:
                return
            t = b & ~P[j]
            P[j] ^= b
            b = t
        if b:
            raise ValueError("negative coverage count")

    def _refresh(self):
        P = self.P
        hi = 0
        for j in range(1, NB):
            hi |= P[j]
        self.C = P[0] | hi
        self.ONE = P[0] & ~hi
        self.UNC = self.g.FULL ^ self.C
        self.U = popcount(self.UNC)

    def trial(self, i, Mn):
        """Number of uncovered cells if runner i's mask became Mn."""
        Cm = self.C ^ (self.M[i] & self.ONE)
        return self.g.G - popcount(Cm | Mn)

    def commit(self, i, v, k, Mn):
        self._sub(self.M[i])
        self._add(Mn)
        self.M[i] = Mn
        self.sp[i] = v
        self.k[i] = k % self.g.G
        self._refresh()

    def rand_unc(self, rng):
        """A random uncovered cell (the first one at or after a uniform position), or None."""
        if not self.U:
            return None
        p = rng.randrange(self.g.G)
        x = self.UNC >> p
        if x:
            return p + (x & -x).bit_length() - 1
        x = self.UNC
        return (x & -x).bit_length() - 1

    def shifts(self):
        return [to_shift(v, k, self.g.G) for v, k in zip(self.sp, self.k)]

    def count_naive(self):
        """(U, ONE) recomputed from the masks (tests)."""
        G = self.g.G
        cnt = [0] * G
        for M in self.M:
            for c in range(G):
                if (M >> c) & 1:
                    cnt[c] += 1
        U = sum(1 for x in cnt if x == 0)
        one = 0
        for c in range(G):
            if cnt[c] == 1:
                one |= 1 << c
        return U, one


# ---------------------------------------------------------------- moves
def push_target(cov, c, rng, top):
    """(i, k): runner i (random among the `top` needing the smallest move) moved so that its
    nearest arc just covers cell c."""
    G = cov.g.G
    r = cov.g.r
    cands = []
    for i, (v, k) in enumerate(zip(cov.sp, cov.k)):
        P = G / v
        x = (c - k) % G
        d = x - round(x / P) * P
        half = r * P
        delta = d - math.copysign(half, d)
        cands.append((abs(delta), i, delta))
    if top < len(cands):
        cands.sort()
        _, i, delta = cands[rng.randrange(top)]
    else:
        _, i, delta = cands[rng.randrange(len(cands))]
    margin = 0.5 + 2.5 * rng.random()
    move = delta + math.copysign(margin, delta)
    return i, int(round(cov.k[i] + move)) % G


JITTER = (1, 1, 2, 3, 5, 8, 13, 21, 34)


def anneal_loop(cov, rng, deadline, vmax, iters=None, T_hi=8.0, T_lo=0.3, cycle=6000,
                p=(0.55, 0.20, 0.15, 0.10), on_zero=None):
    """Anneal cov in place until U = 0 (then call on_zero(cov); stop if it returns True),
    the deadline, or `iters` moves. Returns stats; cov ends at the best state seen."""
    n = len(cov.sp)
    G = cov.g.G
    best_U = cov.U
    best = (cov.sp[:], cov.k[:])
    st = {"it": 0, "acc": 0, "U0": cov.U, "zeros": 0, "restores": 0}
    a1, a2, a3 = p[0], p[0] + p[1], p[0] + p[1] + p[2]
    ratio = T_lo / T_hi
    while True:
        if iters is not None and st["it"] >= iters:
            break
        if (st["it"] & 63) == 0 and time.time() > deadline:
            break
        if cov.U == 0:
            st["zeros"] += 1
            if on_zero is None or on_zero(cov):
                best_U, best = 0, (cov.sp[:], cov.k[:])
                break
            best_U, best = cov.U, (cov.sp[:], cov.k[:])  # on_zero changed the radius
            continue
        it = st["it"]
        st["it"] += 1
        ph = it % cycle
        if ph == 0 and it and cov.U > best_U and rng.random() < 0.5:
            cov.__init__(cov.g, best[0], best[1])
            st["restores"] += 1
        T = T_hi * ratio ** (ph / cycle)
        a = rng.random()
        if a < a1 or a >= a3:
            c = cov.rand_unc(rng)
        if a < a1:
            i, k = push_target(cov, c, rng, 3)
            u = cov.sp[i]
        elif a < a2:
            i = rng.randrange(n)
            u = cov.sp[i]
            k = (cov.k[i] + rng.choice(JITTER) * (1 if rng.random() < 0.5 else -1)) % G
        elif a < a3:
            c = cov.rand_unc(rng)
            i, k = push_target(cov, c, rng, n)
            u = cov.sp[i]
        else:
            i = rng.randrange(n)
            used = set(cov.sp)
            u = rng.randint(1, vmax)
            tries = 0
            while u in used and tries < 50:
                u = rng.randint(1, vmax)
                tries += 1
            if u in used:
                continue
            half = max(1, int(cov.g.r * G / u))
            k = (c + rng.randint(-half, half)) % G
        Mn = cov.g.mask(u, k)
        dU = cov.trial(i, Mn) - cov.U
        if dU <= 0 or rng.random() < math.exp(-dU / T):
            cov.commit(i, u, k, Mn)
            st["acc"] += 1
            if cov.U < best_U:
                best_U, best = cov.U, (cov.sp[:], cov.k[:])
    if cov.U > best_U:
        cov.__init__(cov.g, best[0], best[1])
    st["U"] = cov.U
    return st


# ---------------------------------------------------------------- new runners
def rank_new(cov, rng, vmax, samples=16):
    """[(gain, u, k)] over unused speeds u <= vmax: uncovered cells covered by u at the best
    of `samples` offsets aimed at uncovered cells; sorted by decreasing gain."""
    used = set(cov.sp)
    G = cov.g.G
    out = []
    for u in range(1, vmax + 1):
        if u in used:
            continue
        half = max(1, int(cov.g.r * G / u))
        best = (-1, 0)
        for _ in range(samples):
            c = cov.rand_unc(rng)
            k = rng.randrange(G) if c is None else (c + rng.randint(-half, half)) % G
            gain = popcount(cov.g.mask(u, k) & cov.UNC)
            if gain > best[0]:
                best = (gain, k)
        out.append((best[0], u, best[1]))
    out.sort(key=lambda x: (-x[0], x[1]))
    return out


# ---------------------------------------------------------------- continuous finish
def finish(speeds, shifts, polish_s=30.0):
    """True loneliness of (speeds, float shifts), polished; certificate if below 1/(n+1).
    Returns (cert or None, E, shifts)."""
    n = len(speeds)
    g = slr_lp.gamma(speeds, shifts)
    if polish_s > 0:
        shifts, g, _ = slr_lp.slp_polish(speeds, shifts, g=g, seconds=polish_s)
    E = 1.0 / g - (n + 1)
    if g >= 1.0 / (n + 1):
        return None, E, shifts
    c = slr_sbr.certify(speeds, shifts)
    if c is None:
        return None, E, shifts
    cert = {"n": n, "speeds": list(c["speeds"]), "shift_den": c["shift_den"],
            "shift_num": list(c["shift_num"])}
    if not slr_chain.exact_ok(cert):
        return None, E, shifts
    return cert, E, shifts


# ---------------------------------------------------------------- one worker
def worker(task):
    """task: n, base_speeds, base_shifts (floats, n - 1 or n of them), rank, seed, seconds,
    G, e_g, e_step, vmax, T_hi, T_lo, cycle. Returns a summary dict (cert if found)."""
    t0 = time.time()
    deadline = t0 + task["seconds"]
    rng = random.Random(task["seed"])
    n, G, vmax = task["n"], task["G"], task["vmax"]
    st_all = {"e_g": task["e_g"], "E_best": None, "cert": None, "finishes": 0}
    grid = Grid(G, 1.0 / (n + 1 + task["e_g"]))
    sp = [int(x) for x in task["base_speeds"]]
    offs = [to_off(v, s, G) for v, s in zip(sp, task["base_shifts"])]
    added = None
    while len(sp) < n:
        cov = Cover(grid, sp, offs)
        ranked = rank_new(cov, rng, vmax)
        _, u, k = ranked[task.get("rank", 0) % len(ranked)]
        added = u
        sp.append(u)
        offs.append(k)
    cov = Cover(grid, sp, offs)
    U_start = cov.U

    def on_zero(c):
        st_all["finishes"] += 1
        sh = [float(x) for x in c.shifts()]
        left = deadline - time.time()
        cert, E, _ = finish(c.sp, sh, polish_s=max(2.0, min(30.0, left - 5.0)))
        if st_all["E_best"] is None or E > st_all["E_best"]:
            st_all["E_best"] = E
        if cert is not None:
            st_all["cert"] = cert
            return True
        st_all["e_g"] += task.get("e_step", 0.15)
        c.g = Grid(G, 1.0 / (n + 1 + st_all["e_g"]))
        c.__init__(c.g, c.sp, c.k)
        return False

    st = anneal_loop(cov, rng, deadline - task.get("reserve", 25.0), vmax,
                     T_hi=task.get("T_hi", 8.0), T_lo=task.get("T_lo", 0.3),
                     cycle=task.get("cycle", 6000), on_zero=on_zero)
    E_end = None
    if st_all["cert"] is None:
        left = deadline - time.time()
        cert, E_end, _ = finish(cov.sp, [float(x) for x in cov.shifts()],
                                polish_s=max(2.0, left - 5.0))
        if cert is not None:
            st_all["cert"] = cert
        if st_all["E_best"] is None or E_end > st_all["E_best"]:
            st_all["E_best"] = E_end
    return {"n": n, "seed": task["seed"], "added": added, "U_start": U_start,
            "U_end": cov.U, "it": st["it"], "acc": st["acc"], "zeros": st["zeros"],
            "e_g": st_all["e_g"], "E_best": st_all["E_best"], "E_end": E_end,
            "cert": st_all["cert"], "speeds": cov.sp, "seconds": round(time.time() - t0)}


def run_pool(tasks, workers):
    """Run worker() over tasks; return as soon as one returns a certificate."""
    if workers > 1:
        try:
            import multiprocessing as mp
            ctx = mp.get_context("spawn")
            out = []
            with ctx.Pool(workers) as p:
                for r in p.imap_unordered(worker, tasks):
                    out.append(r)
                    if r["cert"] is not None:
                        break
            return out, "pool%d" % workers
        except Exception as e:  # pragma: no cover - depends on the host
            return [], "poolfail(%s:%s)" % (type(e).__name__, str(e)[:60])
    return [worker(tasks[0])], "serial"


# ---------------------------------------------------------------- gate probe
def chain(seconds=470, workers=6, seed=1, G=1 << 20, e_g=0.3, e_step=0.15, vmax=240,
          step_max=440, max_steps=4, T_hi=(4.0, 8.0, 16.0), paths=None,
          state=slr_chain.STATE):
    """Continue from the highest certified n (repo certs_lp.json or the gate's state file),
    one runner at a time. Returns a text report whose last lines are new certificates."""
    import os
    t0 = time.time()
    paths = paths or [slr_chain.CERTS, state]
    base, src = slr_chain.best_base(paths)
    if base is None:
        return "grid: no valid base certificate in %s" % paths
    cpu = os.cpu_count() or 1
    workers = max(1, min(workers, cpu - 2))
    lines = ["grid seed=%d base n=%d from %s cpu=%d workers=%d G=2^%d e_g=%.2f"
             % (seed, base["n"], "repo" if src == paths[0] else "state", cpu, workers,
                G.bit_length() - 1, e_g)]
    found = []
    tries = 0
    fails = 0
    while len(found) < max_steps:
        left = t0 + seconds - 10 - time.time()
        if left < 60:
            break
        tries += 1
        n_new = base["n"] + 1
        sh = [float(F(k, base["shift_den"])) for k in base["shift_num"]]
        tasks = [{"n": n_new, "base_speeds": base["speeds"], "base_shifts": sh,
                  "rank": fails * workers + w, "seed": seed * 1000 + tries * 10 + w,
                  "seconds": min(step_max, left), "G": G, "e_g": e_g, "e_step": e_step,
                  "vmax": vmax, "T_hi": T_hi[w % len(T_hi)], "T_lo": 0.3, "cycle": 6000}
                 for w in range(workers)]
        res, mode = run_pool(tasks, workers)
        if not res:
            lines.append("step n=%d %s t=%d" % (n_new, mode, round(time.time() - t0)))
            break
        cert = None
        for r in res:
            if r["cert"] is not None and slr_chain.exact_ok(r["cert"], full=True):
                cert = r["cert"]
                break
        Es = ",".join("%.3f" % r["E_best"] if r["E_best"] is not None else "nan"
                      for r in res)
        lines.append("step n=%d %s Es=[%s] U=[%s] it=[%s] add=[%s] %s t=%d"
                     % (n_new, mode, Es, ",".join("%d>%d" % (r["U_start"], r["U_end"])
                                                  for r in res),
                        ",".join(str(r["it"]) for r in res),
                        ",".join(str(r["added"]) for r in res),
                        "CERTIFIED" if cert else "no", round(time.time() - t0)))
        if cert:
            if not slr_chain.save_state(cert, state):
                lines.append("state not saved")
            found.append(cert)
            base = cert
            fails = 0
        else:
            fails += 1
    lines.append("GRID new=%d highest=%s" % (len(found), found[-1]["n"] if found else None))
    for c in found:
        lines.extend(slr_chain.cert_lines(c))
    return "\n".join(lines)
