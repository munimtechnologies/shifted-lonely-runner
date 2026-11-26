# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Job slr-rules-c-v1 (PREREG_rules_c.md): route 11 with more time.

python job_rules_c.py --out-dir /out --minutes 300 --workers 4

Writes tiers.json (one record per tier, with the classes collected), rule.json (the first
verified rule with threshold <= 94, if any), certs.json and certificates.jsonl, report.txt.
"""
import argparse
import os

import rule_search_c as rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--minutes", type=float, default=300.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--tags", default=",".join(rc.ORDER))
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    rep = rc.probe([t for t in a.tags.split(",") if t], budget=a.minutes * 60,
                   workers=a.workers, cache=a.out_dir, verbose=True)
    with open(os.path.join(a.out_dir, "report.txt"), "w", encoding="utf-8") as f:
        f.write(rep + "\n")
    print(rep)


if __name__ == "__main__":
    main()
