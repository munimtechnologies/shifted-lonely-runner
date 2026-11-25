# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2). Made with AI agents working in MV2's name.
"""Tests for rules_m.py and rule_search_m.py (standard library only). Every expected value
is worked out by hand in the comments, or follows from the scaling remark proved in the
rules_m docstring applied to Poliakova's published rule."""
import unittest
from fractions import Fraction as F

import rules_m
import rule_search_m
import slr

P = rules_m.POLIAKOVA_9_8
TOY = rules_m.TOY_M4


class TestClasses(unittest.TestCase):
    def test_classes(self):
        # m = 2 agrees with rules.py: q = 12 -> gcd(k, 6) = 1.
        self.assertEqual(rules_m.responsible_classes(12, 2), [1, 5, 7, 11])
        # m = 4, q = 8: gcd(k, 2) = 1 -> odd k.
        self.assertEqual(rules_m.responsible_classes(8, 4), [1, 3, 5, 7])
        # m = 3, q = 6: gcd(k, 2) = 1 -> 1, 3, 5.
        self.assertEqual(rules_m.responsible_classes(6, 3), [1, 3, 5])
        # m = 3, q = 3: gcd(k, 1) = 1 for every k (gcd(0, 1) = 1).
        self.assertEqual(rules_m.responsible_classes(3, 3), [0, 1, 2])
        # m = 6, q = 18: gcd(k, 3) = 1.
        self.assertEqual(rules_m.responsible_classes(18, 6),
                         [1, 2, 4, 5, 7, 8, 10, 11, 13, 14, 16, 17])
        with self.assertRaises(ValueError):
            rules_m.responsible_classes(10, 4)


class TestPoliakovaAndScaling(unittest.TestCase):
    def test_modulus_2(self):
        self.assertEqual(rules_m.shape_problems(P), [])
        self.assertEqual(rules_m.gain(P), 1)
        self.assertEqual(rules_m.largest(P), 192)
        self.assertEqual(rules_m.threshold(P), 95)  # Poliakova's n >= 95
        ok, fails = rules_m.local_check(P)
        self.assertTrue(ok, fails[:5])

    def test_scaled(self):
        # Scaling by u keeps the criterion and the threshold (rules_m docstring).
        for u in (2, 3):
            r = rules_m.scale(P, u)
            self.assertEqual(rules_m.modulus(r), 2 * u)
            self.assertEqual(rules_m.shape_problems(r), [])
            self.assertEqual(rules_m.largest(r), 192 * u)
            self.assertEqual(rules_m.threshold(r), 95)
            ok, fails = rules_m.local_check(r)
            self.assertTrue(ok, (u, fails[:5]))

    def test_scaled_broken(self):
        # Without 9 (scaled: 27), classes k = 1 mod 4 of q = 12 (scaled: 36) lose their cover.
        # In modulus 6 the classes of 36 are k mod 36 with gcd(k, 6) = 1; those with
        # k = 1 mod 4 are 1, 5, 13, 17, 25, 29.
        r = rules_m.scale(P, 3)
        r["added"] = {9: (F(1, 4), 0)}
        ok, fails = rules_m.local_check(r)
        self.assertFalse(ok)
        self.assertEqual(sorted((q, k) for q, k, _ in fails),
                         [(36, 1), (36, 5), (36, 13), (36, 17), (36, 25), (36, 29)])

    def test_bad_shapes(self):
        # Added speed 12 is a multiple of m = 6; removed 10 is not.
        r = {"m": 6, "removed": [10], "rephased": {}, "added": {12: (F(1, 4), 0)}}
        probs = rules_m.shape_problems(r)
        self.assertEqual(len(probs), 2)
        ok, _ = rules_m.local_check(r)
        self.assertFalse(ok)


class TestToyModulus4(unittest.TestCase):
    def test_local(self):
        self.assertEqual(rules_m.gain(TOY), -1)
        self.assertEqual(rules_m.threshold(TOY), 3)  # ceil(8/4) + 1
        ok, fails = rules_m.local_check(TOY)
        self.assertTrue(ok, fails)
        run = rules_m.covering_runners(TOY)
        # k = 1: only runner 2 matches (1/4 + 3/4 = 1); interval [-4, 4].
        self.assertEqual(rules_m.intervals(8, 1, run), [(F(-4), F(4), 2)])
        # k = 3: only runner 6 matches (9/4 + 3/4 = 3); interval [-4/3, 4/3].
        self.assertEqual(rules_m.intervals(8, 3, run), [(F(-4, 3), F(4, 3), 6)])

    def test_broken(self):
        r = {"m": 4, "removed": [8], "rephased": {}, "added": {2: (F(3, 4), 0)}}
        ok, fails = rules_m.local_check(r)
        self.assertFalse(ok)
        self.assertEqual(sorted((q, k) for q, k, _ in fails), [(8, 3), (8, 7)])

    def test_global(self):
        # N = 2: speeds 4, 2, 6 with shifts 0, 3/4, 3/4 form a closed cover at delta = 1/3.
        # By hand: 4 covers t within 1/12 of a multiple of 1/4; 2 covers [-1/24, 7/24] and
        # [11/24, 19/24]; 6 covers [23/72, 31/72] and [59/72, 67/72]; together all of [0, 1].
        # Open arcs of any radius > 1/3, e.g. 2/5, therefore cover.
        v, s, delta, n = rules_m.build_config(TOY, 2)
        self.assertEqual((v, s, delta, n), ([4, 2, 6], [F(0), F(3, 4), F(3, 4)], F(1, 3), 3))
        self.assertTrue(slr.covers_sweep(v, s, F(2, 5))[0])
        self.assertTrue(slr.covers_endpoints(v, s, F(2, 5))[0])
        # N = 3 (claim: m N = 12 >= L = 8): closed cover at 1/4, so radius 2/7 > 1/4 covers.
        v, s, delta, n = rules_m.build_config(TOY, 3)
        self.assertEqual(v, [4, 12, 2, 6])
        self.assertEqual(delta, F(1, 4))
        self.assertTrue(slr.covers_sweep(v, s, F(2, 7))[0])
        self.assertTrue(slr.covers_endpoints(v, s, F(2, 7))[0])

    def test_scaled_poliakova_global(self):
        # Modulus 6 version of Poliakova's rule at N = 96: n = 95 runners, closed cover at
        # 1/97, so radius 2/193 (< 1/96) covers. (It is her n = 95 configuration with every
        # speed tripled, so this checks build_config for m = 6.)
        r = rules_m.scale(P, 3)
        v, s, delta, n = rules_m.build_config(r, 96)
        self.assertEqual(n, 95)
        self.assertEqual(len(set(v)), 95)
        self.assertIn(9, v)
        self.assertIn(27, v)
        self.assertNotIn(576, v)
        self.assertTrue(slr.covers_sweep(v, s, F(2, 193))[0])

    def test_json_roundtrip(self):
        for r in (TOY, rules_m.scale(P, 3)):
            back = rules_m.rule_from_json(rules_m.rule_to_json(r))
            self.assertEqual(rules_m.rule_to_json(back), rules_m.rule_to_json(r))


class TestEncoder(unittest.TestCase):
    def test_pools(self):
        self.assertEqual(rule_search_m.pools(12, 7, 4), ([4, 8, 12], [1, 2, 3, 5, 6, 7]))

    def test_single_segment_m4(self):
        # q = 8, k = 1, m = 4, beta = 0. Base 4: c = 1/2, sigma0 = 1/2, [-2, 2]; base 8: c = 1,
        # sigma0 = 0 -> untouched key, [-1, 1]; added 2: c = 1/4, sigma0 = 3/4, [-4, 4];
        # added 6: c = 3/4, sigma0 = 1/4, [-4/3, 4/3]. All cover (-1, 1): one clause.
        cl = rule_search_m.pair_clauses(8, 1, [4, 8], [2, 6], [F(0)], {1, 2, 4})
        self.assertEqual(cl, [[("e", 4, F(1, 2), 0), ("u", 8),
                               ("o", 2, F(3, 4), 0), ("o", 6, F(1, 4), 0)]])

    def test_toy_satisfies_encoding(self):
        cl, _ = rule_search_m.all_clauses(8, 7, 4, rule_search_m.halves(), {1, 2, 4})
        self.assertEqual(rule_search_m.clauses_satisfied(TOY, cl), [])
        broken = {"m": 4, "removed": [8], "rephased": {}, "added": {2: (F(3, 4), 0)}}
        self.assertEqual(rule_search_m.clauses_satisfied(broken, cl), [(8, 3), (8, 7)])

    def test_scaled_poliakova_satisfies_encoding(self):
        r = rules_m.scale(P, 3)
        cl, _ = rule_search_m.all_clauses(576, 27, 6, rule_search_m.halves(),
                                          {1, 2, 3, 4, 6}, qs=[24, 36, 48])
        self.assertEqual(rule_search_m.clauses_satisfied(r, cl), [])
        broken = rules_m.scale(P, 3)
        broken["added"] = {9: (F(1, 4), 0)}
        bad = rule_search_m.clauses_satisfied(broken, cl)
        self.assertEqual(bad, [(36, 1), (36, 5), (36, 13), (36, 17), (36, 25), (36, 29)])


if __name__ == "__main__":
    unittest.main()
