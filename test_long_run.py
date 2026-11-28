# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Tests for long_run.py (PREREG_rules_t.md, Addendum 1). No solver call is made here: the tests
check the tier table, resuming from the gate caches, the state/report files, and that the
certifier accepts the committed n = 79 rule and rejects it with one added runner dropped."""
import json
import os
import shutil
import tempfile
import unittest
from fractions import Fraction as F

import long_run as lr
import rules_m
import top_o as to

H = F(1, 2)
Q4 = F(1, 4)

# cover_n079.json's rule (test_cover_n079.py), N = 80, gain 1.
RULE_R80 = {
    "m": 2,
    "removed": [4, 16, 20, 40, 96, 120],
    "rephased": {8: (F(0), F(-1)), 12: (H, H), 24: (H, H), 32: (F(0), F(-3, 2)), 48: (H, H),
                 60: (H, H), 80: (F(0), F(-1)), 160: (F(0), F(1))},
    "added": {3: (Q4, F(0)), 5: (Q4, H), 9: (Q4, F(0)), 15: (Q4, F(0)), 45: (Q4, F(0))},
}


class TestTiers(unittest.TestCase):
    def test_defs(self):
        self.assertEqual(lr.tier_def("t63"), (63, 1, (2, 3, 5, 7)))
        self.assertEqual(lr.tier_def("t84"), (84, 1, (2, 3, 5, 7)))
        self.assertEqual(lr.tier_def("t80"), (80, 1, (2, 3, 5, 7)))
        self.assertEqual(lr.tier_def("r60"), (60, 1, to.P5))
        # r80g2 is the tier probe R7 added (probe_r7_lib.py): N = 80, gain 2, 5-smooth
        self.assertEqual(lr.tier_def("r80g2"), (80, 2, to.P5))
        for t in lr.DEFAULT_TIERS:
            N, g, _P = lr.tier_def(t)
            self.assertTrue(58 <= N - g <= 94 or t in lr.SANITY, t)
        with self.assertRaises(KeyError):
            lr.tier_def("x1")

    def test_initial_state(self):
        t1 = {"t63": {"status": "UNKNOWN", "turns": 1, "classes": [[126, 5]]}}
        r1 = {"r84": {"status": "UNKNOWN", "turns": 2, "classes": [[168, 1], [84, 2]]},
              "r80g2": {"status": "UNKNOWN", "turns": 3, "classes": [[160, 7]]}}
        st = lr.initial_state(["t63", "t84", "t70", "r80g2"], t1, r1)
        self.assertEqual(st["t63"]["classes"], [[126, 5]])
        self.assertEqual(st["t63"]["turns"], 1)
        self.assertEqual(st["t63"]["resumed_from"], "t1")
        # t84 has no t1 entry: seeded from route 19d's r84, turns start at 0
        self.assertEqual(st["t84"]["classes"], [[168, 1], [84, 2]])
        self.assertEqual(st["t84"]["turns"], 0)
        self.assertEqual(st["t84"]["resumed_from"], "r1:r84")
        self.assertEqual(st["t70"]["classes"], [])
        self.assertEqual(st["t70"]["resumed_from"], "scratch")
        self.assertEqual(st["r80g2"]["turns"], 3)
        for t in st:
            self.assertEqual(st[t]["long_turns"], 0)
        # fewest long turns first, then list order
        self.assertEqual(lr.pick(st, ["t63", "t84", "t70", "r80g2"]), "t63")
        st["t63"]["long_turns"] = 1
        self.assertEqual(lr.pick(st, ["t63", "t84", "t70", "r80g2"]), "t84")
        for t in st:
            st[t]["status"] = "INFEASIBLE"
        self.assertIsNone(lr.pick(st, list(st)))


class TestRunFiles(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="mv2-longrun-test-")

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_zero_turns_writes_state_and_report(self):
        out = os.path.join(self.d, "out")
        r1 = {"r60": {"status": "UNKNOWN", "turns": 4, "it_total": 4, "sec_total": 600,
                      "classes": [[120, 1]]}}
        state, why = lr.run(out, ["t63", "r60"], {}, r1, hours=1, max_turns=0, log=lambda s: 0)
        self.assertEqual(why, "max_turns")
        with open(os.path.join(out, "state.json"), encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(saved["r60"]["classes"], [[120, 1]])
        rep = open(os.path.join(out, "report.txt"), encoding="utf-8").read()
        self.assertIn("LONG t63:-0/0 r60:U4/600", rep)
        self.assertIn("STATUS new_n=- -=1 UNKNOWN=1 max_turns", rep)
        self.assertTrue(open(os.path.join(out, "done.txt"), encoding="utf-8").read().strip()
                        .endswith("max_turns"))
        # a restart keeps the saved state and adds new tiers
        state2, _ = lr.run(out, ["t63", "r60", "t70"], {}, {}, hours=1, max_turns=0,
                           log=lambda s: 0)
        self.assertEqual(state2["r60"]["turns"], 4)
        self.assertIn("t70", state2)

    def test_report_found(self):
        st = {"t80": {"status": "FOUND", "it_total": 3, "sec_total": 99,
                      "rule": rules_m.rule_to_json(RULE_R80), "cert": {"ok": True}},
              "t63": {"status": "INFEASIBLE", "it_total": 9, "sec_total": 4000}}
        rep = lr.report(st, ["t63", "t80"], "all decided")
        self.assertIn("SANE t80 N=80 n=79", rep)
        self.assertNotIn("RULE ", rep)
        self.assertIn("STATUS new_n=- FOUND=1 INFEASIBLE=1 all decided", rep)


class TestCertify(unittest.TestCase):
    def test_accepts_n079_rule(self):
        ok, cert, speeds, shifts = lr.certify("r80", rules_m.rule_to_json(RULE_R80))
        self.assertTrue(ok, cert)
        self.assertTrue(cert["stand_alone"], cert)
        self.assertEqual(len(speeds), 79)
        self.assertEqual(len(set(speeds)), 79)

    def test_rejects_dropped_runner(self):
        # Drop the added speed 5 (shifts kept): 78 runners. Probe R8 (RESULTS_rules_r.md) found
        # that dropping any single runner of the n = 79 cover with the shifts kept leaves a time
        # uncovered at radius 1/79, so this must not certify as n = 78.
        rule = dict(RULE_R80)
        rule["added"] = {k: v for k, v in RULE_R80["added"].items() if k != 5}
        try:
            ok = lr.certify("r80g2", rules_m.rule_to_json(rule))[0]
        except Exception:
            ok = False
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
