# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Long-cap driver for routes 19d and 19e (PREREG_rules_r.md, PREREG_rules_t.md, Addendum 1).

The publish gate gives a probe about 450 s, and in the 7-smooth menu one CP-SAT call alone takes
150-430 s, so gate probes T1 and T2 (2026-11-28) each ended UNKNOWN after 2-3 iterations. This
driver runs the SAME exact CEGAR (top_p.cegar_p: unchanged menu q, clauses, slack radius and
fixed-N check) with long per-turn caps on a machine that can run for many hours, and writes its
state after every turn so it can be stopped and resumed at any time.

Nothing about what FOUND or INFEASIBLE means changes with the cap: FOUND is an explicit rule that
must pass the fixed-N check, top_q.full_cert (three global exact checkers) and the stand-alone
verify_cover at R = 1/(n+1); INFEASIBLE is CP-SAT proving the collected necessary clauses
unsatisfiable. Only UNKNOWN (time ran out) depends on the cap.

Usage (state and logs go to --out; --t1 and --r1 are copies of the gate caches mv2-slr-t1 and
mv2-slr-r1, used only to resume each tier from the classes it has already collected):

    python long_run.py --out OUT [--t1 DIR] [--r1 DIR] [--hours 20] [--cap 3600] [--workers 3]
                       [--tiers t63,t70,t84,t80,r80g2,r60,r75,r90,r72,r81] [--max-rss-gb 5]

Files in OUT: state.json (all tiers), cert_<tag>.json (every certified FOUND), progress.log (one
line per turn), report.txt (the latest summary, rewritten after every turn), done.txt (written
when the run ends, with the reason).
"""
import argparse
import json
import os
import sys
import time

import probe_t_lib as pt
import rule_search_s as rs
import rules_m
import top_p as tp
import top_q as tq
import top_r as tr

KIND = tq.KIND
DENS_Q = tq.DENS_Q

# Route 19e first (its pre-registered order, sanity last), then route 19d's undecided tiers whose
# top speed 2N is 5-smooth, with the gain-2 tier at N = 80 (n = 78, next to the n = 79 cover) first.
DEFAULT_TIERS = ["t63", "t70", "t84", "t80", "r80g2", "r60", "r75", "r90", "r72", "r81"]
SANITY = {"t80"}
DECIDED = ("FOUND", "INFEASIBLE", "BUG")


def tier_def(tag):
    """(N, g, P) for a route-19e tag (t...) or a route-19d tag (r...)."""
    if tag in pt.TIERS:
        return pt.TIERS[tag]
    if tag in tr.TIERS:
        return tr.TIERS[tag]
    if tag.startswith("r") and "g" in tag:
        # route-19d style gain tier not in its table, e.g. r80g2: N = 80, gain 2, P5
        n_s, g_s = tag[1:].split("g")
        return (int(n_s), int(g_s), tr.to.P5)
    raise KeyError(tag)


def initial_state(tags, t1, r1):
    """Start each tier from the gate cache that owns it (t1 for t-tags, r1 for r-tags), keeping
    its status, turns and collected classes; a t-tier with no t1 entry is seeded with the classes
    route 19d collected at the same N and gain. Returns {tag: info}."""
    out = {}
    for tag in tags:
        own = (t1 if tag.startswith("t") else r1).get(tag)
        if own:
            info = dict(own)
            info["resumed_from"] = "t1" if tag.startswith("t") else "r1"
        else:
            N, g, _P = tier_def(tag)
            src = "r%d" % N if g == 1 else "r%dg%d" % (N, g)
            seeds = [[int(q), int(k)] for q, k in ((r1.get(src) or {}).get("classes") or [])]
            info = {"status": "-", "turns": 0, "classes": seeds, "resumed_from":
                    ("r1:" + src) if seeds else "scratch"}
        info.setdefault("turns", 0)
        info.setdefault("classes", [])
        info["long_turns"] = info.get("long_turns", 0)
        out[tag] = info
    return out


def rss_gb():
    """Resident memory of this process in GB (Linux /proc), or 0 if unknown."""
    try:
        with open("/proc/self/status", encoding="ascii") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1048576.0
    except Exception:
        pass
    return 0.0


def certify(tag, rule_json):
    """Four exact checks of a FOUND rule. Returns (ok, cert dict, speeds, shifts)."""
    N, g, _P = tier_def(tag)
    n = N - g
    full = tq.full_cert(rules_m.rule_from_json(rule_json), N, n)
    ok4, note4 = pt.stand_alone(full, n)
    cert = {k: v for k, v in full.items() if k not in ("speeds", "shifts")}
    cert["stand_alone"] = ok4
    cert["stand_alone_note"] = note4
    return bool(full.get("ok") and ok4), cert, full.get("speeds"), full.get("shifts")


def pick(state, tags):
    pend = [t for t in tags if state[t].get("status") not in DECIDED]
    if not pend:
        return None
    pend.sort(key=lambda t: (state[t].get("long_turns", 0), tags.index(t)))
    return pend[0]


def report(state, tags, why=""):
    lines = ["LONG " + " ".join(tp._tok(t, state.get(t)) for t in tags)]
    new = []
    for t in tags:
        st = state[t]
        if st.get("status") == "BUG":
            lines.append("BUG %s %s" % (t, " | ".join(st.get("why", []))[:240]))
        if st.get("status") == "FOUND":
            N, g, _P = tier_def(t)
            word = "SANE" if t in SANITY else "RULE"
            if t not in SANITY:
                new.append(N - g)
            lines.append(("%s %s N=%d n=%d %s" % (word, t, N, N - g,
                                                  tp.short_rule(st["rule"])))[:900])
            lines.append("CERT %s %s" % (t, json.dumps(st.get("cert"))[:300]))
    cnt = {}
    for t in tags:
        s = state[t].get("status", "-")
        cnt[s] = cnt.get(s, 0) + 1
    lines.append("STATUS new_n=%s %s %s" % (new or "-", " ".join(
        "%s=%d" % (k, v) for k, v in sorted(cnt.items())), why))
    return "\n".join(lines)


def run(out, tags, t1=None, r1=None, hours=20.0, cap=3600, workers=3, max_rss_gb=5.0,
        max_turns=None, log=print):
    os.makedirs(out, exist_ok=True)
    state_path = os.path.join(out, "state.json")
    state = rs._load(state_path, None)
    if not state:
        state = initial_state(tags, t1 or {}, r1 or {})
        rs._save(state_path, state)
    else:
        for t in tags:  # tiers added on a later start
            if t not in state:
                state.update(initial_state([t], t1 or {}, r1 or {}))
    t_end = time.time() + hours * 3600.0
    ok, note = rs.ensure_ortools() if (max_turns is None or max_turns > 0) else (True, "skip")
    _append(out, "START %s ortools=%s %s tiers=%s cap=%d workers=%d hours=%.1f" % (
        _now(), ok, note[:40], ",".join(tags), cap, workers, hours))
    why = "all decided"
    turns = 0
    while True:
        if not ok:
            why = "no ortools"
            break
        if max_turns is not None and turns >= max_turns:
            why = "max_turns"
            break
        tag = pick(state, tags)
        if tag is None:
            break
        left = t_end - time.time()
        if left < 120:
            why = "time"
            break
        if max_rss_gb and rss_gb() > max_rss_gb:
            why = "memory %.1f GB" % rss_gb()
            break
        N, g, P = tier_def(tag)
        prev = state[tag]
        try:
            info = tp.cegar_p(N, g, P, KIND, DENS_Q, time.time() + min(cap, left - 60),
                              workers=workers, seed_classes=prev.get("classes") or [])
        except Exception as e:
            info = {"status": "BUG", "why": [repr(e)[:160]], "iterations": 0, "seconds": 0,
                    "solve_seconds": 0, "classes": prev.get("classes") or []}
        info["resumed_from"] = prev.get("resumed_from")
        info["turns"] = prev.get("turns", 0) + 1
        info["long_turns"] = prev.get("long_turns", 0) + 1
        info["it_total"] = prev.get("it_total", 0) + info.get("iterations", 0)
        info["sec_total"] = prev.get("sec_total", 0) + info.get("seconds", 0)
        info["solve_total"] = prev.get("solve_total", 0) + info.get("solve_seconds", 0)
        if info["status"] == "FOUND":
            try:
                good, cert, speeds, shifts = certify(tag, info["rule"])
            except Exception as e:
                good, cert, speeds, shifts = False, {"why": repr(e)[:120]}, None, None
            info["cert"] = cert
            if not good:
                info["status"] = "BUG"
                info["why"] = ["fixed_check passed but a global check failed",
                               json.dumps(cert)[:160]]
            else:
                with open(os.path.join(out, "cert_%s.json" % tag), "w", encoding="utf-8") as f:
                    json.dump({"tag": tag, "N": N, "n": N - g, "rule": info["rule"],
                               "speeds": speeds, "shifts": [str(x) for x in shifts],
                               "cert": cert}, f)
        state[tag] = info
        rs._save(state_path, state)
        turns += 1
        line = "TURN %s %s %s long_turn=%d it=%d cls=%d solve=%s sec=%s rss=%.2f" % (
            _now(), tag, info["status"][:4], info["long_turns"], info.get("iterations", 0),
            len(info.get("classes") or []), info.get("solve_seconds", "-"),
            info.get("seconds", "-"), rss_gb())
        _append(out, line)
        log(line)
        _write(out, "report.txt", report(state, tags))
    rep = report(state, tags, why)
    _write(out, "report.txt", rep)
    _write(out, "done.txt", "%s %s\n" % (_now(), why))
    _append(out, "END %s %s" % (_now(), why))
    return state, why


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _append(out, line):
    with open(os.path.join(out, "progress.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _write(out, name, text):
    tmp = os.path.join(out, name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    os.replace(tmp, os.path.join(out, name))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--t1", default=None, help="copy of the gate cache mv2-slr-t1")
    ap.add_argument("--r1", default=None, help="copy of the gate cache mv2-slr-r1")
    ap.add_argument("--hours", type=float, default=20.0)
    ap.add_argument("--cap", type=int, default=3600)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--max-rss-gb", type=float, default=5.0)
    ap.add_argument("--tiers", default=",".join(DEFAULT_TIERS))
    a = ap.parse_args(argv)
    tags = [t.strip() for t in a.tiers.split(",") if t.strip()]
    for t in tags:
        tier_def(t)  # fail early on an unknown tag
    t1 = rs._load(os.path.join(a.t1, "state.json"), {}) if a.t1 else {}
    r1 = rs._load(os.path.join(a.r1, "state.json"), {}) if a.r1 else {}
    _state, why = run(a.out, tags, t1, r1, a.hours, a.cap, a.workers, a.max_rss_gb)
    print(open(os.path.join(a.out, "report.txt"), encoding="utf-8").read())
    return 0 if why in ("all decided", "time", "max_turns") else 1


if __name__ == "__main__":
    sys.exit(main())
