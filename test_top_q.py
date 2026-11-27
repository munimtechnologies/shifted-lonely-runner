# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Tests for top_q.py (route 19c, PREREG_rules_q.md). Expected values are worked out by hand in
the comments. The solver test needs OR-Tools (installed into %TEMP% by ensure_ortools) and is
skipped without it."""
import random
import time
import unittest
from fractions import Fraction as F

import rules_m
import rule_search_s as rs
import slr
import top_o as to
import top_p as tp
import top_q as tq


class TestTiers(unittest.TestCase):
    def test_tiers(self):
        # gain 1 for N = 59..95 except 64: 36 tiers; gain 2 at 64, 96 with P3 and P5: 4.
        self.assertEqual(len(tq.TARGETS), 40)
        self.assertEqual(len(set(tq.TARGETS)), 40)
        self.assertEqual(len(tq.ORDER), 42)
        self.assertEqual(tq.ORDER[:4], ["q64", "q96", "q64g2", "q96g2"])
        self.assertEqual(tq.TARGETS[-2:], ["q64g2p5", "q96g2p5"])
        self.assertEqual(tq.TIERS["q95"], (95, 1, to.P3))
        self.assertEqual(tq.TIERS["q64g2p5"], (64, 2, to.P5))
        # the targets cover n = 58..94 except 63 (known), plus n = 62 and 94 again at gain 2
        ns = sorted({tq.n_of(t) for t in tq.TARGETS})
        self.assertEqual(ns, [n for n in range(58, 95) if n != 63])
        self.assertEqual(tq.n_of("q64g2"), 62)
        self.assertEqual(tq.n_of("q96g2"), 94)

    def test_seed_tags(self):
        self.assertEqual(tq.seed_tag("q72"), "x72")
        self.assertEqual(tq.seed_tag("q64g2"), "x64g2")
        self.assertIsNone(tq.seed_tag("q96g2"))
        self.assertIsNone(tq.seed_tag("q64g2p5"))
        self.assertIsNone(tq.seed_tag("q64"))
        # every seed tag of a target is a route-19b target
        for t in tq.TARGETS:
            st = tq.seed_tag(t)
            if st is not None:
                self.assertIn(st, tp.TARGETS)

    def test_seeds_for(self):
        # 10 is not a multiple of 4, so not touchable at N = 72; the duplicate [8, 1] collapses.
        cl = {"x72": {"classes": [[8, 1], [8, 3], [10, 1], [8, 1]]}}
        self.assertEqual(tq.seeds_for("q72", cl, {}), [[8, 1], [8, 3]])
        self.assertEqual(tq.seeds_for("q72", {}, cl), [[8, 1], [8, 3]])  # route-19 fallback
        self.assertEqual(tq.seeds_for("q96g2", cl, cl), [])
        # at most per_q per speed: _spread([1, 3, 5, 7], 2) = [1, 5]
        cl4 = {"x72": {"classes": [[8, 1], [8, 3], [8, 5], [8, 7]]}}
        self.assertEqual(tq.seeds_for("q72", cl4, {}, per_q=2), [[8, 1], [8, 5]])


class TestMenu(unittest.TestCase):
    def _in_menu(self, rule, N, P):
        _m, removed, reph, added = rules_m._norm_rule(rule)
        touch, _fixed, add_pool = to.pools_o(N, P)
        s0s = set(to.s0_menu(tq.DENS_Q))
        betas = set(to.betas_of(tq.KIND))
        self.assertTrue(set(removed) <= set(touch), removed)
        self.assertTrue(set(reph) <= set(touch), reph)
        self.assertTrue(set(added) <= set(add_pool), added)
        for s0, b in list(reph.values()) + list(added.values()):
            self.assertIn(s0, s0s)
            self.assertIn(b, betas)

    def test_menu_values(self):
        # quarters for s0; halves of delta on [-2, 2] for beta (9 values)
        self.assertEqual(to.s0_menu(tq.DENS_Q), [F(0), F(1, 4), F(1, 2), F(3, 4)])
        self.assertEqual(len(to.betas_of(tq.KIND)), 9)
        # 3-smooth multiples of 4 up to 128 (128 = 2N is one of them), odd 3-smooth up to 129
        touch, _f, add = to.pools_o(64, to.P3)
        self.assertEqual(touch, [4, 8, 12, 16, 24, 32, 36, 48, 64, 72, 96, 108, 128])
        self.assertEqual(add, [1, 3, 9, 27, 81])

    def test_known_rules_in_menu(self):
        self._in_menu(tq.SIMPLE_63, 64, to.P3)
        self._in_menu(rules_m.POLIAKOVA_9_8, 96, to.P3)
        self.assertEqual(rules_m.gain(tq.SIMPLE_63), 1)
        # 3 removed + 6 rephased + 2 added = 11 touched; 64 - 3 + 2 = 63 runners
        _m, rem, reph, add = rules_m._norm_rule(tq.SIMPLE_63)
        self.assertEqual(len(rem) + len(reph) + len(add), 11)
        self.assertEqual(rules_m.build_config(tq.SIMPLE_63, 64)[3], 63)


class TestIndep(unittest.TestCase):
    def test_hand_cases(self):
        # one arc of radius 1/4 cannot cover
        self.assertFalse(tq.indep_cover([1], [0], F(1, 4))[0])
        # (-1/3, 1/3) and (1/6, 5/6) cover the circle
        self.assertTrue(tq.indep_cover([1, 1], [0, F(1, 2)], F(1, 3))[0])
        # (-1/4, 1/4) and (1/4, 3/4) miss 1/4 and 3/4
        ok, x = tq.indep_cover([1, 1], [0, F(1, 2)], F(1, 4))
        self.assertFalse(ok)
        self.assertIn(x, (F(1, 4), F(3, 4)))

    def test_agrees_with_slr(self):
        rnd = random.Random(20261127)
        for _ in range(250):
            k = rnd.randint(2, 4)
            v = rnd.sample(range(1, 10), k)
            s = [F(rnd.randrange(6), 6) for _ in v]
            R = rnd.choice([F(1, 3), F(1, 4), F(2, 7), F(1, 5)])
            a, _ = slr.covers_sweep(v, s, R)
            b, _ = tq.indep_cover(v, s, R)
            self.assertEqual(a, b, (v, s, R))

    def test_callens(self):
        v, s, _d, k = rules_m.build_config(to.CALLENS_63, 64)
        self.assertEqual(k, 63)
        self.assertTrue(tq.indep_cover(v, s, F(1, 64))[0])


class TestSolver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ok, cls.note = rs.ensure_ortools()

    def setUp(self):
        if not self.ok:
            self.skipTest("OR-Tools unavailable: " + self.note[:80])

    def test_sanity_tier_sound(self):
        # N = 64, gain 1 in menu q from scratch. Whatever the answer, it must be sound: a FOUND
        # rule passes all three global checkers at R = 1/64.
        info = tp.cegar_p(64, 1, to.P3, tq.KIND, tq.DENS_Q, time.time() + 90, workers=8)
        self.assertNotEqual(info["status"], "BUG", info.get("why"))
        self.assertNotEqual(info["status"], "INFEASIBLE")  # SIMPLE_63 is in the menu
        if info["status"] == "FOUND":
            rule = rules_m.rule_from_json(info["rule"])
            self.assertTrue(to.fixed_check(rule, 64, g=1)[0])
            c = tq.full_cert(rule, 64, 63)
            self.assertTrue(c["ok"], {k: c[k] for k in c if k not in ("speeds", "shifts")})


if __name__ == "__main__":
    unittest.main()
