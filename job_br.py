# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Job slr-br-v1: best-response search (slr_br.py) for speeds 1..n, n = 18..94.

For each n, seeds 1, 2, 3, ... are tried until a certificate passes the exact check or the
per-n time budget runs out. Writes out/br_certs.jsonl (one certificate per certified n, exact
fraction shifts) and out/br_summary.json (best radius ratio per n, sweeps, seconds).
Seed 1 with max_sweeps=60000 is the same search as test_slr_br_gap.py, so its n = 18, 19, 20
certificates (if the gate passed) are regenerated here and saved.
"""
import argparse
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor

import slr_br


def work(args):
    n, budget = args
    t0 = time.time()
    tries = []
    seed = 1
    while True:
        left = budget - (time.time() - t0)
        if left < 5 and seed > 1:
            break
        secs = max(5.0, min(left, 150.0 if seed == 1 else left))
        cert, st = slr_br.certify_consecutive(n, seed=seed, max_sweeps=60000, seconds=secs)
        st["seed"] = seed
        tries.append(st)
        if cert is not None:
            cert["seed"] = seed
            return n, cert, tries
        seed += 1
        if time.time() - t0 > budget:
            break
    return n, None, tries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--minutes", type=float, default=170)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--lo", type=int, default=18)
    ap.add_argument("--hi", type=int, default=94)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    ns = list(range(a.lo, a.hi + 1))
    budget = a.minutes * 60.0 * a.workers / len(ns)
    t0 = time.time()
    summary = {"budget_seconds_per_n": round(budget, 1), "results": {}}
    with open(os.path.join(a.out_dir, "br_certs.jsonl"), "w") as fc, \
            ProcessPoolExecutor(max_workers=a.workers) as ex:
        for n, cert, tries in ex.map(work, [(n, budget) for n in ns]):
            ratios = [t.get("best_ratio") for t in tries if t.get("best_ratio") is not None]
            summary["results"][str(n)] = {
                "certified": cert is not None,
                "seed": cert["seed"] if cert else None,
                "best_ratio": min(ratios) if ratios else None,
                "tries": tries,
            }
            if cert is not None:
                fc.write(json.dumps(cert) + "\n")
                fc.flush()
            print(n, "certified" if cert else "not found",
                  min(ratios) if ratios else None, flush=True)
    summary["certified"] = [n for n in ns if summary["results"][str(n)]["certified"]]
    summary["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(a.out_dir, "br_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps({"certified": summary["certified"], "seconds": summary["seconds"]}))


if __name__ == "__main__":
    main()
