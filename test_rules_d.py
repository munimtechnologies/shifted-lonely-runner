# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Tests for rule_search_d.py (PREREG_rules_d.md). Standard library only; nothing here needs
OR-Tools."""
import json
import os
import tempfile
import unittest
from fractions import Fraction as F

import rules_m
import rule_search_m
import rule_search_c as rc
import rule_search_d as rd

POL = rules_m.POLIAKOVA_9_8


class Tiers(unittest.TestCase):
    def test_order_and_plans(self):
        self.assertTrue(set(rd.ORDER_D) <= set(rd.TIERS_D))
        for plan in (rd.PLAN_D1, rd.PLAN_D2, rd.PLAN_D3):
            self.assertLessEqual(sum(c for _, c in plan), 530)
            for tag, _ in plan:
                self.assertIn(tag, rd.TIERS_D)

    def test_c6chk_threshold(self):
        m, L, P, kind, dens, exp = rd.TIERS_D["c6chk"]
        self.assertEqual((m, L, exp), (6, 576, "find"))
        self.assertEqual(L // m - 1, 95)  # Poliakova's threshold, unchanged by scaling


class ScaledPoliakova(unittest.TestCase):
    """c6chk must contain Poliakova's rule scaled by 3, and that rule must pass the exact
    criterion on the m = 6 base with helpers up to 576."""

    def setUp(self):
        self.sc = rules_m.scale(POL, 3)
        m, L, P, kind, dens, _ = rd.TIERS_D["c6chk"]
        self.touch, self.fixed, self.added = rc.pools_c(m, L, P)
        self.betas = rule_search_m.halves() if kind == "h" else rule_search_m.quarters()
        self.dens = dens

    def test_in_menu(self):
        sc = self.sc
        for w in list(sc["removed"]) + list(sc["rephased"]):
            self.assertIn(w, self.touch)
        for a in sc["added"]:
            self.assertIn(a, self.added)
        for s0, b in list(sc["rephased"].values()) + list(sc["added"].values()):
            self.assertIn(F(s0).denominator, self.dens)
            self.assertIn(F(b), self.betas)

    def test_passes_local_check(self):
        ok, fails = rules_m.local_check(self.sc, untouched_upto=576)
        self.assertTrue(ok, fails[:3])
        self.assertEqual(rules_m.threshold(self.sc, untouched_upto=576), 95)


class Hints(unittest.TestCase):
    def test_hint_values(self):
        touch = [6, 12, 18]
        cand = {"removed": [12], "rephased": {18: (F(1, 2), F(1, 2))},
                "added": {3: (F(1, 4), F(0))}}
        keys = [("e", 18, F(1, 2), F(1, 2)), ("e", 18, F(0), F(1)), ("e", 6, F(1, 2), F(0)),
                ("o", 3, F(1, 4), F(0)), ("o", 3, F(3, 4), F(0)), ("o", 9, F(1, 4), F(0))]
        rem, unt, opt = rd.hint_values(cand, touch, keys)
        self.assertEqual(rem, {6: 0, 12: 1, 18: 0})
        self.assertEqual(unt, {6: 1, 12: 0, 18: 0})
        self.assertEqual([opt[k] for k in keys], [1, 0, 0, 1, 0, 0])


class Seeding(unittest.TestCase):
    def test_seed_state(self):
        c_state = {
            "c2chk": {"status": "FOUND", "classes": [[12, 1]], "rule": {"m": 2}},
            "c3A58": {"status": "INFEASIBLE", "classes": [[3, 1]]},
            "c6A58": {"status": "UNKNOWN", "classes": [[6, 1], [12, 5]],
                      "iterations_total": 8, "seconds_total": 816},
            "zzz": {"status": "INFEASIBLE"},
        }
        st = rd.seed_state({"c4A58": {"status": "UNKNOWN", "classes": []}}, c_state)
        self.assertEqual(st["c2chk"]["status"], "FOUND")
        self.assertNotIn("classes", st["c2chk"])
        self.assertEqual(st["c3A58"]["status"], "INFEASIBLE")
        self.assertEqual(st["c6A58"]["classes"], [[6, 1], [12, 5]])
        self.assertEqual(st["c6A58"]["seconds_total"], 816)
        self.assertNotIn("zzz", st)
        self.assertEqual(st["c4A58"]["classes"], [])

    def test_probe_reports_decided_without_solver(self):
        d = tempfile.mkdtemp(prefix="mv2-test-rules-d-")
        c = tempfile.mkdtemp(prefix="mv2-test-rules-dc-")
        with open(os.path.join(c, "tiers.json"), "w", encoding="utf-8") as f:
            json.dump({"c3A58": {"status": "INFEASIBLE", "classes": []}}, f)
        rep = rd.probe_d([], budget=60, cache=d, c_cache=c)
        self.assertIn("STATUS c3A58=INFEASIBLE", rep)


class Certification(unittest.TestCase):
    def test_certify_poliakova_95(self):
        d = tempfile.mkdtemp(prefix="mv2-test-rules-d-cert-")
        import time
        found = {"tag": "test", "L": 192, "rule": rules_m.rule_to_json(POL), "threshold": 95}
        line = rd.certify(found, d, time.time() + 300, nmax=95)
        self.assertIn("CERTIFIED n=95 FAILED=- missing_58_94=58-94", line)


if __name__ == "__main__":
    unittest.main()
