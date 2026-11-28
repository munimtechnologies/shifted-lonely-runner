# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Tests for top_r.py (route 19d, PREREG_rules_r.md). Expected values are worked out by hand in
the comments. No solver is needed: the probes run the CEGAR."""
import unittest
from fractions import Fraction as F

import rules_m
import top_o as to
import top_q as tq
import top_r as tr


class TestTiers(unittest.TestCase):
    def test_tiers(self):
        # r64 (sanity) + r64g2 + r96g2 + gain 1 at the 36 values N = 59..95 except 64
        self.assertEqual(len(tr.ORDER), 39)
        self.assertEqual(len(set(tr.ORDER)), 39)
        self.assertEqual(len(tr.TARGETS), 38)
        self.assertEqual(tr.ORDER[:9], ["r64", "r64g2", "r96g2", "r60", "r75", "r80", "r90",
                                        "r72", "r81"])
        self.assertEqual(tr.TIERS["r75"], (75, 1, to.P5))
        self.assertEqual(tr.TIERS["r96g2"], (96, 2, to.P5))
        ns = sorted({tr.n_of(t) for t in tr.TARGETS})
        self.assertEqual(ns, [n for n in range(58, 95) if n != 63])
        self.assertEqual(tr.n_of("r64g2"), 62)
        self.assertEqual(tr.n_of("r96g2"), 94)

    def test_pools_p5(self):
        # 5-smooth multiples of 4 up to 128 (19 of them), odd 5-smooth up to 129 (11)
        touch, _f, add = to.pools_o(64, to.P5)
        self.assertEqual(touch, [4, 8, 12, 16, 20, 24, 32, 36, 40, 48, 60, 64, 72, 80, 96, 100,
                                 108, 120, 128])
        self.assertEqual(add, [1, 3, 5, 9, 15, 25, 27, 45, 75, 81, 125])
        # the top trick: 2N = 150 = 2 * 3 * 5^2 is touchable at N = 75 with P5, not with P3
        self.assertIn(150, to.pools_o(75, to.P5)[0])
        self.assertNotIn(150, to.pools_o(75, to.P3)[0])
        self.assertNotIn(146, to.pools_o(73, to.P5)[0])  # 146 = 2 * 73

    def test_seeds(self):
        # 10 is not a multiple of 4, so not touchable; the duplicate [8, 1] collapses
        q1 = {"q72": {"classes": [[8, 1], [8, 3], [10, 1], [8, 1]]}}
        self.assertEqual(tr.seeds_for("r72", q1), [[8, 1], [8, 3]])
        q1 = {"q64g2p5": {"classes": [[20, 1]]}, "q64g2": {"classes": [[8, 1], [20, 1]]}}
        self.assertEqual(tr.seeds_for("r64g2", q1), [[8, 1], [20, 1]])
        self.assertEqual(tr.seeds_for("r64", q1), [])
        self.assertEqual(tr.seeds_for("r96g2", q1), [])
        self.assertEqual(tr.seed_sources("r64g2"), ["q64g2p5", "q64g2"])

    def test_q1_lines(self):
        q1 = {"q64": {"status": "FOUND", "it_total": 4, "sec_total": 9, "solve_total": 3,
                      "rule": rules_m.rule_to_json(tq.SIMPLE_63)},
              "q59": {"status": "INFEASIBLE", "it_total": 1, "sec_total": 5, "solve_total": 1}}
        lines = tr.q1_lines(q1)
        # 42 route-19c tiers: 2 known, 40 never run
        self.assertTrue(lines[0].startswith("QSTATE -=40 FOUND=1 INFEASIBLE=1 QIT it=5"))
        self.assertIn("q64:F4/9", lines[1])
        self.assertEqual(lines[2], "QBUG none")
        self.assertEqual(len(lines), 3)  # a sanity tier is never a QRULE


class TestKnownRules(unittest.TestCase):
    """The four certified covers in menu q pass the exact closed-cover test and the global
    endpoint checker."""

    def _cover(self, rule, N, n):
        self.assertEqual(rules_m.gain(rule), N - n)
        self.assertTrue(to.fixed_check(rule, N, g=N - n)[0])
        v, s, _d, k = rules_m.build_config(rule, N)
        self.assertEqual(k, n)
        self.assertEqual(len(set(v)), n)
        self.assertTrue(tq.indep_cover(v, s, F(1, n + 1))[0])

    def test_rule_q64(self):
        self._cover(tr.RULE_Q64, 64, 63)

    def test_rule_q96(self):
        self._cover(tr.RULE_Q96, 96, 95)


class TestClauseSoundness(unittest.TestCase):
    """Every INFEASIBLE of routes 19c and 19d rests on the clauses of top_o.class_clauses_o being
    necessary conditions. A rule that passes fixed_check must therefore falsify none of them."""

    def test_present_keys(self):
        keys = tr.present_keys(tq.SIMPLE_63, 64, to.P3)
        self.assertIn(("u", 4), keys)                    # untouched touchable speed
        self.assertNotIn(("u", 8), keys)                 # removed
        self.assertIn(("e", 16, F(0), F(-3, 2)), keys)   # rephased
        self.assertIn(("o", 9, F(3, 4), F(0)), keys)     # added
        # 13 touchable speeds: 3 removed, 6 rephased, 4 untouched; plus 2 added
        self.assertEqual(len(keys), 6 + 4 + 2)

    def test_certified_rules_falsify_nothing(self):
        cases = [(tq.SIMPLE_63, 64, to.P3), (tq.SIMPLE_63, 64, to.P5),
                 (tr.RULE_Q64, 64, to.P3), (tr.RULE_Q96, 96, to.P3),
                 (rules_m.POLIAKOVA_9_8, 96, to.P3)]
        for rule, N, P in cases:
            self.assertTrue(to.fixed_check(rule, N, g=1)[0])
            bad = tr.violations(rule, N, 1, P)
            self.assertEqual(bad[:3], [], (N, P))

    def test_failing_rules_falsify_something(self):
        # SIMPLE_63 without its two added speeds: gain 3, so n = 61 if it covered; it does not
        # (else route 19c's q64g2 would have been FOUND). Every class whose clause it falsifies
        # must also be a class fixed_check reports as failing.
        r1 = dict(tq.SIMPLE_63, added={})
        # SIMPLE_63 without 9 at gain 2 (n = 62): q64g2 was INFEASIBLE, so this must fail
        r2 = dict(tq.SIMPLE_63, added={3: (F(3, 4), F(0))})
        for rule, g in ((r1, 3), (r2, 2)):
            ok, fails = to.fixed_check(rule, 64, g=g)
            self.assertFalse(ok)
            bad = tr.violations(rule, 64, g, to.P3)
            self.assertTrue(bad)
            failing = {(q, k) for q, k, _z in fails}
            self.assertTrue({(q, k) for q, k, _c in bad} <= failing)


if __name__ == "__main__":
    unittest.main()
