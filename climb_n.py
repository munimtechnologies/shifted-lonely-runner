# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Route 18 (PREREG_rules_n.md): climb the exact chain margin, with swaps at the critical cycle.

Route 17 (polish_l.py) showed that the near-covers route 16 reached for n = 64 and n = 94 have an
exact chain margin lambda of exactly 0, and that the critical cycle in both is a pair of runners:
speeds {6, 124} at radius 1/65 and {6, 184} at radius 1/95. Both pairs sum to 2(n + 1).

Rigid pairs. Take runners of speeds a and b, and two contacts in a chain: lift A_k of a just
before lift B_m of b, and lift B_m' of b just before lift A_k' of a. With x = s / v the two
overlaps are (k + R)/a - (m - R)/b - x_a + x_b and (m' + R)/b - (k' - R)/a - x_b + x_a, so
their SUM does not depend on the shifts:

    2R (a + b) / (a b) + (b (k - k') + a (m' - m)) / (a b).

The second numerator runs over the multiples of g = gcd(a, b). So the sum can be exactly 0 only
if 2R (a + b) / g is an integer; with R = 1/(n + 1): (n + 1) g divides 2 (a + b). Call such a
pair RIGID at n. A chain whose critical cycle is a non-rigid pair can never have lambda exactly
0, so every lambda = 0 two-runner critical cycle must be rigid (a built-in consistency check,
`rig=` in the report). If both contacts of a rigid pair are forced, re-tuning shifts cannot help:
one of the two runners has to change speed, or the chain has to be rerouted.

The climb. The objective is lambda itself, decided exactly (polish_l.polish: greedy chain,
difference constraints, Karp's minimum cycle mean in integers), after a short fixpoint of
polish and re-chaining. Moves replace one runner of the critical cycle by an unused speed at
its best-response shift (slr._best_shift, as in route 16), preferring speeds that form no rigid
pair with the other cycle runners. A move is kept only if lambda rises. With no rising move the
state is kicked (a few shifts randomised, 15 s of route-16 search) and the climb resumes; the
best lambda ever seen is kept. lambda > 0 means a cover: it is re-checked by both exact checkers
of slr.py and padded to exactly n runners (descent_k.certify_k).

Nothing here proves a negative: lambda <= 0 rules out one chain, and a climb that ends without
a cover proves nothing about the speed sets it visited.
"""
import math
import multiprocessing
import os
import random
import tempfile
import time
from fractions import Fraction as F

import descent_k as dk
import polish_l as pl
import rule_search_s as rs
import slr

TIERS_N = ["kC64", "kP94", "kC62", "kC61", "cC63"]  # route 16's tiers, same meaning
TOL_N = 2e-6        # chain bridging tolerance (gaps up to this may be bridged)
FIX_ITERS = 2       # polish / re-chain fixpoint rounds per evaluation
KICK_SEARCH = 15.0  # seconds of route-16 search in a kick
LOW = F(-1)         # lambda value used when no chain can be formed


def rigid(a, b, n):
    """True iff speeds a, b can have two contacts whose overlaps sum to exactly 0 at radius
    1/(n + 1), i.e. (n + 1) gcd(a, b) divides 2 (a + b)."""
    return (2 * (a + b)) % ((n + 1) * math.gcd(a, b)) == 0


def rigid_pairs(v, n):
    """Number of rigid pairs among the speeds v at n."""
    v = sorted(v)
    return sum(1 for i in range(len(v)) for j in range(i + 1, len(v)) if rigid(v[i], v[j], n))


def pair_sum(a, b, R, k, m, m2, k2):
    """Exact sum of the two overlaps of contacts (A_k, B_m) and (B_m2, A_k2) (shift-free)."""
    R = F(R)
    return (F(k) + R) / a - (F(m) - R) / b + (F(m2) + R) / b - (F(k2) - R) / a


def evaluate(v, s, R, tol=TOL_N, iters=FIX_ITERS):
    """Fixpoint of exact polish and re-chaining. Returns a dict with lam (Fraction; LOW if no
    chain), s (the best shifts seen), cyc (critical speeds), chain, cover, and s_cover when a
    polished configuration passed the exact check."""
    best = {"lam": None, "s": [float(x) % 1.0 for x in s], "cyc": [], "chain": None,
            "cover": False, "why": None}
    cur = list(best["s"])
    for _ in range(iters):
        p = pl.polish(v, cur, R, tol)
        lam = p.get("lam")
        if lam is None:
            if best["lam"] is None:
                best["why"] = p.get("why") or "no cycle"
            break
        if best["lam"] is None or lam > best["lam"]:
            best.update(lam=lam, cyc=p.get("cyc") or [], chain=p.get("chain"),
                        s=list(p.get("s_new") or cur))
            if p.get("cover"):
                best["cover"] = True
                best["s_cover"] = list(p["s_new"])
                break
        else:
            break
        if p.get("s_new") is None:
            break
        cur = list(p["s_new"])
    if best["lam"] is None:
        best["lam"] = LOW
    return best


def _cyc_idx(v, cyc):
    pos = {w: i for i, w in enumerate(v)}
    return [pos[w] for w in cyc if w in pos]


def climb(v, s, R, n, deadline, rng, pool_max, take=3, wsample=8, start=None):
    """Exact lambda climb from (v, s). Returns a state dict (status COVER or NONE)."""
    v = list(v)
    s = [float(x) % 1.0 for x in s]
    r = float(R) * (1.0 - dk.SHRINK)
    cur = start or evaluate(v, s, R)
    out = {"status": "NONE", "evals": 1, "ups": 0, "kicks": 0, "steps": 0, "plateau": 0,
           "lam0": cur["lam"], "cyc0": list(cur["cyc"]), "hist": []}
    best = {"lam": cur["lam"], "v": list(v), "s": list(cur["s"]), "cyc": list(cur["cyc"])}

    def found(vv, ev):
        out.update(status="COVER", v=list(vv), s=list(ev["s_cover"]), lam=ev["lam"],
                   cyc=list(ev["cyc"]))
        return out

    if cur["cover"]:
        return found(v, cur)
    s = list(cur["s"])
    while time.time() < deadline:
        out["steps"] += 1
        idx = _cyc_idx(v, cur["cyc"])
        rng.shuffle(idx)
        idx = idx[:take]
        while len(idx) < min(take, len(v)):
            j = rng.randrange(len(v))
            if j not in idx:
                idx.append(j)
        cyc_set = set(cur["cyc"])
        have = set(v)
        pool = [w for w in range(1, pool_max + 1) if w not in have]
        arcs = dk.arcs_of(v, s, r)
        move = None
        for i in idx:
            if time.time() > deadline:
                break
            g = dk.gaps_without(arcs, i)
            if not g:
                continue
            others = [w for w in cyc_set if w != v[i]]
            good = [w for w in pool if not any(rigid(w, u, n) for u in others)]
            cands = [v[i]] + rng.sample(good or pool, min(wsample, len(good or pool)))
            for w in cands:
                if time.time() > deadline:
                    break
                sh, _ov = slr._best_shift(w, g, r, rng)
                v2 = list(v)
                v2[i] = w
                s2 = list(s)
                s2[i] = sh
                ev = evaluate(v2, s2, R)
                out["evals"] += 1
                if ev["cover"]:
                    return found(v2, ev)
                # best lambda; among equal lambdas prefer a changed speed (plateau moves)
                key = (ev["lam"], int(w != v[i]), rng.random())
                if move is None or key > move[2]:
                    move = (ev, v2, key)
        if move is not None and move[0]["lam"] > cur["lam"]:
            cur, v = move[0], move[1]
            s = list(cur["s"])
            out["ups"] += 1
        elif (move is not None and move[0]["lam"] == cur["lam"] and move[2][1] == 1
              and out["plateau"] < 3 * out["steps"] // 4 + 1):
            cur, v = move[0], move[1]
            s = list(cur["s"])
            out["plateau"] += 1
        else:
            out["kicks"] += 1
            if rng.random() < 0.5:
                v2, s2 = list(best["v"]), list(best["s"])
            else:
                v2, s2 = list(v), list(s)
            k = max(1, int(round(len(v2) * rng.uniform(0.02, 0.08))))
            for j in rng.sample(range(len(v2)), k):
                s2[j] = rng.random()
            res = dk.search_k(v2, s2, R, min(deadline, time.time() + KICK_SEARCH), rng, pool_max)
            if res["status"] == "COVER":
                ev = evaluate(res["v"], res["s"], R)
                if ev["cover"]:
                    return found(res["v"], ev)
                out["status"] = "SEARCHCOVER"
                out.update(v=list(res["v"]), s=list(res["s"]))
                return out
            v = list(res["v"])
            cur = evaluate(v, res["s"], R)
            out["evals"] += 1
            if cur["cover"]:
                return found(v, cur)
            s = list(cur["s"])
        if cur["lam"] > best["lam"]:
            best = {"lam": cur["lam"], "v": list(v), "s": list(cur["s"]), "cyc": list(cur["cyc"])}
            out["hist"].append(pl.lam_txt(cur["lam"]))
    out.update(v=best["v"], s=best["s"], lam=best["lam"], cyc=best["cyc"])
    return out


# ---------------------------------------------------------------- tiers and probe

def seed_for(tag, lcache, kcache, rng):
    """Start of a tier: route 17's cached state, else route 16's, else route 16's start."""
    for name, path in (("l17", os.path.join(lcache, "l_%s.json" % tag)),
                       ("k16", os.path.join(kcache, "k_%s.json" % tag))):
        st = rs._load(path, {})
        if st.get("v") and st.get("s"):
            return list(st["v"]), list(st["s"]), name
    v, s, _start = dk.init_tier(tag, rng)
    return v, s, "init"


def run_tier_n(tag, deadline, rng, prev=None, lcache=None, kcache=None):
    st = dict(prev or {})
    if st.get("status") in ("FOUND", "BUG"):
        return st
    src, n, _mode = dk.TIERS_K[tag]
    R = F(1, n + 1)
    if st.get("v"):
        v, s = list(st["v"]), list(st["s"])
    else:
        v, s, st["seed"] = seed_for(tag, lcache or "", kcache or "", rng)
        st["rp"] = rigid_pairs(v, n)
    st.update(tag=tag, n=n)
    pool_max = 2 * max(dk.source(src)[0])
    t0 = time.time()
    res = climb(v, s, R, n, deadline, rng, pool_max)
    for key in ("evals", "ups", "kicks", "steps", "plateau"):
        st[key] = st.get(key, 0) + res[key]
    if "lam0" not in st:
        st["lam0"] = pl.lam_txt(res["lam0"])
        st["cyc0"] = list(res["cyc0"])[:12]
    if res["status"] == "COVER":
        cert = dk.certify_k(res["v"], res["s"], n)
        st.update(cert=cert, v=list(res["v"]), s=list(res["s"]),
                  status="FOUND" if cert.get("ok") else "BUG")
    elif res["status"] == "SEARCHCOVER":
        cert = dk.certify_k(res["v"], res["s"], n)
        st.update(cert=cert, v=list(res["v"]), s=list(res["s"]),
                  status="FOUND" if cert.get("ok") else "BUG")
    else:
        old = st.get("lam_f")
        if old is None or float(res["lam"]) >= old:
            st.update(v=list(res["v"]), s=list(res["s"]), lam=pl.lam_txt(res["lam"]),
                      lam_f=float(res["lam"]), cyc=list(res["cyc"])[:12],
                      lam_exact=str(res["lam"]))
            cy = res["cyc"]
            st["rig"] = (int(rigid(cy[0], cy[1], n)) if len(cy) == 2 else "-")
        st["status"] = "UNKNOWN"
        st["unc"] = dk.measure(st["v"], st["s"], 1.0 / (n + 1))
    st["hist"] = ((st.get("hist") or []) + res["hist"])[-4:]
    st["seconds"] = round(st.get("seconds", 0.0) + time.time() - t0, 1)
    st["turns"] = st.get("turns", 0) + 1
    return st


def _worker_n(tag, deadline, cache, lcache, kcache, seed):
    path = os.path.join(cache, "n_%s.json" % tag)
    try:
        prev = rs._load(path, {})
        st = run_tier_n(tag, deadline, random.Random(seed), prev, lcache, kcache)
        rs._save(path, st)
        if st.get("status") == "FOUND":
            rs._save(os.path.join(cache, "cert_%s.json" % tag), st["cert"])
    except Exception as e:
        import traceback
        with open(os.path.join(cache, "err_%s.txt" % tag), "w", encoding="utf-8") as f:
            f.write("%r\n%s" % (e, traceback.format_exc()[-400:]))


def line_n(tag, st):
    return ("%s n=%s st=%s sd=%s rp=%s lam0=%s cyc0=%s lam=%s cyc=%s rig=%s up=%s pl=%s kk=%s "
            "ev=%s unc=%.2g t=%s tu=%s h=%s" % (
                tag, st.get("n"), st.get("status"), st.get("seed"), st.get("rp"), st.get("lam0"),
                ",".join(str(x) for x in st.get("cyc0") or []), st.get("lam"),
                ",".join(str(x) for x in st.get("cyc") or []), st.get("rig"), st.get("ups"),
                st.get("plateau"), st.get("kicks"), st.get("evals"), st.get("unc") or 0.0,
                int(st.get("seconds") or 0), st.get("turns"),
                ">".join(st.get("hist") or []) or "-"))


def r17_line(lcache):
    """Route 17's cached state, compact (its probe reports were cut at the front)."""
    out = []
    for tag in pl.TIERS_L:
        st = rs._load(os.path.join(lcache, "l_%s.json" % tag), {})
        if st:
            out.append("%s=%s/%s/%s/%.2g/p%s" % (tag, (st.get("status") or "?")[:3],
                                                st.get("lam_best"), ",".join(
                                                    str(x) for x in (st.get("cyc") or [])[:4]),
                                                st.get("unc") or 0.0, st.get("polishes")))
    cal = rs._load(os.path.join(lcache, "cal.json"), {})
    c = ("CAL17 raw=%s lam=%s cov=%s cert=%s upw=%s upm0=%.2g uplam=%s upcov=%s upcyc=%s" % (
        cal.get("c63raw_covers"), cal.get("c63_lam"), cal.get("c63_cover"), cal.get("c63_cert"),
        cal.get("up_w"), cal.get("up_m0") or 0.0, cal.get("up_lam"), cal.get("up_cover"),
        ",".join(str(x) for x in (cal.get("up_cyc") or [])[:6]))) if cal else "CAL17 none"
    return "R17 " + (" ".join(out) if out else "none"), c


def rule_line_n(tag, st):
    c = st.get("cert") or {}
    return "RULE %s n=%s ok=%s D=%s v=%s S=%s" % (
        tag, c.get("n"), c.get("ok"), c.get("D"), ",".join(str(x) for x in c.get("v0") or []),
        ",".join(str(x) for x in c.get("S") or []))


def probe_n(budget=520, cache=None, lcache=None, kcache=None):
    t_end = time.time() + budget
    tmp = tempfile.gettempdir()
    cache = cache or os.path.join(tmp, "mv2-slr-n1")
    lcache = lcache or os.path.join(tmp, "mv2-slr-l1")
    kcache = kcache or os.path.join(tmp, "mv2-slr-k1")
    os.makedirs(cache, exist_ok=True)
    lines = []
    ctx = multiprocessing.get_context("spawn")
    procs = []
    seed0 = int(time.time() * 1000) % (1 << 30)
    for idx, tag in enumerate(TIERS_N):
        st = rs._load(os.path.join(cache, "n_%s.json" % tag), {})
        if st.get("status") in ("FOUND", "BUG"):
            continue
        if os.path.exists(os.path.join(cache, "err_%s.txt" % tag)):
            continue
        p = ctx.Process(target=_worker_n, args=(tag, t_end - 40, cache, lcache, kcache,
                                                seed0 + 7919 * idx))
        p.start()
        procs.append((tag, p))
    for tag, p in procs:
        p.join(max(0.5, t_end - 5 - time.time()))
        if p.is_alive():
            p.terminate()
            lines.append("killed %s" % tag)
    lines.append("procs=%d" % len(procs))
    for tag in TIERS_N:
        ep = os.path.join(cache, "err_%s.txt" % tag)
        if os.path.exists(ep):
            with open(ep, encoding="utf-8") as f:
                lines.append("ERROR %s %s" % (tag, f.read()[-160:].replace("\n", " | ")))
    states = {t: rs._load(os.path.join(cache, "n_%s.json" % t), {}) for t in TIERS_N}
    for tag in TIERS_N:
        if states[tag]:
            lines.append(line_n(tag, states[tag]))
    r17, cal = r17_line(lcache)
    lines.append(pl.r16_line(kcache))
    lines.append(r17)
    lines.append(cal)
    for tag in TIERS_N:
        if states[tag].get("status") in ("FOUND", "BUG"):
            lines.append(rule_line_n(tag, states[tag]))
    lines.append("STATUS " + " ".join("%s=%s" % (t, states[t].get("status"))
                                      for t in TIERS_N if states[t]))
    return "\n".join(lines)


def job_main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--minutes", type=float, default=120)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    rep = probe_n(budget=60.0 * a.minutes, cache=os.path.join(a.out_dir, "cache"),
                  lcache=os.path.join(a.out_dir, "lcache"), kcache=os.path.join(a.out_dir, "kcache"))
    with open(os.path.join(a.out_dir, "report_n.txt"), "w", encoding="utf-8") as f:
        f.write(rep + "\n")
    print(rep)
    return rep


if __name__ == "__main__":
    job_main()
