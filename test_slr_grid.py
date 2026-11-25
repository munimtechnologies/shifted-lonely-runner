# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Tests for route 8 (slr_grid.py). Standard library only; under a minute."""
import json
import os
import random
import time
import unittest
from fractions import Fraction as F

import slr_chain
import slr_grid as S

HERE = os.path.dirname(os.path.abspath(__file__))


def dist(x):
    """||x||, exact for Fractions."""
    x = x - (x.numerator // x.denominator)
    return min(x, 1 - x)


class Masks(unittest.TestCase):
    def test_base_mask_matches_definition(self):
        G = 3000
        r = F(1, 25)
        for v in (1, 7, 13):
            M = S.base_mask(v, 1 / 25, G)
            for c in range(G):
                want = dist(F(v * (2 * c + 1), 2 * G)) < r
                self.assertEqual(bool((M >> c) & 1), want, (v, c))

    def test_rotation_is_the_shift(self):
        G = 3000
        r = F(1, 25)
        g = S.Grid(G, 1 / 25)
        for v in (3, 11):
            for k in (0, 1, 457, G - 1):
                M = g.mask(v, k)
                s = S.to_shift(v, k, G)
                for c in range(0, G, 7):
                    want = dist(F(v * (2 * c + 1), 2 * G) + s) < r
                    self.assertEqual(bool((M >> c) & 1), want, (v, k, c))

    def test_to_off_inverts_to_shift(self):
        G = 1 << 20
        rng = random.Random(5)
        for _ in range(50):
            v = rng.randint(1, 240)
            s = rng.random()
            k = S.to_off(v, s, G)
            back = float(S.to_shift(v, k, G))
            err = min(abs(back - s), 1 - abs(back - s))
            self.assertLessEqual(err, v / G)


class Counts(unittest.TestCase):
    def test_counts_trial_commit(self):
        G = 1500
        rng = random.Random(1)
        g = S.Grid(G, 0.06)
        sp = [1, 2, 3, 5, 8, 9]
        offs = [rng.randrange(G) for _ in sp]
        cov = S.Cover(g, sp, offs)
        U, one = cov.count_naive()
        self.assertEqual(cov.U, U)
        self.assertEqual(cov.ONE, one)
        for _ in range(40):
            i = rng.randrange(len(sp))
            u = rng.choice([cov.sp[i], 4, 6, 7, 10, 11])
            if u in cov.sp and u != cov.sp[i]:
                continue
            k = rng.randrange(G)
            Mn = g.mask(u, k)
            want = cov.trial(i, Mn)
            cov.commit(i, u, k, Mn)
            self.assertEqual(cov.U, want)
            U, one = cov.count_naive()
            self.assertEqual(cov.U, U)
            self.assertEqual(cov.ONE, one)
            unc = cov.rand_unc(rng)
            if cov.U:
                self.assertFalse((cov.C >> unc) & 1)
            else:
                self.assertIsNone(unc)

    def test_anneal_loop_consistent_and_never_worse(self):
        G = 2048
        rng = random.Random(2)
        g = S.Grid(G, 0.11)
        sp = [1, 2, 3, 4, 5]
        cov = S.Cover(g, sp, [rng.randrange(G) for _ in sp])
        U0 = cov.U
        st = S.anneal_loop(cov, rng, time.time() + 60, vmax=12, iters=3000,
                           on_zero=lambda c: True)
        self.assertLessEqual(cov.U, U0)
        self.assertEqual(st["U"], cov.U)
        U, one = cov.count_naive()
        self.assertEqual(cov.U, U)
        self.assertEqual(len(set(cov.sp)), 5)
        self.assertTrue(all(1 <= v <= 12 for v in cov.sp))


class Certificate55(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(HERE, "certs_lp.json"), encoding="utf-8") as fh:
            c = [x for x in json.load(fh) if x["n"] == 55][0]
        cls.v = c["speeds"]
        cls.s = [k / c["shift_den"] for k in c["shift_num"]]

    def test_grid_sees_cover_and_hole(self):
        G = 1 << 20
        offs = [S.to_off(v, s, G) for v, s in zip(self.v, self.s)]
        self.assertEqual(S.Cover(S.Grid(G, 1 / 54), self.v, offs).U, 0)
        self.assertGreater(S.Cover(S.Grid(G, 1 / 60), self.v, offs).U, 0)

    def test_finish_certifies_the_known_counterexample(self):
        cert, E, _ = S.finish(self.v, self.s, polish_s=0)
        self.assertIsNotNone(cert)
        self.assertEqual(cert["n"], 55)
        self.assertGreater(E, 0.1)
        self.assertTrue(slr_chain.exact_ok(cert, full=True))

    def test_finish_refuses_a_non_counterexample(self):
        # speeds 1 and 3 at shift 0: at t = 1/2 both are 1/2 from the start, so gamma = 1/2
        cert, E, _ = S.finish([1, 3], [0.0, 0.0], polish_s=0)
        self.assertIsNone(cert)
        self.assertLess(E, 0)


class Worker(unittest.TestCase):
    def test_worker_runs_and_any_cert_is_exact(self):
        r = S.worker({"n": 7, "base_speeds": [1, 2, 3, 4, 5, 6], "base_shifts": [0.0] * 6,
                      "rank": 0, "seed": 3, "seconds": 8, "G": 1 << 14, "e_g": 0.2,
                      "vmax": 20, "reserve": 4})
        self.assertEqual(len(r["speeds"]), 7)
        self.assertEqual(len(set(r["speeds"])), 7)
        if r["cert"] is not None:
            self.assertTrue(slr_chain.exact_ok(r["cert"], full=True))


if __name__ == "__main__":
    unittest.main()
