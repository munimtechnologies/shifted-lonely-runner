# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Job slr-rules-e-v1 (PREREG_rules_e.md): route 11c with more time.

python job_rules_e.py --out-dir /out --minutes 330 --nproc 2 --workers 2

Pass 1 gives every tier of ORDER_E an equal share of the time; later passes split what is left
among the tiers still open (open cubes get twice their earlier time). Writes tiers.json,
rule.json and certs.json (if a rule with threshold <= 94 is found) and report.txt.
"""
import argparse
import os
import time

import rule_search_e as re_
import rule_search_s as rs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--minutes", type=float, default=330.0)
    ap.add_argument("--nproc", type=int, default=2)
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    t_end = time.time() + a.minutes * 60
    reports = []
    for npass in range(1, 6):
        left = t_end - time.time()
        if left < 180:
            break
        state = rs._load(os.path.join(a.out_dir, "tiers.json"), {})
        todo = [t for t in re_.ORDER_E
                if state.get(t, {}).get("status") not in ("FOUND", "INFEASIBLE", "BUG")]
        if not todo or rs._load(os.path.join(a.out_dir, "rule.json"), None):
            break
        share = (left - 60) / len(todo)
        plan = [(t, share) for t in todo]
        rep = re_.probe_e(plan, budget=left - 30, nproc=a.nproc, workers=a.workers,
                          cache=a.out_dir, d_cache="", c_cache="", first_cap=300.0)
        reports.append("== pass %d (share %.0fs)\n%s" % (npass, share, rep))
        print(reports[-1], flush=True)
    with open(os.path.join(a.out_dir, "report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(reports) + "\n")


if __name__ == "__main__":
    main()
