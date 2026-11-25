# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2). Made with AI agents working in MV2's name.
"""Tests for rules.py. Standard library only. Every expected value is worked out by hand
in the comments (or follows from a published theorem that is cited)."""
import unittest
from fractions import Fraction as F

import rules
import slr


class TestClasses(unittest.TestCase):
    def test_classes(self):
        # q = 2: gcd(k, 1) = 1 for k = 0, 1.
        self.assertEqual(rules.responsible_classes(2), [0, 1])
        # q = 6: gcd(k, 3) = 1 -> 1, 2, 4, 5.
        self.assertEqual(rules.responsible_classes(6), [1, 2, 4, 5])
        # q = 12: gcd(k, 6) = 1 -> 1, 5, 7, 11.
        self.assertEqual(rules.responsible_classes(12), [1, 5, 7, 11])
        # q = 8: odd k.
        self.assertEqual(rules.responsible_classes(8), [1, 3, 5, 7])


class TestClosedCover(unittest.TestCase):
    def test_cover(self):
        ok, _ = rules.closed_cover([(F(-1), F(0)), (F(0), F(1))])
        self.assertTrue(ok)  # closed intervals meeting at 0
        ok, z = rules.closed_cover([(F(-1), F(0)), (F(1, 10), F(1))])
        self.assertFalse(ok)
        self.assertEqual(z, 0)
        ok, z = rules.closed_cover([(F(-1, 2), F(2))])
        self.assertFalse(ok)
        self.assertEqual(z, -1)
        ok, _ = rules.closed_cover([(F(-3), F(1, 3)), (F(-1, 3), F(1))])
        self.assertTrue(ok)
        ok, z = rules.closed_cover([(F(-3), F(1, 3)), (F(-1, 3), F(9, 10))])
        self.assertFalse(ok)
        self.assertEqual(z, F(9, 10))


class TestPoliakova(unittest.TestCase):
    """Poliakova's Theorem 7 (9 -> 8 rule) and the Table 1 variant must pass the
    criterion with no help from untouched runners (her rules are 'local')."""

    def test_main_rule(self):
        r = rules.POLIAKOVA_9_8
        self.assertEqual(rules.shape_problems(r), [])
        self.assertEqual(rules.gain(r), 1)
        self.assertEqual(rules.largest(r), 192)
        ok, fails = rules.local_check(r)
        self.assertTrue(ok, fails[:5])

    def test_variant(self):
        ok, fails = rules.local_check(rules.POLIAKOVA_9_8_VARIANT)
        self.assertTrue(ok, fails[:5])

    def test_q8_by_hand(self):
        # q = 8, k = 1: runner 12 at (1/2, 1/2) has c = 3/2, 3/2 + 1/2 = 2, interval
        # [(-3/2)/(3/2), (1/2)/(3/2)] = [-1, 1/3]; runner 16 at (0, -1) has c = 2,
        # interval [0, 1]; runner 64 at (0, -1) has c = 8, interval [0, 1/4].
        run = rules.covering_runners(rules.POLIAKOVA_9_8)
        iv = sorted((a, b, w) for a, b, w in rules.intervals(8, 1, run))
        self.assertEqual(iv, [(F(-1), F(1, 3), 12), (F(0), F(1, 4), 64), (F(0), F(1), 16)])

    def test_broken_missing_9(self):
        r = {"removed": rules.POLIAKOVA_9_8["removed"],
             "rephased": rules.POLIAKOVA_9_8["rephased"],
             "added": {3: (F(1, 4), 0)}}
        ok, fails = rules.local_check(r)
        self.assertFalse(ok)
        # Without 9, the classes k = 1, 5 (= 1 mod 4) of q = 12 lose their cover.
        self.assertEqual(sorted((q, k) for q, k, _ in fails), [(12, 1), (12, 5)])

    def test_broken_untilted_16(self):
        reph = dict(rules.POLIAKOVA_9_8["rephased"])
        reph[16] = (F(1, 2), 0)  # 16 moved half a lap instead of tilted by -delta
        r = {"removed": [8, 32, 192], "rephased": reph, "added": {3: (F(1, 4), 0), 9: (F(1, 4), 0)}}
        ok, fails = rules.local_check(r)
        self.assertFalse(ok)
        self.assertIn(8, {q for q, _, _ in fails})

    def test_identity_rephase_rejected(self):
        r = {"removed": [4], "rephased": {6: (0, 0)}, "added": {}}
        self.assertTrue(rules.shape_problems(r))


class TestEncoder(unittest.TestCase):
    """rule_search's clause builder (pure Python; the solver itself needs ortools)."""

    def test_single_segment(self):
        import rule_search
        # q = 4, k = 1, beta = 0 only. 2: c = 1/2, sigma0 = -1/2 = 1/2 mod 1, [-2, 2];
        # 4: c = 1, sigma0 = 0 -> untouched key, [-1, 1]; 1: c = 1/4, sigma0 = 3/4, [-4, 4];
        # 3: c = 3/4, sigma0 = 1/4, [-4/3, 4/3]. All cover (-1, 1): one clause of 4 keys.
        cl = rule_search.pair_clauses(4, 1, [2, 4], [1, 3], [F(0)], {1, 2, 4})
        self.assertEqual(cl, [[("e", 2, F(1, 2), 0), ("u", 4),
                               ("o", 1, F(3, 4), 0), ("o", 3, F(1, 4), 0)]])

    def test_two_halves(self):
        import rule_search
        # q = 8, k = 1, only 16 (c = 2, sigma0 = 0): beta = -1 -> [0, 1], beta = 1 -> [-1, 0].
        cl = rule_search.pair_clauses(8, 1, [16], [], [F(-1), F(1)], {1})
        self.assertEqual(sorted(cl), sorted([[("e", 16, F(0), F(-1))], [("e", 16, F(0), F(1))]]))

    def test_gap_gives_empty_clause(self):
        import rule_search
        # beta in {-1, 0}: [0, 1] and [-1/2, 1/2]; (-1, -1/2) is covered by nothing.
        cl = rule_search.pair_clauses(8, 1, [16], [], [F(-1), F(0)], {1})
        self.assertEqual(cl, [[]])

    def test_poliakova_satisfies_encoding(self):
        import rule_search
        cl, _ = rule_search.all_clauses(192, 9, rule_search.halves(), {1, 2, 3, 4, 6}, qs=[8, 12, 16])
        self.assertEqual(rule_search.clauses_satisfied(rules.POLIAKOVA_9_8, cl), [])
        broken = {"removed": [8, 32, 192], "rephased": rules.POLIAKOVA_9_8["rephased"],
                  "added": {3: (F(1, 4), 0)}}
        bad = rule_search.clauses_satisfied(broken, cl)
        self.assertEqual(sorted(bad), [(12, 1), (12, 5)])


class TestGlobal(unittest.TestCase):
    def test_base_config_semantics(self):
        # Base 2, 4, ..., 40 (N = 20), no shifts: loneliness exactly 1/21, so open arcs of
        # radius 1/21 miss t = 1/42, and open arcs of radius 2/41 > 1/21 cover.
        v = list(range(2, 41, 2))
        s = [F(0)] * len(v)
        self.assertFalse(slr.covers_sweep(v, s, F(1, 21))[0])
        self.assertFalse(slr.covers_endpoints(v, s, F(1, 21))[0])
        self.assertTrue(slr.covers_sweep(v, s, F(2, 41))[0])
        self.assertTrue(slr.covers_endpoints(v, s, F(2, 41))[0])

    def test_poliakova_n95_certificate(self):
        # Poliakova's Theorem 2 at its first case: N = 96 gives n = 95 runners covering
        # with delta = 1/97 (closed), hence open arcs of radius 2/193 > 1/97 cover, and
        # 2/193 < 1/96 = 1/(n+1).
        v, s, delta, n = rules.build_config(rules.POLIAKOVA_9_8, 96)
        self.assertEqual(n, 95)
        self.assertEqual(delta, F(1, 97))
        self.assertEqual(len(set(v)), n)
        R = F(2, 193)
        self.assertLess(R, F(1, n + 1))
        self.assertTrue(slr.covers_endpoints(v, s, R)[0])
        self.assertTrue(slr.covers_sweep(v, s, R)[0])

    def test_json_roundtrip(self):
        r = rules.POLIAKOVA_9_8_VARIANT
        back = rules.rule_from_json(rules.rule_to_json(r))
        self.assertEqual(rules.rule_to_json(back), rules.rule_to_json(r))


if __name__ == "__main__":
    unittest.main()
