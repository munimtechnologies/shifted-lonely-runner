# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2). Made with AI agents working in MV2's name.
"""Tests for slr.py. Standard library only. Every expected value is proved by hand
in the comments (no published data is used here)."""
import random
import time
import unittest
from fractions import Fraction

import slr


def dist(x):
    x = x % 1
    return min(x, 1 - x)


def fmin(v, s, t):
    return min(dist(vi * t + si) for vi, si in zip(v, s))


class TestCheckers(unittest.TestCase):
    def both(self, v, s, R):
        a, wa = slr.covers_sweep(v, s, R)
        b, wb = slr.covers_endpoints(v, s, R)
        self.assertEqual(a, b, (v, s, R))
        for w in (wa, wb):
            if w is not None:  # a reported uncovered point must really be uncovered
                self.assertGreaterEqual(fmin(v, [Fraction(x) for x in s], Fraction(w)), Fraction(R))
        return a

    def test_two_runners(self):
        # v = (1, 2), s = 0: union is [0,R) u (1/2-R/2, 1/2+R/2) u (1-R, 1); it covers
        # iff R > 1/3 (1/3 is then a boundary point of two arcs).
        v, s = [1, 2], [0, 0]
        self.assertFalse(self.both(v, s, Fraction(1, 3)))
        self.assertTrue(self.both(v, s, Fraction(1, 3) + Fraction(1, 1000)))

    def test_unshifted_consecutive_is_tight(self):
        # (1..n), s = 0: t = 1/(n+1) has ||i t|| = min(i, n+1-i)/(n+1) >= 1/(n+1), so open arcs
        # of radius 1/(n+1) miss it; by Dirichlet every t has some q <= n with
        # ||q t|| <= 1/(n+1), so any larger radius covers.
        for n in range(3, 8):
            v = list(range(1, n + 1))
            s = [0] * n
            self.assertFalse(self.both(v, s, Fraction(1, n + 1)))
            self.assertTrue(self.both(v, s, Fraction(1, n + 1) + Fraction(1, 10000)))

    def test_random_agreement(self):
        rng = random.Random(20261124)
        for _ in range(250):
            n = rng.randint(2, 5)
            v = rng.sample(range(1, 13), n)
            s = [Fraction(rng.randint(0, 29), 30) for _ in range(n)]
            R = Fraction(rng.randint(80, 160), 100 * (n + 1))
            if R >= Fraction(1, 2):
                R = Fraction(49, 100)
            ok = self.both(v, s, R)
            if ok:  # spot-check: covered points really are within R of some runner
                for _ in range(40):
                    t = Fraction(rng.randint(0, 9999), 10000)
                    self.assertLess(fmin(v, s, t), R)

    def test_shift_invariance(self):
        # Replacing s_i by s_i + v_i * c (all i) is a time translation: same answer.
        v = [2, 3, 5, 7]
        s = [Fraction(1, 7), Fraction(2, 5), Fraction(0), Fraction(5, 11)]
        c = Fraction(3, 13)
        s2 = [(si + vi * c) % 1 for vi, si in zip(v, s)]
        for R in (Fraction(1, 6), Fraction(1, 5), Fraction(2, 9)):
            self.assertEqual(self.both(v, s, R), self.both(v, s2, R))


class TestSearch(unittest.TestCase):
    def test_quantize(self):
        self.assertEqual(slr.quantize([0.0, 0.5, 0.9999999999999999]), [0, 1 << 47, 0])

    def test_easy_cover_found_and_certified(self):
        # (1,2,3): radius 0.29 > 1/4 is coverable (s = 0 already covers by Dirichlet).
        rng = random.Random(7)
        v = [1, 2, 3]
        s, unc = slr.search_cover(v, 0.29, [rng.random() for _ in v], time.time() + 10, rng)
        self.assertEqual(unc, 0.0)
        sq = [Fraction(p, slr.Q) for p in slr.quantize(s)]
        ok, _ = slr.gamma_upper_ok(v, sq, Fraction(3, 10))
        self.assertTrue(ok)

    def test_cannot_beat_two_runner_optimum(self):
        # (1,2), radius 3/10: after a time shift s_1 = 0, [3/10, 7/10] (length 2/5) must be
        # covered by runner 2's two arcs of length 3/10 whose centres are 1/2 apart, whose
        # union has no connected piece longer than 3/10. So no shifts cover.
        rng = random.Random(3)
        v = [1, 2]
        s, unc = slr.search_cover(v, 0.3, [0.1, 0.7], time.time() + 1.0, rng)
        self.assertGreater(unc, 0.0)
        sq = [Fraction(p, slr.Q) for p in slr.quantize(s)]
        ok, _ = slr.gamma_upper_ok(v, sq, Fraction(3, 10))
        self.assertFalse(ok)

    def test_solve_levels_records_are_exact(self):
        rng = random.Random(11)
        v = [1, 2, 3]
        # levels e < 0 are allowed here only to get an easy radius 1/(4+e) > 1/4
        recs, status = slr.solve_levels(v, [Fraction(-1, 2)], 10, 1, rng)
        self.assertEqual(status, "certified")
        self.assertEqual(len(recs), 1)
        self.assertTrue(recs[0]["checkA"] and recs[0]["checkB"])
        self.assertEqual(recs[0]["R"], "2/7")


if __name__ == "__main__":
    unittest.main()
