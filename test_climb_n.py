# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Standard-library tests for route 18 (climb_n.py, PREREG_rules_n.md). Expected values are
worked out by hand in the comments."""
import os
import random
import tempfile
import time
import unittest
from fractions import Fraction as F

import climb_n as cn
import descent_k as dk
import polish_l as pl
import rule_search_s as rs


class TestRigid(unittest.TestCase):
    def test_cases(self):
        # route 17's critical cycles: 6 + 124 = 130 = 2 * 65, gcd 2: 260 % 130 == 0
        self.assertTrue(cn.rigid(6, 124, 64))
        # 6 + 184 = 190 = 2 * 95, gcd 2: 380 % 190 == 0
        self.assertTrue(cn.rigid(6, 184, 94))
        # at n = 63: 260 % (64 * 2) = 4
        self.assertFalse(cn.rigid(6, 124, 63))
        # the tight instance {1, 2} at 1/3: 6 % 3 == 0; at n = 4: 6 % 5 = 1
        self.assertTrue(cn.rigid(1, 2, 2))
        self.assertFalse(cn.rigid(1, 2, 4))
        # 12 % (6 * 2) == 0; 10 % 6 = 4
        self.assertTrue(cn.rigid(2, 4, 5))
        self.assertFalse(cn.rigid(2, 3, 5))
        # {1, 2, 3} at n = 3: only 1 + 3 = 4 is rigid (6 % 4 = 2, 8 % 4 = 0, 10 % 4 = 2)
        self.assertEqual(cn.rigid_pairs([1, 2, 3], 3), 1)

    def test_pair_sum_zero(self):
        # 124 * (k - k2) + 6 * (m2 - m) = -4 with k - k2 = -1, m2 - m = 20; over 24180:
        # 124 + 6 + 3900 - 4030 = 0
        self.assertEqual(cn.pair_sum(6, 124, F(1, 65), 0, 0, 20, 1), 0)
        # {1, 2} at 1/3: 1/3 - 1/3 + 2/3 - 2/3
        self.assertEqual(cn.pair_sum(1, 2, F(1, 3), 0, 1, 1, 1), 0)
        for k2 in range(-3, 4):
            for m2 in range(-40, 41):
                self.assertNotEqual(cn.pair_sum(6, 124, F(1, 64), 0, 0, m2, k2), 0)

    def test_lemma_exhaustive(self):
        # a zero sum exists iff the pair is rigid; a solution with |k2| <= a needs
        # |m2| <= b + 2 (a + b) / (n + 1) <= 8 + 16, so these ranges are enough
        for n in range(2, 9):
            R = F(1, n + 1)
            for a in range(1, 9):
                for b in range(a + 1, 9):
                    z = any(cn.pair_sum(a, b, R, 0, 0, m2, k2) == 0
                            for k2 in range(-a, a + 1) for m2 in range(-26, 27))
                    self.assertEqual(z, cn.rigid(a, b, n), (a, b, n))


class TestEvaluate(unittest.TestCase):
    def test_tight_pair(self):
        # {1, 2} at 1/3 with zero shifts: arcs (-1/3, 1/3), (1/3, 2/3), (2/3, 4/3) touch at
        # 1/3 and 2/3. Edges (1, 0): 0 and (0, 1): 0, so lambda = 0, cycle {1, 2}.
        ev = cn.evaluate([1, 2], [0.0, 0.0], F(1, 3))
        self.assertEqual(ev["lam"], 0)
        self.assertEqual(sorted(ev["cyc"]), [1, 2])
        self.assertFalse(ev["cover"])

    def test_one_runner_gap(self):
        # one runner at 2/5 leaves [2/5, 3/5]; bridged chain has the loop 2R - 1 = -1/5
        ev = cn.evaluate([1], [0.0], F(2, 5), tol=0.3)
        self.assertEqual(ev["lam"], F(-1, 5))
        self.assertFalse(ev["cover"])

    def test_no_chain_is_low(self):
        ev = cn.evaluate([1], [0.0], F(2, 5))
        self.assertEqual(ev["lam"], cn.LOW)

    def test_easy_cover(self):
        ev = cn.evaluate([1, 2, 3], [0.0, 0.0, 0.0], F(1, 3))
        self.assertTrue(ev["cover"])
        self.assertGreater(ev["lam"], 0)
        self.assertIsNotNone(dk.compact_k([1, 2, 3], ev["s_cover"], F(1, 3))[0])

    def test_callens(self):
        v, s = pl.c63_certified()
        ev = cn.evaluate(v, [float(x) for x in s], F(1, 64))
        self.assertTrue(ev["cover"])
        self.assertTrue(dk.certify_k(v, ev["s_cover"], 63)["ok"])


class TestClimb(unittest.TestCase):
    def test_climb_finds_easy_cover(self):
        res = cn.climb([1, 2, 3], [0.2, 0.5, 0.9], F(1, 3), 2, time.time() + 30,
                       random.Random(5), 6)
        self.assertIn(res["status"], ("COVER", "SEARCHCOVER"))
        self.assertEqual(len(set(res["v"])), 3)
        self.assertIsNotNone(dk.compact_k(res["v"], res["s"], F(1, 3))[0])

    def test_tier_short(self):
        d = tempfile.mkdtemp()
        st = cn.run_tier_n("kC62", time.time() + 40, random.Random(3), {},
                           os.path.join(d, "none-l"), os.path.join(d, "none-k"))
        self.assertIn(st["status"], ("UNKNOWN", "FOUND"))
        self.assertEqual(st["seed"], "init")
        self.assertEqual(len(st["v"]), 62)
        self.assertEqual(len(set(st["v"])), 62)
        self.assertIn("lam0", st)
        self.assertIsInstance(st["rp"], int)
        line = cn.line_n("kC62", st)
        self.assertTrue(line.startswith("kC62 n=62 st="))


class TestReport(unittest.TestCase):
    def test_r17_line(self):
        d = tempfile.mkdtemp()
        rs._save(os.path.join(d, "l_kC64.json"),
                 {"status": "UNKNOWN", "lam_best": "0", "cyc": [6, 124], "unc": 3.27e-9,
                  "polishes": 24})
        rs._save(os.path.join(d, "cal.json"),
                 {"c63raw_covers": True, "c63_lam": "+1e-05", "c63_cover": True,
                  "c63_cert": True, "up_w": 256, "up_m0": 1.2e-15, "up_lam": "0",
                  "up_cover": False, "up_cyc": [6, 124], "done": True})
        r17, cal = cn.r17_line(d)
        self.assertEqual(r17, "R17 kC64=UNK/0/6,124/3.3e-09/p24")
        self.assertIn("raw=True", cal)
        self.assertIn("uplam=0", cal)
        self.assertIn("upcyc=6,124", cal)
        r17, cal = cn.r17_line(os.path.join(d, "missing"))
        self.assertEqual((r17, cal), ("R17 none", "CAL17 none"))

    def test_line_n(self):
        st = {"n": 64, "status": "UNKNOWN", "seed": "l17", "rp": 40, "lam0": "0",
              "cyc0": [6, 124], "lam": "0", "cyc": [10, 120], "rig": 1, "ups": 0,
              "plateau": 3, "kicks": 2, "evals": 50, "unc": 3e-9, "seconds": 470, "turns": 1,
              "hist": []}
        line = cn.line_n("kC64", st)
        self.assertIn("cyc=10,120 rig=1", line)
        self.assertIn("pl=3", line)
        self.assertLess(len(line), 220)


if __name__ == "__main__":
    unittest.main()
