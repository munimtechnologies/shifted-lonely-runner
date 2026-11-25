# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 5: best response over speed AND shift, for the open range 55 <= n <= 94.

Counterexamples to the shifted Lonely Runner Conjecture are now known for 5 <= n <= 17
(Blanco, Criado and Santos, arXiv:2603.24784), 18 <= n <= 54 (aadrianvv, published
2026-11-22 in github.com/1337isnot1337/solved-conjectures, results/
shifted-lonely-runner-counterexamples, unrefereed) and n >= 95 (Poliakova,
arXiv:2609.23952). This module attacks n = 55 upward:

  * `load_external` reads the published 18..54 certificates (list of {"n", "speeds",
    "shift_num", "shift_den", "gamma"}), and `verify_external` re-checks each one with
    MV2's own exact checkers (slr.py: covers_sweep and covers_endpoints, written before the
    external file was seen, plus slr_br.exact_cover at the recorded gamma).
  * `sbr_search` is best-response dynamics in which a runner may also change its SPEED: for
    the gaps the other runners leave at radius r, each candidate speed u gets its exact best
    shift (slr_br.best_shift), and the runner takes the (speed, shift) that covers the most.
    Radius continuation (shrink after every cover), small kicks, step halving.
  * `probe` warm-starts n from the published certificate for n - 1 plus the best added
    runner, and searches down to r = 0.999/(n+1).
  * `certify` rounds the shifts to k/10^6 (falling back to k/10^8, then the exact binary
    values) and re-checks the cover in exact rational arithmetic at R = 1/(n+1) - 1/10^11.
    Nothing is claimed unless this exact check passes.
The float search proves nothing by itself; it is deterministic for a given seed (a time
limit can only stop it early).
"""
import hashlib
import json
import math
import random
import time
import urllib.request
from fractions import Fraction as F

import slr_br

EXT_URL = ("https://raw.githubusercontent.com/1337isnot1337/solved-conjectures/main/"
           "results/shifted-lonely-runner-counterexamples/certificates.json")
TARGET = 0.999  # search radius = TARGET/(n+1); leaves room for rounding the shifts


# ---------------------------------------------------------------- external certificates
def load_external(src=EXT_URL, timeout=60):
    """Return ({n: {"n", "speeds", "shifts" (Fractions), "gamma" (Fraction)}}, sha256)."""
    if src.startswith("http"):
        req = urllib.request.Request(src, headers={"User-Agent": "slr-cert-check"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    else:
        with open(src, "rb") as fh:
            data = fh.read()
    out = {}
    for c in json.loads(data.decode("utf-8")):
        n = int(c["n"])
        q = int(c["shift_den"])
        out[n] = {"n": n, "speeds": [int(x) for x in c["speeds"]],
                  "shifts": [F(int(x), q) for x in c["shift_num"]],
                  "gamma": F(c["gamma"])}
    return out, hashlib.sha256(data).hexdigest()


def verify_external(certs):
    """Rows (n, basic_ok, sweep_ok, endpoints_ok, closed_cover_at_gamma) for each certificate.

    sweep_ok / endpoints_ok: the OPEN arcs of radius 1/(n+1) cover the circle, i.e.
    gamma(v; s) < 1/(n+1) (two independent exact checkers from slr.py).
    closed_cover_at_gamma: the closed arcs of the recorded radius gamma cover, i.e.
    gamma(v; s) <= recorded gamma.
    """
    import slr
    rows = []
    for n in sorted(certs):
        c = certs[n]
        v, s, g = c["speeds"], c["shifts"], c["gamma"]
        basic = (len(v) == n and len(s) == n and len(set(v)) == n and min(v) >= 1
                 and 0 < g < F(1, n + 1))
        a = slr.covers_sweep(v, s, F(1, n + 1))[0]
        b = slr.covers_endpoints(v, s, F(1, n + 1))[0]
        c_ok = slr_br.exact_cover(v, s, g)
        rows.append((n, basic, a, b, c_ok))
    return rows


# ---------------------------------------------------------------- float search
def runner_iv(v, s, r):
    out = []
    slr_br.float_intervals(v, s, r, out)
    return out


def gaps_except(ivs, skip):
    """Uncovered parts of [0, 1] left by every runner except index `skip` (-1: none)."""
    iv = []
    for j, lst in enumerate(ivs):
        if j != skip:
            iv.extend(lst)
    return slr_br.gaps_of(iv)


def unused_speeds(speeds, vmax):
    used = set(speeds)
    return [u for u in range(1, vmax + 1) if u not in used]


def best_move(k, speeds, g, r, rng, vmax, p_speed, n_cand):
    """Best (speed, shift) for runner k against the gaps g of the other runners.

    Returns (speed, shift, covered_measure, covered_measure_with_own_speed).
    With probability p_speed, n_cand random unused speeds in 1..vmax are also tried.
    """
    v = speeds[k]
    s, m = slr_br.best_shift(v, g, r, rng)
    best = (v, s, m)
    if p_speed > 0 and rng.random() < p_speed:
        pool = unused_speeds(speeds, vmax)
        for u in rng.sample(pool, min(n_cand, len(pool))):
            su, mu = slr_br.best_shift(u, g, r, rng)
            if mu > best[2] + 1e-13:
                best = (u, su, mu)
    return best[0], best[1], best[2], m


def br_sweeps(speeds, shifts, r, rng, sweeps, vmax, p_speed, n_cand):
    """Best-response sweeps (in place). True as soon as the closed arcs cover [0, 1]."""
    n = len(speeds)
    ivs = [runner_iv(v, s, r) for v, s in zip(speeds, shifts)]
    for _ in range(sweeps):
        order = list(range(n))
        rng.shuffle(order)
        for k in order:
            g = gaps_except(ivs, k)
            if not g:
                return True
            u, s, _, _ = best_move(k, speeds, g, r, rng, vmax, p_speed, n_cand)
            speeds[k], shifts[k] = u, s
            ivs[k] = runner_iv(u, s, r)
        if not gaps_except(ivs, -1):
            return True
    return False


def sbr_search(speeds, shifts, r_start, r_target, rng, deadline, vmax, p_speed=0.3,
               n_cand=40, step0=0.004, min_step=0.00025, sweeps_per_try=3):
    """Shrink the radius from r_start to r_target keeping a cover.

    Returns (best, stats); best = (r, speeds, shifts) for the smallest r at which a cover was
    found (float check), or None.
    """
    n = len(speeds)
    speeds = list(speeds)
    shifts = list(shifts)
    st = {"sweeps": 0, "kicks": 0, "restarts": 0, "best_r": None}
    best = None
    r = r_start
    step = step0
    fails = 0
    while time.time() < deadline:
        ok = br_sweeps(speeds, shifts, r, rng, sweeps_per_try, vmax, p_speed, n_cand)
        st["sweeps"] += sweeps_per_try
        if ok:
            best = (r, speeds[:], shifts[:])
            st["best_r"] = r
            if r <= r_target:
                break
            step = min(step0, step * 1.5)
            r = max(r_target, r * (1.0 - step))
            fails = 0
            continue
        fails += 1
        if fails % 3:
            shifts[rng.randrange(n)] = rng.random()
            continue
        if best is None:
            st["restarts"] += 1
            shifts = [rng.random() for _ in range(n)]
            continue
        speeds, shifts = best[1][:], best[2][:]
        if step > min_step:
            step /= 2.0
        else:
            st["kicks"] += 1
            for _ in range(2):
                shifts[rng.randrange(n)] = rng.random()
            if p_speed > 0 and rng.random() < 0.5:
                k = rng.randrange(n)
                pool = unused_speeds(speeds, vmax)
                if pool:
                    speeds[k] = rng.choice(pool)
                    shifts[k] = rng.random()
        r = max(r_target, best[0] * (1.0 - step))
    return best, st


def add_runner(speeds, shifts, r, rng, vmax):
    """Append the unused speed (<= vmax) and shift that cover most of the gaps at radius r."""
    ivs = [runner_iv(v, s, r) for v, s in zip(speeds, shifts)]
    g = gaps_except(ivs, -1)
    pool = unused_speeds(speeds, vmax)
    if not g:
        return speeds + [pool[0]], shifts + [rng.random()]
    best = None
    for u in pool:
        su, mu = slr_br.best_shift(u, g, r, rng)
        if best is None or mu > best[2] + 1e-13:
            best = (u, su, mu)
    return speeds + [best[0]], shifts + [best[1]]


# ---------------------------------------------------------------- exact certificate
def certify(speeds, shifts, digits=6):
    """Exact check at R = 1/(n+1) - 1/10^11 of rounded shifts. Returns a certificate or None."""
    n = len(speeds)
    if len(set(speeds)) != n or min(speeds) < 1:
        return None
    R = F(1, n + 1) - F(1, 10 ** 11)
    for d in (digits, digits + 2, None):
        if d is None:
            ex = [F(s) % 1 for s in shifts]
            q = 1
            for x in ex:
                q = q * x.denominator // math.gcd(q, x.denominator)
            nums = [int(x * q) for x in ex]
        else:
            q = 10 ** d
            nums = [int(round(s * q)) % q for s in shifts]
            ex = [F(k, q) for k in nums]
        if slr_br.exact_cover(speeds, ex, R):
            return {"n": n, "speeds": list(speeds), "shift_den": q, "shift_num": nums,
                    "radius": str(R)}
    return None


# ---------------------------------------------------------------- gate probe
def probe(n, seed=1, seconds=500, base_n=None, p_speed=0.3, n_cand=40, vmax=None, chain=2,
          src=EXT_URL):
    """Warm-start n from the published certificate for base_n (default n - 1); search down to
    TARGET/(n+1); on success certify, check with slr.py, and continue to n + 1 (up to `chain`
    certificates). Returns a compact text report (certificates last)."""
    import slr
    t0 = time.time()
    deadline = t0 + seconds
    certs, sha = load_external(src)
    base_n = base_n or n - 1
    b = certs[base_n]
    rng = random.Random(seed)
    speeds = list(b["speeds"])
    shifts = [float(x) for x in b["shifts"]]
    g = b["gamma"]
    vmax = vmax or max(240, max(speeds) + 24)
    lines = ["probe n=%d seed=%d p_speed=%s n_cand=%d vmax=%d base=%d E_base=%.4f sha=%s"
             % (n, seed, p_speed, n_cand, vmax, base_n, float(1 / g) - (base_n + 1), sha[:12])]
    r_start = float(g) * (1.0 + 1e-9)
    found = []
    m = n
    while time.time() < deadline and len(found) < chain:
        r_target = TARGET / (m + 1)
        while len(speeds) < m:
            speeds, shifts = add_runner(speeds, shifts, r_target, rng, vmax)
        best, st = sbr_search(speeds, shifts, r_start, r_target, rng, deadline, vmax,
                              p_speed=p_speed, n_cand=n_cand)
        if best is None:
            lines.append("n=%d no cover even at the start radius %r" % (m, st))
            break
        r_b = best[0]
        lines.append("n=%d best_ratio=%.5f E=%.4f sweeps=%d kicks=%d t=%.0f"
                     % (m, r_b * (m + 1), 1 / r_b - (m + 1), st["sweeps"], st["kicks"],
                        time.time() - t0))
        if r_b > r_target:
            break
        cert = certify(best[1], best[2])
        if cert is None:
            lines.append("n=%d exact check FAILED" % m)
            break
        ex = [F(k, cert["shift_den"]) for k in cert["shift_num"]]
        a = slr.covers_sweep(cert["speeds"], ex, F(1, m + 1))[0]
        bb = slr.covers_endpoints(cert["speeds"], ex, F(1, m + 1))[0]
        lines.append("n=%d CERTIFIED sweep=%d endpoints=%d" % (m, a, bb))
        found.append(cert)
        speeds, shifts = best[1][:], best[2][:]
        r_start = r_b
        m += 1
    lines.append("seconds=%.0f" % (time.time() - t0))
    for c in found:
        lines.append("C%d V:%s" % (c["n"], ",".join(str(x) for x in c["speeds"])))
        lines.append("C%d S/%d:%s" % (c["n"], c["shift_den"],
                                      ",".join(str(x) for x in c["shift_num"])))
    return "\n".join(lines)
