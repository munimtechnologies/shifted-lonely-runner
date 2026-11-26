# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Tests for rule_search_f.py (PREREG_rules_f.md). Standard library only; nothing here needs
OR-Tools."""
import json
import os
import tempfile
import unittest
from fractions import Fraction as F

import rules_m
import rule_search_c as rc
import rule_search_f as rf

POL = rules_m.POLIAKOVA_9_8
H = F(1, 2)


class Plans(unittest.TestCase):
    def test_plans(self):
        for plan in (rf.PLAN_F1, rf.PLAN_F2, rf.PLAN_F3):
            self.assertLessEqual(sum(s for _, s in plan), 530)
            for tag, _ in plan:
                self.assertIn(tag, rf.TIERS_F)
        self.assertEqual(set(rf.ORDER_F), set(rf.TIERS_F))

    def test_thresholds_of_targets(self):
        # a rule meeting a target tier's gain at its L has threshold <= 94
        for tag, (m, L, fix, g, exp) in rf.TIERS_F.items():
            thr = -(-L // m) - g
            if exp == "search":
                self.assertEqual(thr, 94, tag)
            if exp == "find":
                self.assertEqual(thr, 95, tag)

    def test_menus_hold_fixed_parts(self):
        for tag in rf.TIERS_F:
            self.assertEqual(rf.check_menu(tag), [], tag)


class FixedPart(unittest.TestCase):
    def test_all_is_scaled_poliakova(self):
        for m in (2, 4, 6):
            fx = rf.fixed_part(m, "all")
            sc = rules_m.rule_to_json(rules_m.scale(POL, m // 2))
            got = rules_m.rule_to_json(dict(fx, m=m))
            self.assertEqual(got, sc)

    def test_core(self):
        fx = rf.fixed_part(2, "core")
        self.assertEqual(fx["removed"], [8, 32])
        self.assertEqual(sorted(fx["rephased"]), [12, 16, 24, 48, 64, 96])
        self.assertEqual(fx["added"], {})
        fx6 = rf.fixed_part(6, "core")
        self.assertEqual(fx6["removed"], [24, 96])
        self.assertEqual(sorted(fx6["rephased"]), [36, 48, 72, 144, 192, 288])
        self.assertEqual(fx6["rephased"][288], (H, H))
        self.assertEqual(fx6["rephased"][192], (F(0), F(-1)))
        with self.assertRaises(ValueError):
            rf.fixed_part(3, "core")

    def test_core_has_gain_zero_without_adds(self):
        # the core alone (no adds) leaves 2 removals; Poliakova pays them with 2 adds
        fx = rf.fixed_part(4, "core")
        self.assertEqual(len(fx["removed"]), 2)

    def test_forced_keys_match_clause_keys(self):
        # m = 2: class (12, 7): the added 3 at shift 1/4 covers all of [-1, 1] (c = 1/4)
        m, L, touch, fixed, added, betas, dens, fix, g = rf.menu("f2S")
        keys = set(rf.forced_keys(rf.fixed_part(2, "all")))
        self.assertIn(("o", 3, F(1, 4), F(0)), keys)
        cls = rc.class_clauses(12, 7, touch, fixed, added, betas, dens)
        self.assertTrue(cls)
        for clause in cls:
            self.assertIn(("o", 3, F(1, 4), F(0)), clause)
        # m = 6: class (576, 1): the rephased 288 at (1/2, 1/2) covers all of [-1, 1]
        m, L, touch, fixed, added, betas, dens, fix, g = rf.menu("f6S")
        keys6 = set(rf.forced_keys(rf.fixed_part(6, "all")))
        self.assertIn(("e", 288, H, H), keys6)
        cls = rc.class_clauses(576, 1, touch, fixed, added, betas, dens)
        self.assertTrue(cls)
        for clause in cls:
            self.assertIn(("e", 288, H, H), clause)


class Soundness(unittest.TestCase):
    """The scaled rule passes the exact criterion at the sanity tiers' L, and satisfies the
    sampled clauses of the f-menus (the escape literal unt[q] is false for touched q)."""

    def _sat(self, tag, per_q):
        m, L, touch, fixed, added, betas, dens, fix, g = rf.menu(tag)
        fx = rf.fixed_part(m, "all")
        keys = set(rf.forced_keys(fx))
        X = set(fx["removed"]) | set(fx["rephased"])
        for q in sorted(X):
            for k in rc._spread(rules_m.responsible_classes(q, m), per_q):
                for clause in rc.class_clauses(q, k, touch, fixed, added, betas, dens):
                    sat = any((key[1] not in X) if key[0] == "u" else (key in keys)
                              for key in clause)
                    self.assertTrue(sat, (tag, q, k, clause[:4]))

    def test_f2S_clauses(self):
        self._sat("f2S", 8)

    def test_f6S_clauses(self):
        self._sat("f6S", 3)

    def test_scaled_rules_pass(self):
        for m, L in ((4, 384), (6, 576)):
            r = rules_m.scale(POL, m // 2)
            ok, fails = rules_m.local_check(r, untouched_upto=L)
            self.assertTrue(ok, fails[:3])
            self.assertEqual(rules_m.threshold(r, untouched_upto=L), 95)


class Bookkeeping(unittest.TestCase):
    def test_probe_without_solver(self):
        d = tempfile.mkdtemp(prefix="mv2-test-rules-f-")
        e = tempfile.mkdtemp(prefix="mv2-test-rules-fe-")
        with open(os.path.join(d, "tiers.json"), "w", encoding="utf-8") as f:
            json.dump({"f2G2": {"m": 2, "L": 192, "fix": "all", "min_gain": 2,
                                "status": "INFEASIBLE", "iterations_total": 2,
                                "n_classes": 40, "literals": 900, "seconds_total": 12.3}}, f)
        with open(os.path.join(e, "tiers.json"), "w", encoding="utf-8") as f:
            json.dump({"c2neg": {"status": "UNKNOWN", "n_infeasible": 29, "n_cubes": 38,
                                 "frontier": 72}}, f)
        rep = rf.probe_f([], budget=30, cache=d, e_cache=e)
        self.assertIn("f2G2 m=2 L=192 fix=all g>=2 st=INFEASIBLE", rep)
        self.assertIn("11c c2neg=UNKNOWN/29/38/fr72", rep)
        self.assertTrue(rep.rstrip().splitlines()[-1].startswith("STATUS f2G2=INFEASIBLE"))
        self.assertEqual(rf.e_summary(tempfile.mkdtemp(prefix="mv2-test-rules-fx-")),
                         "11c none")


if __name__ == "__main__":
    unittest.main()
