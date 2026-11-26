# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Job slr-rules-d-v1 (PREREG_rules_d.md): route 11b with more time.

python job_rules_d.py --out-dir /out --minutes 330 --workers 4 --cap 2400

Pass 1 gives every tier of ORDER_D up to --cap seconds; later passes give the tiers still
UNKNOWN the time that is left (they resume from their collected classes). Writes tiers.json,
rule.json and certs.json (if a rule with threshold <= 94 is found) and report.txt.
"""
import argparse
import os
import time

import rule_search_d as rd
import rule_search_s as rs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--minutes", type=float, default=330.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--cap", type=float, default=2400.0)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    t_end = time.time() + a.minutes * 60
    reports = []
    cap = a.cap
    for npass in range(1, 6):
        left = t_end - time.time()
        if left < 120:
            break
        state = rs._load(os.path.join(a.out_dir, "tiers.json"), {})
        todo = [t for t in rd.ORDER_D
                if state.get(t, {}).get("status") not in ("FOUND", "INFEASIBLE", "BUG")]
        if not todo or rs._load(os.path.join(a.out_dir, "rule.json"), None):
            break
        plan = [(t, cap) for t in todo]
        rep = rd.probe_d(plan, budget=left, workers=a.workers, cache=a.out_dir, c_cache="")
        reports.append("== pass %d (cap %.0fs)\n%s" % (npass, cap, rep))
        print(reports[-1], flush=True)
        cap = max(cap, left / max(1, len(todo)))
    with open(os.path.join(a.out_dir, "report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(reports) + "\n")


if __name__ == "__main__":
    main()
