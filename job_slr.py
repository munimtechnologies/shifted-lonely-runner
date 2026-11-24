# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2). Made with AI agents working in MV2's name.
"""Job slr-gap-v1: search for shifted Lonely Runner counterexamples for 18 <= n <= 94.

Pre-registered in PREREG.md. Writes /out/certificates.jsonl (one line per task, written
as soon as the task ends) and /out/summary_slr.json.
"""
import argparse
import json
import os
import random
import time
from fractions import Fraction
from multiprocessing import Pool

import slr

# Exact gamma_sh(1..n), Table 2 of Blanco-Criado-Santos, arXiv:2603.24784.
KNOWN = {2: (1, 3), 3: (1, 4), 4: (1, 5), 5: (15, 94), 6: (9, 67), 7: (25, 214),
         8: (1, 10), 9: (5, 58), 10: (27, 349), 11: (1, 14), 12: (6, 91),
         13: (1, 16), 14: (71, 1228), 15: (1, 18)}

LEVELS = [Fraction(1, 20), Fraction(1, 4), Fraction(1, 2), Fraction(3, 4), Fraction(1),
          Fraction(5, 4), Fraction(3, 2), Fraction(7, 4), Fraction(2), Fraction(5, 2),
          Fraction(3), Fraction(4), Fraction(5), Fraction(6), Fraction(8)]

# Published n = 5 certificates for v = (1,2,3,4,5), gamma = 15/94 (sanity check S0).
PUBLISHED_N5 = {
    "paper_fig1": [Fraction(0), Fraction(46, 94), Fraction(38, 94), Fraction(47, 94), Fraction(72, 94)],
    "repo_readme": [Fraction(0), Fraction(767, 3760), Fraction(1079, 11280), Fraction(323, 3760), Fraction(429, 3760)],
    "repo_consecutive_out": [Fraction(0), Fraction(1113, 1880), Fraction(2681, 3760), Fraction(617, 940), Fraction(323, 752)],
}


def speed_sets(n):
    full = list(range(1, n + 2))
    return [
        ("consecutive", list(range(1, n + 1))),
        ("consecutive", list(range(1, n + 1))),  # second try, new seed
        ("drop1", [x for x in full if x != 1]),
        ("drop2", [x for x in full if x != 2]),
        ("dropn", [x for x in full if x != n]),
    ]


def run_task(task):
    n, label, v, t_first, t_level, improve_cap, seed, hard_deadline, phase = task
    t0 = time.time()
    out = {"n": n, "label": label, "speeds": v, "seed": seed, "phase": phase}
    if time.time() >= hard_deadline - 5:
        out.update({"status": "skipped-deadline", "levels": [], "seconds": 0.0})
        return out
    rng = random.Random(seed)
    recs, status = slr.solve_levels(v, LEVELS, t_first, t_level, rng,
                                    hard_deadline=hard_deadline, improve_cap=improve_cap)
    out.update({"status": status, "levels": recs, "seconds": round(time.time() - t0, 1)})
    good = [r for r in recs if r["checkA"] and r["checkB"]]
    out["best_e"] = good[-1]["e"] if good else None
    out["best_R"] = good[-1]["R"] if good else None
    return out


def sanity_s0():
    res = {}
    v = [1, 2, 3, 4, 5]
    for name, s in PUBLISHED_N5.items():
        a1, _ = slr.covers_sweep(v, s, Fraction(1, 6))
        b1, _ = slr.covers_endpoints(v, s, Fraction(1, 6))
        a2, _ = slr.covers_sweep(v, s, Fraction(15, 94))
        b2, _ = slr.covers_endpoints(v, s, Fraction(15, 94))
        res[name] = {"covers_at_1/6": [a1, b1], "covers_at_15/94": [a2, b2],
                     "holds": a1 and b1 and not a2 and not b2}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--minutes", type=float, default=200.0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--nmin", type=int, default=18)
    ap.add_argument("--nmax", type=int, default=94)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    start = time.time()
    hard = start + args.minutes * 60.0
    certs_path = os.path.join(args.out_dir, "certificates.jsonl")
    fh = open(certs_path, "a", encoding="utf-8")

    summary = {"job": "slr-gap-v1", "started_unix": round(start), "levels": [str(e) for e in LEVELS]}
    summary["S0_published_n5"] = sanity_s0()
    print("S0", json.dumps(summary["S0_published_n5"]), flush=True)

    results = []

    def run_round(tasks):
        with Pool(args.workers) as pool:
            for out in pool.imap_unordered(run_task, tasks):
                results.append(out)
                fh.write(json.dumps(out) + "\n")
                fh.flush()
                print(out["phase"], out["n"], out["label"], out["status"], out.get("best_e"),
                      out["seconds"], flush=True)

    # Phase 1: validation on (1..n), n = 5..17 (Blanco-Criado-Santos Prop. 5.14 range).
    # Phase 2: main range, (1..n) first.
    tasks = []
    for n in range(5, 18):
        tasks.append((n, "consecutive", list(range(1, n + 1)), 20, 10, 40, 1000 * n + 1, hard, "validation"))
    for n in range(args.nmin, args.nmax + 1):
        tasks.append((n, "consecutive", list(range(1, n + 1)), 90, 15, 45, 1000 * n + 1, hard, "main"))
    run_round(tasks)

    # Phase 3: retry the main-range n with no certificate, through speed_sets(n)[1:].
    def certified(n):
        return any(r["n"] == n and r["phase"] in ("main", "retry") and r.get("best_e") is not None
                   for r in results)

    for k in range(1, len(speed_sets(args.nmin))):
        failing = [n for n in range(args.nmin, args.nmax + 1) if not certified(n)]
        if not failing or time.time() > hard - 60:
            break
        tasks = []
        for n in failing:
            label, v = speed_sets(n)[k]
            tasks.append((n, label, v, 300, 15, 30, 1000 * n + 1 + k, hard, "retry"))
        run_round(tasks)
    fh.close()

    # Summary and pre-registered checks.
    main_cert = sorted({r["n"] for r in results if r["phase"] in ("main", "retry") and r.get("best_e") is not None})
    rng_all = list(range(args.nmin, args.nmax + 1))
    s1_viol = []
    s2_bad = []
    for r in results:
        for rec in r["levels"]:
            if rec["checkA"] != rec["checkB"]:
                s2_bad.append([r["n"], r["label"], rec["e"]])
            if (rec["checkA"] and rec["checkB"] and r["label"] == "consecutive"
                    and r["n"] in KNOWN and Fraction(rec["R"]) <= Fraction(*KNOWN[r["n"]])):
                s1_viol.append([r["n"], rec["R"]])
    best_e_consec = {}
    best_e_any = {}
    for r in results:
        if r.get("best_e") is None:
            continue
        e = Fraction(r["best_e"])
        if r["label"] == "consecutive":
            old = best_e_consec.get(r["n"])
            if old is None or e > old:
                best_e_consec[r["n"]] = e
        old = best_e_any.get(r["n"])
        if old is None or e > old:
            best_e_any[r["n"]] = e
    val_cert = sorted(n for n in range(5, 18) if n in best_e_consec)
    summary.update({
        "S1_violations": s1_viol,
        "S2_checker_disagreements": s2_bad,
        "validation_certified_n": val_cert,
        "V1_n8_to_17_all_certified": all(n in best_e_consec for n in range(8, 18)),
        "main_certified_n": main_cert,
        "main_missing_n": [n for n in rng_all if n not in main_cert],
        "H1_all_main_certified": len(main_cert) == len(rng_all),
        "best_e_consecutive": {str(n): str(e) for n, e in sorted(best_e_consec.items())},
        "best_e_any": {str(n): str(e) for n, e in sorted(best_e_any.items())},
        "H2_count_consecutive_e_ge_1_in_main": sum(1 for n in rng_all if best_e_consec.get(n, Fraction(-1)) >= 1),
        "wall_minutes": round((time.time() - start) / 60.0, 1),
    })
    summary["H2_holds"] = summary["H2_count_consecutive_e_ge_1_in_main"] >= (len(rng_all) + 1) // 2
    with open(os.path.join(args.out_dir, "summary_slr.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps({k: summary[k] for k in ("S1_violations", "S2_checker_disagreements",
                                               "V1_n8_to_17_all_certified", "main_missing_n",
                                               "H1_all_main_certified", "H2_holds", "wall_minutes")}))
    print("done")


if __name__ == "__main__":
    main()
