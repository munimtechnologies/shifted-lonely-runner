# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2). Made with AI agents working in MV2's name.
"""Job slr-rules-m-v1: search for local shifted-Lonely-Runner rules on a base of multiples of
m (m = 6, 4, 12), whose threshold rho - g (rho = L/m) is far below Poliakova's 95, and certify
every n they reach in 18..94.

Pre-registered in PREREG_rules_m.md. Outputs (in --out-dir):
  rules_found_m.jsonl         one line per solver call (written as it ends)
  certificates_rules_m.jsonl  one line per n: full speeds and shifts, both global checks
  summary_rules_m.json        sanity checks, first verified rule, n range certified
"""
import argparse
import json
import os
import time
from fractions import Fraction as F

import rules_m
import rule_search_m
import slr

# (rho, m): rho = 19 first, because a gain-1 rule with rho <= 19 covers every n >= 18.
DEFAULT_PLAN = "19:6,19:4,19:12,24:6,24:4,32:6,32:4"


def menus(L):
    return [
        ("A", rule_search_m.halves(), {1, 2, 3, 4, 6}, L + 1, 600),
        ("B", rule_search_m.quarters(), {1, 2, 3, 4, 6, 8, 12}, L + 1, 900),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--minutes", type=float, default=330.0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--plan", default=DEFAULT_PLAN)
    ap.add_argument("--lit-budget", type=int, default=3_000_000)
    ap.add_argument("--nmax", type=int, default=94)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    start = time.time()
    hard = start + 60.0 * args.minutes
    summ = {"job": "slr-rules-m-v1", "started_unix": round(start), "plan": args.plan}

    # S0: Poliakova's rule and its rescalings to m = 4, 6 pass the criterion; the hand-made
    # modulus-4 example passes and its broken version fails.
    s0 = {}
    for name, r in (("poliakova_m2", rules_m.POLIAKOVA_9_8),
                    ("poliakova_m4", rules_m.scale(rules_m.POLIAKOVA_9_8, 2)),
                    ("poliakova_m6", rules_m.scale(rules_m.POLIAKOVA_9_8, 3)),
                    ("toy_m4", rules_m.TOY_M4)):
        ok, fails = rules_m.local_check(r)
        s0[name] = {"ok": ok, "fails": [list(map(str, f)) for f in fails[:5]]}
    broken = {"m": 4, "removed": [8], "rephased": {}, "added": {2: (F(3, 4), 0)}}
    s0["toy_m4_broken_fails"] = not rules_m.local_check(broken)[0]
    summ["S0"] = s0
    print("S0", json.dumps(s0), flush=True)

    # S0b: encoding completeness: the modulus-6 Poliakova rule satisfies every clause the
    # encoder makes for its touched speeds 24, 36, 48, in both menus.
    r6 = rules_m.scale(rules_m.POLIAKOVA_9_8, 3)
    s0b = {}
    for tag, betas, dens in (("A", rule_search_m.halves(), {1, 2, 3, 4, 6}),
                             ("B", rule_search_m.quarters(), {1, 2, 3, 4, 6, 8, 12})):
        t0 = time.time()
        cl, lits = rule_search_m.all_clauses(576, 27, 6, betas, dens, qs=[24, 36, 48])
        bad = rule_search_m.clauses_satisfied(r6, cl)
        s0b[tag] = {"bad": [list(b) for b in bad], "literals": lits,
                    "seconds": round(time.time() - t0, 1)}
    summ["S0b"] = s0b
    print("S0b", json.dumps(s0b), flush=True)

    found_fh = open(os.path.join(args.out_dir, "rules_found_m.jsonl"), "a", encoding="utf-8")
    best = None
    calls = []
    for item in args.plan.split(","):
        rho, m = (int(x) for x in item.split(":"))
        L = rho * m
        for tag, betas, dens, A, tl in menus(L):
            left = hard - time.time()
            if left < 120:
                break
            rule, info = rule_search_m.solve(L, A, m, betas, dens, min(tl, left - 60),
                                             workers=args.workers, lit_budget=args.lit_budget)
            info["menu"] = tag
            if rule is not None:
                ok, fails = rules_m.local_check(rule, untouched_upto=L)
                info["local_ok"] = ok
                info["local_fails"] = [list(map(str, f)) for f in fails[:5]]
                info["rule"] = rules_m.rule_to_json(rule)
                info["largest"] = rules_m.largest(rule)
                info["threshold"] = rules_m.threshold(rule, untouched_upto=L)
                if ok and best is None:
                    best = (L, rule)
            calls.append(info)
            found_fh.write(json.dumps(info) + "\n")
            found_fh.flush()
            print("solve", json.dumps({k: info.get(k) for k in
                                       ("m", "L", "menu", "status", "gain", "local_ok",
                                        "literals", "threshold")}), flush=True)
            if best is not None:
                break
        if best is not None:
            break
    found_fh.close()
    summ["solver_calls"] = [{k: c.get(k) for k in ("m", "L", "menu", "status", "gain",
                                                   "local_ok", "literals", "solve_seconds")}
                            for c in calls]

    certs = []
    if best is not None:
        L, rule = best
        g = rules_m.gain(rule)
        m = rules_m.modulus(rule)
        nmin = rules_m.threshold(rule, untouched_upto=L)
        summ["best"] = {"L_menu": L, "m": m, "largest_touched": rules_m.largest(rule),
                        "gain": g, "threshold_n": nmin, "rule": rules_m.rule_to_json(rule)}
        with open(os.path.join(args.out_dir, "certificates_rules_m.jsonl"), "a",
                  encoding="utf-8") as fh:
            for n in range(max(5, nmin), args.nmax + 1):
                if time.time() > hard + 1800:
                    break
                N = n + g
                if m * N < L:
                    continue
                v, s, delta, nn = rules_m.build_config(rule, N)
                R = F(2, 2 * N + 1)
                t0 = time.time()
                a, _ = slr.covers_endpoints(v, s, R)
                b, _ = slr.covers_sweep(v, s, R)
                rec = {"n": nn, "N": N, "m": m, "delta": str(delta), "R": str(R),
                       "R_below_1_over_n_plus_1": R < F(1, nn + 1),
                       "distinct": len(set(v)) == nn, "checkB_endpoints": a,
                       "checkA_sweep": b, "speeds": v, "shifts": [str(x) for x in s],
                       "seconds": round(time.time() - t0, 2)}
                certs.append(rec)
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                print("cert", n, a, b, rec["seconds"], flush=True)
    good = sorted(c["n"] for c in certs if c["checkB_endpoints"] and c["checkA_sweep"]
                  and c["R_below_1_over_n_plus_1"] and c["distinct"])
    summ.update({
        "certified_n": good,
        "certified_in_18_94": [n for n in good if 18 <= n <= 94],
        "missing_in_18_94": [n for n in range(18, 95) if n not in good],
        "S2_global_disagreements": [c["n"] for c in certs
                                    if c["checkB_endpoints"] != c["checkA_sweep"]],
        "wall_minutes": round((time.time() - start) / 60.0, 1),
    })
    with open(os.path.join(args.out_dir, "summary_rules_m.json"), "w", encoding="utf-8") as f:
        json.dump(summ, f, indent=1)
    print(json.dumps({k: summ.get(k) for k in ("best", "missing_in_18_94",
                                               "S2_global_disagreements", "wall_minutes")}))
    print("done")


if __name__ == "__main__":
    main()
