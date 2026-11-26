# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Job slr-rules-s-v1 (PREREG_rules_s.md): route 10 with more time per tier.

python job_rules_s.py --out-dir /out --minutes 300 --workers 2 --tl-scale 4

Writes calls.jsonl (one line per tier), rule.json (the first verified rule, if any),
certs.json and certificates.jsonl (full configurations and both global checks), report.txt.
"""
import argparse
import os

import rule_search_s as rs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--minutes", type=float, default=300.0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--tl-scale", type=float, default=4.0)
    ap.add_argument("--tags", default=",".join(rs.ORDER + ["chk192"]))
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    rep = rs.probe([t for t in a.tags.split(",") if t], budget=a.minutes * 60,
                   workers=a.workers, cache=a.out_dir, tl_scale=a.tl_scale)
    with open(os.path.join(a.out_dir, "report.txt"), "w", encoding="utf-8") as f:
        f.write(rep + "\n")
    print(rep)


if __name__ == "__main__":
    main()
