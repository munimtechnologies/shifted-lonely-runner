# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Standard-library tests for route 14 (rule_search_i.py, PREREG_rules_i.md). No OR-Tools."""
import os
import tempfile
import unittest
from fractions import Fraction as F

import rule_search_g as rg
import rule_search_i as ri
import slr


class TestScaledHint(unittest.TestCase):
    def test_m2_is_poliakova(self):
        for N in (64, 72, 96):
            self.assertEqual(ri.scaled_poliakova(2, N), rg.poliakova_cand(N))

    def test_odd_m_refused(self):
        with self.assertRaises(ValueError):
            ri.scaled_poliakova(3, 96)

    def _exact_cover(self, m):
        N, n = 96, 95
        Md, _shifts = rg.shift_menu(N)
        h = ri.scaled_poliakova(m, N)
        v, s = rg.config_of(h, m, N, Md)
        self.assertEqual(len(v), n)
        self.assertEqual(len(set(v)), n)
        ok, x = slr.covers_sweep(v, s, F(1, n + 1))
        self.assertTrue(ok, "uncovered point %s" % (x,))

    def test_scaled_rule_is_a_95_runner_cover_m4(self):
        # the sanity tier s4H is satisfiable: scaling every speed keeps a cover
        self._exact_cover(4)

    def test_scaled_rule_is_a_95_runner_cover_m6(self):
        self._exact_cover(6)

    def test_hint_lies_in_menu_at_96(self):
        for m in (2, 4, 6):
            full = ri.scaled_poliakova(m, 96)
            got = ri.hint_in_menu(m, 96, rg.P5)
            self.assertEqual(sorted(got["removed"]), sorted(full["removed"]))
            self.assertEqual(got["rephased"], full["rephased"])
            self.assertEqual(got["added"], full["added"])

    def test_hint_at_smaller_N_drops_only_speeds_beyond_the_base(self):
        got = ri.hint_in_menu(6, 72, rg.P5)
        full = ri.scaled_poliakova(6, 72)
        for w in full["removed"]:
            self.assertEqual(w in got["removed"], w <= 6 * 72)
        self.assertEqual(got["added"], full["added"])


class TestTiers(unittest.TestCase):
    def test_tiers(self):
        self.assertEqual(set(ri.ORDER_I), set(ri.TIERS_I))
        self.assertEqual(ri.ORDER_I[0], "s4H")
        for tag, (m, n, N, P, hint) in ri.TIERS_I.items():
            self.assertGreaterEqual(N - n, 1)
            self.assertEqual(hint, m % 2 == 0, tag)
            if tag != "s4H":
                self.assertIn(n, ri.OPEN, tag)
            touch, _f, added = rg.pools_g(m, N, P)
            self.assertTrue(touch and added)
        self.assertNotIn(63, ri.OPEN)
        self.assertNotIn(57, ri.OPEN)
        self.assertNotIn(95, ri.OPEN)

    def test_register_is_local_and_reversible(self):
        saved = rg.poliakova_cand
        try:
            ri._register("e6N72")
            self.assertEqual(rg.TIERS_G["e6N72"][:4], (6, 71, 72, rg.P5))
            self.assertEqual(rg.poliakova_cand(72), ri.scaled_poliakova(6, 72))
        finally:
            rg.poliakova_cand = saved
            rg.TIERS_G.pop("e6N72", None)
        self.assertEqual(rg.poliakova_cand(96), ri.scaled_poliakova(2, 96))

    def test_line_and_cache_line(self):
        r = {"m": 6, "n": 71, "N": 72, "status": "UNKNOWN", "iterations_total": 3,
             "n_clauses": 10, "tl": 45.0, "seconds_total": 12.3, "turns": 1}
        line = ri.line_i("e6N72", r)
        self.assertIn("st=UNKNOWN", line)
        self.assertIn("turns=1", line)
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(ri.h_cache_line(d), "13b solver=None ")
            self.assertEqual(ri.h_cache_line(os.path.join(d, "missing")), "13b none")


if __name__ == "__main__":
    unittest.main()
