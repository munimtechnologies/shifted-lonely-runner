# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Tests for slr_lp.py (standard library only). PREREG_lp.md, prediction L1."""
import random
import unittest
from fractions import Fraction as F

import slr_br
import slr_lp


class Holes(unittest.TestCase):
    def test_single_runner(self):
        # speed 1, shift 0, r = 1/4: the arc is [-1/4, 1/4], the gap (1/4, 3/4), peak 1/2
        hl = slr_lp.holes([1], [0.0], 0.25)
        self.assertEqual(len(hl), 1)
        a, b, L, R = hl[0]
        self.assertAlmostEqual(b - a, 0.5, places=12)
        self.assertEqual((L, R), (0, 0))
        hh = slr_lp.hole_heights([1], hl, 0.25)
        self.assertAlmostEqual(hh[0][2], 0.5, places=12)

    def test_gap_measure_matches_slr_br(self):
        rng = random.Random(3)
        for _ in range(30):
            n = rng.randint(2, 9)
            sp = rng.sample(range(1, 30), n)
            sh = [rng.random() for _ in range(n)]
            r = rng.uniform(0.02, 0.2)
            m1 = sum(b - a for a, b, _, _ in slr_lp.holes(sp, sh, r))
            m2 = sum(b - a for a, b in slr_br.total_gaps(sp, sh, r))
            self.assertAlmostEqual(m1, m2, places=9)

    def test_hole_estimate_is_upper_bound(self):
        rng = random.Random(5)
        for _ in range(20):
            n = rng.randint(3, 8)
            sp = rng.sample(range(1, 25), n)
            sh = [rng.random() for _ in range(n)]
            g = slr_lp.gamma(sp, sh)
            r = g * 0.97
            hh = slr_lp.hole_heights(sp, slr_lp.holes(sp, sh, r), r)
            self.assertGreaterEqual(max(h for _, _, h, _ in hh), g - 1e-12)


class Gamma(unittest.TestCase):
    def test_consecutive_speeds_are_tight(self):
        for n in range(3, 12):
            sp = list(range(1, n + 1))
            g = slr_lp.gamma(sp, [0.0] * n)
            self.assertAlmostEqual(g, 1.0 / (n + 1), places=12)

    def test_gamma_against_exact_cover(self):
        rng = random.Random(7)
        for _ in range(10):
            n = rng.randint(3, 7)
            sp = rng.sample(range(1, 20), n)
            sh = [rng.random() for _ in range(n)]
            g = slr_lp.gamma(sp, sh)
            ex = [F(s) for s in sh]
            self.assertTrue(slr_br.exact_cover(sp, ex, F(g * (1 + 1e-9))))
            self.assertFalse(slr_br.exact_cover(sp, ex, F(g * (1 - 1e-9))))


class DifferenceConstraints(unittest.TestCase):
    def test_min_z_two_variables(self):
        # x1 - x0 <= (z - 1)/1, |x| <= 1  =>  smallest z is -1 (x1 = -1, x0 = 1)
        x, z = slr_lp.min_z(2, [(0, 1, 1.0, 1.0)], [1.0, 1.0], -5.0, 1.0, iters=80)
        self.assertAlmostEqual(z, -1.0, places=9)
        self.assertLessEqual(x[1] - x[0], z - 1.0 + 1e-9)
        self.assertTrue(all(abs(t) <= 1.0 + 1e-12 for t in x))

    def test_infeasible_cycle(self):
        # x1 - x0 <= -1 and x0 - x1 <= -1 is infeasible
        cons = [(0, 1, 1.0, 1.0), (1, 0, 1.0, 1.0)]
        self.assertIsNone(slr_lp.feasible(2, cons, [5.0, 5.0], 0.0))


class Polish(unittest.TestCase):
    def test_polish_never_increases_and_is_exact(self):
        rng = random.Random(11)
        improved = 0
        for trial in range(4):
            n = 7
            sp = list(range(1, n + 1))
            sh = [rng.random() for _ in range(n)]
            g1 = slr_lp.gamma(sp, sh)
            sh2, g2, st = slr_lp.slp_polish(sp, sh, g=g1, seconds=6)
            self.assertLessEqual(g2, g1)
            if g2 < g1 * (1 - 1e-6):
                improved += 1
            ex = [F(s) for s in sh2]
            self.assertTrue(slr_br.exact_cover(sp, ex, F(g2 * (1 + 1e-9))))
            self.assertFalse(slr_br.exact_cover(sp, ex, F(g2 * (1 - 1e-9))))
        self.assertGreaterEqual(improved, 2)

    def test_worker_small(self):
        # 5 runners warm-started from 4: the worker returns a consistent configuration
        sp = [1, 2, 3, 4]
        sh = [0.1, 0.4, 0.7, 0.2]
        res = slr_lp.worker({"n": 5, "base_speeds": sp, "base_shifts": sh, "add": None,
                             "seed": 1, "seconds": 8, "vmax": 12, "pool": None})
        self.assertEqual(len(res["speeds"]), 5)
        self.assertEqual(len(set(res["speeds"])), 5)
        self.assertAlmostEqual(slr_lp.gamma(res["speeds"], res["shifts"]), res["gamma"],
                               places=12)
        self.assertLessEqual(res["E2"], 4.0)  # E_n <= n - 1 (Poliakova)


if __name__ == "__main__":
    unittest.main()
