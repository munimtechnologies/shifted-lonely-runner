# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Tests for slr_br.py (standard library only). Run: python -m unittest -v test_slr_br"""
import random
import unittest
from fractions import Fraction as F

import slr_br


class ExactChecker(unittest.TestCase):
    def test_a_dirichlet_tight(self):
        # Speeds 1..n with zero shifts: by Dirichlet every t has some k <= n with
        # ||k t|| <= 1/(n+1), and t = 1/(n+1) has ||k t|| >= 1/(n+1) for all k <= n.
        for n in range(1, 14):
            sp = list(range(1, n + 1))
            z = [F(0)] * n
            self.assertTrue(slr_br.exact_cover(sp, z, F(1, n + 1)), n)
            self.assertFalse(slr_br.exact_cover(sp, z, F(1, n + 1) - F(1, 10 ** 6)), n)

    def test_b_single_runner(self):
        # One runner covers the circle iff r >= 1/2, whatever its speed or shift.
        for v in (1, 2, 5):
            for s in (F(0), F(1, 3), F(7, 10)):
                self.assertTrue(slr_br.exact_cover([v], [s], F(1, 2)))
                self.assertFalse(slr_br.exact_cover([v], [s], F(49, 100)))

    def test_c_float_matches_exact(self):
        rng = random.Random(7)
        for _ in range(300):
            n = rng.randint(2, 6)
            sp = rng.sample(range(1, 13), n)
            sh = [rng.random() for _ in range(n)]
            r = 0.05 + 0.25 * rng.random()
            fl = not slr_br.total_gaps(sp, sh, r)
            ex = slr_br.exact_cover(sp, [F(x) for x in sh], F(r))
            self.assertEqual(fl, ex, (sp, sh, r))

    def test_d_best_shift_is_optimal_on_grid(self):
        # The exact best response must be at least as good as any shift on a fine grid.
        rng = random.Random(11)
        for _ in range(40):
            v = rng.randint(1, 9)
            pts = sorted(rng.random() for _ in range(6))
            gaps = [(pts[0], pts[1]), (pts[2], pts[3]), (pts[4], pts[5])]
            r = 0.03 + 0.1 * rng.random()
            s, cov = slr_br.best_shift(v, gaps, r, rng)

            def covered(shift):
                iv = []
                slr_br.float_intervals(v, shift, r, iv)
                tot = 0.0
                for a, b in gaps:
                    for c, d in iv:
                        lo, hi = max(a, c), min(b, d)
                        if hi > lo:
                            tot += hi - lo
                return tot

            self.assertAlmostEqual(covered(s), cov, places=9)
            for i in range(400):
                self.assertLessEqual(covered(i / 400.0), cov + 1e-9)


class KnownCounterexample(unittest.TestCase):
    def test_e_n8_known(self):
        # Blanco-Criado-Santos: gamma_sh(1..8) = 1/10 < 1/9, so a cover at radius just below 1/9
        # exists. Sanity check of the search on a case known to be a counterexample.
        cert, st = slr_br.certify_consecutive(8, seed=1, max_sweeps=6000, seconds=60)
        print("n=8", st, flush=True)
        self.assertIsNotNone(cert, "n=8 search failed: %r" % (st,))
        self.assertTrue(slr_br.exact_cover(cert["speeds"], [F(x) for x in cert["shifts"]],
                                           F(cert["radius"])))
        self.assertLess(F(cert["radius"]), F(1, 9))


if __name__ == "__main__":
    unittest.main()
