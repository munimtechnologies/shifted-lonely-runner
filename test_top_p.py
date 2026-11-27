# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Tests for top_p.py (route 19b, PREREG_rules_p.md). Expected values are worked out by hand
in the comments. The solver tests need OR-Tools (installed into %TEMP% by ensure_ortools) and
are skipped without it."""
import time
import unittest
from fractions import Fraction as F

import rules_m
import rule_search_s as rs
import top_o as to
import top_p as tp


class TestTiers(unittest.TestCase):
    def test_tiers(self):
        # 59..95 has 37 values; minus 64, 72, 81 leaves 34; plus x64g2, x72, x81 = 37 targets.
        self.assertEqual(len(tp.TARGETS), 37)
        self.assertEqual(len(tp.ORDER), 39)
        self.assertEqual(tp.ORDER[:5], ["pf64x", "ph64", "x64g2", "x72", "x81"])
        self.assertEqual(tp.tier("pf64x"), (64, 1, to.P3, "x", to.DENS_A))
        self.assertEqual(tp.tier("ph64"), (64, 1, to.P3, "h", to.DENS_A))
        self.assertEqual(tp.tier("x64g2")[:2], (64, 2))
        self.assertEqual(tp.tier("x95")[:2], (95, 1))
        # every route-19 target is a route-19b target
        self.assertEqual(set(tp.TARGETS), {t for t in to.ORDER if not t.startswith(("f", "h"))})


class TestReport(unittest.TestCase):
    def test_short_rule_callens(self):
        s = tp.short_rule(rules_m.rule_to_json(to.CALLENS_63))
        self.assertTrue(s.startswith("R=4,8,32,72,96,108 S=12@1/2,1/2 16@0,-1 24@1/2,1/2"), s)
        self.assertIn("128@0,-1", s)
        self.assertTrue(s.endswith("81@3/4,1/8"), s)

    def test_old_lines(self):
        o1 = {"h64": {"status": "FOUND", "rule": rules_m.rule_to_json(to.CALLENS_63)},
              "x72": {"status": "UNKNOWN"}}
        lines = tp.old_lines(o1)
        self.assertTrue(lines[0].startswith("OLD h64 R=4,8,32"))
        # route 19 has 40 tiers (f96h, f64x, h64 and 37 targets): one FOUND, one UNKNOWN,
        # 38 never run
        self.assertEqual(len(to.ORDER), 40)
        self.assertEqual(lines[-1], "O1STATE -=38 FOUND=1 UNKNOWN=1")


class TestSolver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ok, cls.note = rs.ensure_ortools()

    def setUp(self):
        if not self.ok:
            self.skipTest("OR-Tools unavailable: " + self.note[:80])

    def test_feasible_tiny(self):
        # touch {4, 8}; class (4, 1) needs speed 1 at 3/4 unless 4 is untouched.
        # Gain >= 1 is reachable (e.g. remove 8, keep 4), so the model is feasible.
        cl = {(4, 1): [[("o", 1, F(3, 4), F(0))]]}
        st, rule = tp.solve_feas(cl, [4, 8], 1, 10, 2)
        self.assertIn(st, ("FEASIBLE", "OPTIMAL"))
        self.assertGreaterEqual(rules_m.gain(rule), 1)
        untouched4 = 4 not in rule["removed"] and 4 not in rule["rephased"]
        self.assertTrue(untouched4 or 1 in rule["added"], rule)

    def test_infeasible_tiny(self):
        # touch {4}; gain >= 1 forces 4 removed, so neither the rephasing nor "4 untouched"
        # can satisfy the clause of class (4, 1): INFEASIBLE.
        cl = {(4, 1): [[("e", 4, F(1, 2), F(0))]]}
        st, rule = tp.solve_feas(cl, [4], 1, 10, 2)
        self.assertEqual(st, "INFEASIBLE")
        self.assertIsNone(rule)

    def test_cegar_small_agrees(self):
        # N = 8, gain 1 (n = 7), menu h. Whatever the answer, it must be sound: FOUND passes
        # both global checkers, and the old and new solvers never contradict each other.
        t = time.time()
        new = tp.cegar_p(8, 1, to.P3, "h", to.DENS_A, t + 40, workers=4)
        self.assertNotEqual(new["status"], "BUG", new.get("why"))
        if new["status"] == "FOUND":
            rule = rules_m.rule_from_json(new["rule"])
            self.assertTrue(to.fixed_check(rule, 8, g=1)[0])
            self.assertTrue(to.certify(rule, 8, n=7)["ok"])
        old = to.cegar_o(8, 1, to.P3, "h", to.DENS_A, time.time() + 40, workers=4)
        pair = {new["status"], old["status"]}
        self.assertFalse(pair == {"FOUND", "INFEASIBLE"}, (new["status"], old["status"]))


if __name__ == "__main__":
    unittest.main()
