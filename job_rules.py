# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2). Made with AI agents working in MV2's name.
"""Job slr-rules-v1: search for local shifted-Lonely-Runner rules with largest speed L far
below Poliakova's 192, and certify every n they reach in 18..94.

Pre-registered in PREREG_rules.md. Outputs (in --out-dir):
  rules_found.jsonl         one line per solver call (written as it ends)
  certificates_rules.jsonl  one line per n: full speeds and shifts, both global checks
  summary_rules.json        S0/S0b sanity, first L with a verified rule, n range certified
"""
import argparse
import json
import os
import time
from fractions import Fraction as F

import rules
import rule_search
import slr

DEFAULT_LS = "16,20,24,28,32,36,38,40,44,48,56,64,80,96,128"


def configs(L):
    return [
        ("A", rule_search.halves(), {1, 2, 3, 4, 6}, 2 * L + 1, 300),
        ("B", rule_search.quarters(), {1, 2, 3, 4, 6, 8, 12}, 2 * L + 1, 600),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--minutes", type=float, default=320.0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--Ls", default=DEFAULT_LS)
    ap.add_argument("--lit-budget", type=int, default=3_000_000)
    ap.add_argument("--nmax", type=int, default=94)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    start = time.time()
    hard = start + 60.0 * args.minutes
    summ = {"job": "slr-rules-v1", "started_unix": round(start)}

    # S0: Poliakova's rules pass the exact local criterion with no untouched help.
    s0 = {}
    for name, r in (("9to8", rules.POLIAKOVA_9_8), ("9to8_variant", rules.POLIAKOVA_9_8_VARIANT)):
        ok, fails = rules.local_check(r)
        s0[name] = {"ok": ok, "fails": [list(map(str, f)) for f in fails[:5]]}
    summ["S0_poliakova_local"] = s0
    print("S0", json.dumps(s0), flush=True)

    # S0b: encoding completeness: the 9->8 rule satisfies every clause the encoder makes for
    # its touched speeds, in both menus used below (dens and betas of config A, B).
    X = sorted(set(rules.POLIAKOVA_9_8["removed"]) | set(rules.POLIAKOVA_9_8["rephased"]))
    s0b = {}
    for tag, betas, dens in (("A", rule_search.halves(), {1, 2, 3, 4, 6}),
                             ("B", rule_search.quarters(), {1, 2, 3, 4, 6, 8, 12})):
        t0 = time.time()
        cl, lits = rule_search.all_clauses(192, 9, betas, dens, qs=X)
        bad = rule_search.clauses_satisfied(rules.POLIAKOVA_9_8, cl)
        s0b[tag] = {"bad": [list(b) for b in bad], "literals": lits,
                    "seconds": round(time.time() - t0, 1)}
    summ["S0b_encoding_completeness"] = s0b
    print("S0b", json.dumps(s0b), flush=True)

    found_fh = open(os.path.join(args.out_dir, "rules_found.jsonl"), "a", encoding="utf-8")
    best = None
    calls = []
    for L in [int(x) for x in args.Ls.split(",")]:
        for tag, betas, dens, A, tl in configs(L):
            left = hard - time.time()
            if left < 120:
                break
            rule, info = rule_search.solve(L, A, betas, dens, min(tl, left - 60),
                                           workers=args.workers, lit_budget=args.lit_budget)
            info["config"] = tag
            if rule is not None:
                ok, fails = rules.local_check(rule, untouched_upto=L)
                info["local_ok"] = ok
                info["local_fails"] = [list(map(str, f)) for f in fails[:5]]
                info["rule"] = rules.rule_to_json(rule)
                info["largest"] = rules.largest(rule)
                if ok and best is None:
                    best = (L, rule)
            calls.append(info)
            found_fh.write(json.dumps(info) + "\n")
            found_fh.flush()
            print("solve", json.dumps({k: info.get(k) for k in
                                       ("L", "config", "status", "gain", "local_ok", "literals")}),
                  flush=True)
            if best is not None:
                break
        if best is not None:
            break
    found_fh.close()
    summ["solver_calls"] = [{k: c.get(k) for k in ("L", "config", "status", "gain", "local_ok",
                                                   "literals", "solve_seconds")} for c in calls]

    certs = []
    if best is not None:
        L, rule = best
        g = rules.gain(rule)
        Lr = rules.largest(rule)
        need = max(L, Lr)  # untouched helpers go up to L
        summ["best"] = {"L_menu": L, "largest_touched": Lr, "gain": g,
                        "rule": rules.rule_to_json(rule)}
        nmin = -(-need // 2) - g
        with open(os.path.join(args.out_dir, "certificates_rules.jsonl"), "a", encoding="utf-8") as fh:
            for n in range(max(5, nmin), args.nmax + 1):
                if time.time() > hard + 1800:
                    break
                N = n + g
                if 2 * N < need:
                    continue
                v, s, delta, nn = rules.build_config(rule, N)
                R = F(2, 2 * N + 1)
                t0 = time.time()
                a, _ = slr.covers_endpoints(v, s, R)
                b, _ = slr.covers_sweep(v, s, R)
                rec = {"n": nn, "N": N, "delta": str(delta), "R": str(R),
                       "R_below_1_over_n_plus_1": R < F(1, nn + 1),
                       "distinct": len(set(v)) == nn, "checkB_endpoints": a, "checkA_sweep": b,
                       "speeds": v, "shifts": [str(x) for x in s],
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
    with open(os.path.join(args.out_dir, "summary_rules.json"), "w", encoding="utf-8") as f:
        json.dump(summ, f, indent=1)
    print(json.dumps({k: summ.get(k) for k in ("best", "missing_in_18_94",
                                               "S2_global_disagreements", "wall_minutes")}))
    print("done")


if __name__ == "__main__":
    main()
