# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Fetch the modules that rule_search_d.py builds on from this repository's main branch
(used by the compete job, whose work folder holds only the route-11b files)."""
import urllib.request

BASE = "https://raw.githubusercontent.com/munimtechnologies/shifted-lonely-runner/main/"

for name in ("rules_m.py", "rule_search_m.py", "rule_search_s.py", "rule_search_c.py",
             "slr.py"):
    with urllib.request.urlopen(BASE + name, timeout=60) as r:
        data = r.read()
    with open(name, "wb") as f:
        f.write(data)
    print("fetched", name, len(data))
