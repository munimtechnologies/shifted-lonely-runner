# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 16 (PREREG_rules_k.md): continuous local search around the two structured covers.

Route 15 (descent_j.py) asked the same neighbour question exactly, over a finite menu of shifts,
and CP-SAT decided none of its five target tiers in two gate probes. This module drops
exactness of the search (never of the result): every shift is a real number, re-tuned by the
exact best response of slr._best_shift (the shift that covers the largest measure of what the
other runners leave open), with speed swaps and random kicks to leave local minima. A
configuration is reported only after both exact checkers of slr.py accept it at radius 1/(n+1),
padded to exactly n distinct speeds (descent_j.certify_j).

Tiers (n, start):
  cC63  calibration: Callens's 63 speeds with every shift random, radius 1/64. A known cover
        exists for these speeds; how often the search re-finds one measures the search.
  kC62  Callens's cover minus the runner whose deletion leaves the least uncovered measure at
        radius 1/63 (n = 62, open).
  kC61  the same, two runners deleted greedily, radius 1/62 (n = 61, open).
  kC64  Callens's cover plus the one added runner (speed <= 256, best shift) that leaves the
        least uncovered measure at radius 1/65 (n = 64, open).
  kP94  Poliakova's 95-runner cover on 2, 4, ..., 192 minus one runner, radius 1/95 (open).
Swaps may replace any runner by an unused speed up to twice the source's largest speed.
A search that ends without a cover proves nothing; its best uncovered measure is reported.
"""
import multiprocessing
import os
import random
import tempfile
import time
from fractions import Fraction as F

import descent_j as dj
import rule_search_s as rs
import slr

TIERS_K = {
    "cC63": ("C", 63, "rand"),
    "kC62": ("C", 62, "down"),
    "kC61": ("C", 61, "down"),
    "kC64": ("C", 64, "up"),
    "kP94": ("P", 94, "down"),
}
ORDER_K = ["cC63", "kC62", "kC61", "kC64", "kP94"]
DENOMS = (520, 1040, 1164, 2080, 2328, 4160, 4656, 8320, 1 << 14, 1 << 16, 1 << 18,
          1 << 20, 1 << 24, 1 << 32, 1 << 40, 1 << 48)
TOL = 1e-13
SHRINK = 1e-7  # the float search works at radius R (1 - SHRINK)


def source(src):
    """(speeds, float shifts) of Callens's 63 ('C') or Poliakova's 95 ('P') cover."""
    v, S, Dg = dj.c63() if src == "C" else dj.p95()
    return list(v), [x / Dg for x in S]


def arcs_of(v, s, r):
    return [slr._norm_arcs(v[i], float(s[i]) % 1.0, r) for i in range(len(v))]


def measure(v, s, r):
    """Float uncovered measure of the open arcs of radius r."""
    return slr._unc_measure(arcs_of(v, s, float(r)))


def n_gaps(v, s, r):
    allarcs = []
    for A in arcs_of(v, s, float(r)):
        allarcs.extend(A)
    return len(slr._gaps(allarcs))


def gaps_without(arcs, i):
    others = []
    for j, A in enumerate(arcs):
        if j != i:
            others.extend(A)
    return slr._gaps(others)


def init_down(src, n, rng=None):
    """Delete k - n runners greedily (least uncovered measure at radius 1/(n+1), source
    shifts kept). Returns (v, s, start) with start['m1'] the single-deletion minimum."""
    v, s = source(src)
    R = 1.0 / (n + 1)
    dels, m1, m = [], None, None
    while len(v) > n:
        best = None
        for i in range(len(v)):
            mi = measure(v[:i] + v[i + 1:], s[:i] + s[i + 1:], R)
            if best is None or mi < best[0]:
                best = (mi, i)
        m, i = best
        if m1 is None:
            m1 = m
        dels.append(v[i])
        del v[i]
        del s[i]
    return v, s, {"del": dels, "m0": m, "m1": m1}


def init_up(src, n, rng):
    """Add the one runner (unused speed <= 2 max(v), best shift) that leaves the least
    uncovered measure at radius 1/(n+1)."""
    v, s = source(src)
    r = 1.0 / (n + 1)
    g = slr._gaps([a for A in arcs_of(v, s, r) for a in A])
    gm = sum(b - a for a, b in g)
    have = set(v)
    best = None
    for w in range(1, 2 * max(v) + 1):
        if w in have:
            continue
        sh, ov = slr._best_shift(w, g, r, rng)
        res = gm - ov / w
        if best is None or res < best[0]:
            best = (res, w, sh)
    res, w, sh = best
    return v + [w], s + [sh], {"add": w, "m0": res, "m_src": gm}


def init_rand(src, n, rng):
    v, _s = source(src)
    s = [rng.random() for _ in v]
    return v, s, {"rand": True, "m0": measure(v, s, 1.0 / (n + 1))}


def init_tier(tag, rng):
    src, n, mode = TIERS_K[tag]
    if mode == "down":
        return init_down(src, n, rng)
    if mode == "up":
        return init_up(src, n, rng)
    return init_rand(src, n, rng)


def exact_ok(v, s, R):
    """Exact check A at radius R of the float shifts rounded to 1/2^48."""
    P = slr.quantize([float(x) % 1.0 for x in s])
    return slr.covers_sweep(v, [F(p, slr.Q) for p in P], R)[0]


def try_swap(v, s, arcs, r, rng, pool_max, unc, picks=6, sample=48):
    """Replace one of `picks` random runners by an unused speed with its best shift if that
    lowers the uncovered measure. Edits v, s, arcs in place; returns True on a swap."""
    have = set(v)
    pool = [w for w in range(1, pool_max + 1) if w not in have]
    if not pool:
        return False
    best = None
    for i in rng.sample(range(len(v)), min(picks, len(v))):
        g = gaps_without(arcs, i)
        if not g:
            return False
        gm = sum(b - a for a, b in g)
        for w in rng.sample(pool, min(sample, len(pool))):
            sh, ov = slr._best_shift(w, g, r, rng)
            res = gm - ov / w
            if best is None or res < best[0]:
                best = (res, i, w, sh)
    if best is not None and best[0] < unc * (1.0 - 1e-9):
        _res, i, w, sh = best
        v[i], s[i] = w, sh
        arcs[i] = slr._norm_arcs(w, sh, r)
        return True
    return False


def search_k(v, s, R, deadline, rng, pool_max, swap_p=0.5):
    """Best response on every shift, speed swaps and kicks until a float cover passes the
    exact check at R (status COVER) or the deadline (status NONE). Returns a dict."""
    v = list(v)
    s = [float(x) % 1.0 for x in s]
    n = len(v)
    r = float(R) * (1.0 - SHRINK)
    arcs = arcs_of(v, s, r)
    unc = slr._unc_measure(arcs)
    out = {"status": "NONE", "sweeps": 0, "swaps": 0, "kicks": 0, "rejected": 0}
    best = [unc, list(v), list(s)]
    if unc < TOL and exact_ok(v, s, R):
        out.update(status="COVER", best_unc=0.0, v=v, s=s)
        return out
    stall = 0
    while time.time() < deadline:
        before = unc
        order = list(range(n))
        rng.shuffle(order)
        covered = False
        for i in order:
            if time.time() > deadline:
                break
            g = gaps_without(arcs, i)
            if not g:
                covered = True
                break
            sh, _ov = slr._best_shift(v[i], g, r, rng)
            s[i] = sh
            arcs[i] = slr._norm_arcs(v[i], sh, r)
        out["sweeps"] += 1
        unc = 0.0 if covered else slr._unc_measure(arcs)
        if unc < TOL:
            if exact_ok(v, s, R):
                out.update(status="COVER", best_unc=0.0, v=list(v), s=list(s))
                return out
            out["rejected"] += 1
            stall = 2
        elif unc < best[0] * (1.0 - 1e-9):
            best = [unc, list(v), list(s)]
            stall = 0
        elif unc > before * (1.0 - 1e-6):
            stall += 1
        if stall >= 2:
            stall = 0
            if rng.random() < swap_p and try_swap(v, s, arcs, r, rng, pool_max, unc):
                out["swaps"] += 1
                unc = slr._unc_measure(arcs)
                continue
            v, s = list(best[1]), list(best[2])
            k = max(1, int(round(n * rng.uniform(0.02, 0.12))))
            for i in rng.sample(range(n), k):
                s[i] = rng.random()
            arcs = arcs_of(v, s, r)
            unc = slr._unc_measure(arcs)
            out["kicks"] += 1
    out.update(best_unc=best[0], v=best[1], s=best[2])
    return out


def compact_k(v, s, R):
    """Smallest denominator D in DENOMS whose rounded shifts still cover exactly at R."""
    for D in DENOMS:
        S = [int(round(float(x) * D)) % D for x in s]
        if slr.covers_sweep(v, [F(a, D) for a in S], R)[0]:
            return D, S
    return None, None


def certify_k(v, s, n):
    R = F(1, n + 1)
    D, S = compact_k(v, s, R)
    if D is None:
        return {"ok": False, "why": "no denominator in DENOMS covers"}
    cert = dj.certify_j(v, [F(a, D) for a in S], n)
    cert.update(D=D, S=S, v0=list(v), pad=n - len(v))
    return cert


def run_tier_k(tag, deadline, rng, prev=None):
    """One turn of one tier, resumed from the cached best configuration."""
    prev = dict(prev or {})
    if prev.get("status") == "FOUND":
        return prev
    src, n, _mode = TIERS_K[tag]
    t0 = time.time()
    if prev.get("v"):
        v, s, info = prev["v"], prev["s"], prev
    else:
        v, s, start = init_tier(tag, rng)
        info = {"tag": tag, "n": n, "start": start, "hist": [], "sweeps": 0, "swaps": 0,
                "kicks": 0, "rejected": 0, "seconds": 0.0, "turns": 0, "best_unc": None}
    pool_max = 2 * max(source(src)[0])
    res = search_k(v, s, F(1, n + 1), deadline, rng, pool_max)
    for key in ("sweeps", "swaps", "kicks", "rejected"):
        info[key] = info.get(key, 0) + res[key]
    old = info.get("best_unc")
    if old is None or res["best_unc"] <= old or res["status"] == "COVER":
        info["v"], info["s"], info["best_unc"] = list(res["v"]), list(res["s"]), res["best_unc"]
    info["hist"] = (info.get("hist") or []) + [info["best_unc"]]
    info["turns"] = info.get("turns", 0) + 1
    info["status"] = "UNKNOWN"
    if res["status"] == "COVER":
        cert = certify_k(res["v"], res["s"], n)
        info["cert"] = cert
        info["status"] = "FOUND" if cert.get("ok") else "BUG"
    info["gaps"] = n_gaps(info["v"], info["s"], F(1, n + 1)) if info["status"] != "FOUND" else 0
    info["seconds"] = round(info.get("seconds", 0.0) + time.time() - t0, 1)
    return info


def _worker_k(tag, deadline, cache, seed):
    path = os.path.join(cache, "k_%s.json" % tag)
    try:
        prev = rs._load(path, {})
        info = run_tier_k(tag, deadline, random.Random(seed), prev)
        rs._save(path, info)
        if info.get("status") == "FOUND":
            rs._save(os.path.join(cache, "cert_%s.json" % tag), info["cert"])
    except Exception as e:  # report it; the other tiers keep going
        import traceback
        with open(os.path.join(cache, "err_%s.txt" % tag), "w", encoding="utf-8") as f:
            f.write("%r\n%s" % (e, traceback.format_exc()[-500:]))


def start_txt(d):
    if "del" in d:
        return "del=%s m1=%.3g" % (",".join(str(x) for x in d["del"]), d.get("m1") or 0.0)
    if "add" in d:
        return "add=%s src=%.3g" % (d["add"], d.get("m_src") or 0.0)
    return "rand"


def line_k(tag, st):
    d = st.get("start") or {}
    h = ">".join("%.2g" % x for x in (st.get("hist") or [])[-4:])
    return "%s n=%s st=%s best=%.3g g=%s sw=%s swp=%s kk=%s rej=%s t=%ss tu=%s %s m0=%.3g h=%s" % (
        tag, st.get("n"), st.get("status"), st.get("best_unc") or 0.0, st.get("gaps"),
        st.get("sweeps"), st.get("swaps"), st.get("kicks"), st.get("rejected"),
        int(st.get("seconds") or 0), st.get("turns"), start_txt(d), d.get("m0") or 0.0, h)


def r15_line(jdir):
    """Route 15's cached state, compact: tag=status/iterations/clauses/del1-min@speed."""
    out = []
    for tag in dj.ORDER_J:
        r = rs._load(os.path.join(jdir, "t_%s.json" % tag), {})
        if not r:
            if os.path.exists(os.path.join(jdir, "err_%s.txt" % tag)):
                out.append("%s=ERR" % tag)
            continue
        d = r.get("diag") or {}
        out.append("%s=%s/%s/%s/%.2g@%s" % (tag, (r.get("status") or "?")[:3],
                                            r.get("iterations_total"), r.get("n_clauses"),
                                            d.get("min") or 0.0, d.get("at")))
    return "R15 " + (" ".join(out) if out else "none")


def rule_line(tag, st):
    c = st.get("cert") or {}
    return "RULE %s n=%s ok=%s open=%s sweep=%s endpoints=%s pad=%s D=%s v=%s S=%s" % (
        tag, c.get("n"), c.get("ok"), c.get("n") in dj.OPEN, c.get("sweep"), c.get("endpoints"),
        c.get("pad"), c.get("D"), ",".join(str(x) for x in c.get("v0") or []),
        ",".join(str(x) for x in c.get("S") or []))


def probe_k(tiers=ORDER_K, budget=520, cache=None):
    """Every open tier in its own process for the whole budget; report with the summary last."""
    t_end = time.time() + budget
    cache = cache or os.path.join(tempfile.gettempdir(), "mv2-slr-k1")
    os.makedirs(cache, exist_ok=True)
    lines = []

    def state(tag):
        return rs._load(os.path.join(cache, "k_%s.json" % tag), {})

    ctx = multiprocessing.get_context("spawn")
    procs = []
    seed0 = int(time.time() * 1000) % (1 << 30)
    for idx, tag in enumerate(tiers):
        if state(tag).get("status") in ("FOUND", "BUG"):
            continue
        if os.path.exists(os.path.join(cache, "err_%s.txt" % tag)):
            continue
        p = ctx.Process(target=_worker_k, args=(tag, t_end - 60, cache, seed0 + 7919 * idx))
        p.start()
        procs.append((tag, p))
    for tag, p in procs:
        p.join(max(0.5, t_end - 5 - time.time()))
        if p.is_alive():
            p.terminate()
            lines.append("killed %s" % tag)
    lines.append("procs=%d" % len(procs))
    for tag in tiers:
        ep = os.path.join(cache, "err_%s.txt" % tag)
        if os.path.exists(ep):
            with open(ep, encoding="utf-8") as f:
                lines.append("ERROR %s %s" % (tag, f.read()[-200:].replace("\n", " | ")))
    states = {t: state(t) for t in tiers}
    for tag in tiers:
        if states[tag]:
            lines.append(line_k(tag, states[tag]))
    lines.append(r15_line(os.path.join(tempfile.gettempdir(), "mv2-slr-rules-j1")))
    for tag in tiers:
        if states[tag].get("status") in ("FOUND", "BUG"):
            lines.append(rule_line(tag, states[tag]))
    lines.append("STATUS " + " ".join("%s=%s" % (t, states[t].get("status"))
                                      for t in tiers if states[t]))
    return "\n".join(lines)


def job_main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--minutes", type=float, default=180)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    rep = probe_k(budget=60.0 * a.minutes, cache=os.path.join(a.out_dir, "cache"))
    with open(os.path.join(a.out_dir, "report_k.txt"), "w", encoding="utf-8") as f:
        f.write(rep + "\n")
    print(rep)
    return rep


if __name__ == "__main__":
    job_main()
