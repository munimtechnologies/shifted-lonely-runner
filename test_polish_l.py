# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Standard-library tests for route 17 (polish_l.py, PREREG_rules_l.md). Expected values are
worked out by hand in the comments."""
import random
import time
import unittest
from fractions import Fraction as F

import descent_j as dj
import descent_k as dk
import polish_l as pl
import slr


class TestKarp(unittest.TestCase):
    def test_small_graph(self):
        # cycles: 0<->1 mean (2+4)/2 = 3; 1<->2 mean (1+1)/2 = 1; loop at 2 mean 3/2
        edges = {(0, 1): F(2), (1, 0): F(4), (1, 2): F(1), (2, 1): F(1), (2, 2): F(3, 2)}
        lam, cyc, cm = pl.karp([0, 1, 2], edges)
        self.assertEqual(lam, 1)
        self.assertEqual(cm, 1)
        self.assertEqual(set(cyc), {1, 2})

    def test_negative_loop(self):
        lam, _cyc, _cm = pl.karp([0, 1], {(0, 1): F(1), (1, 0): F(1), (1, 1): F(-1)})
        self.assertEqual(lam, -1)

    def test_fraction_weights(self):
        # 2-cycle with weights 1/3 and 1/6: mean 1/4; loop at 0 of 1/2
        lam, _c, _m = pl.karp(["a", "b"], {("a", "b"): F(1, 3), ("b", "a"): F(1, 6),
                                           ("a", "a"): F(1, 2)})
        self.assertEqual(lam, F(1, 4))


class TestGaps(unittest.TestCase):
    def test_one_runner(self):
        # ||t|| < 1/3 leaves [1/3, 2/3]
        self.assertEqual(pl.exact_gaps([1], [0], F(1, 3)), [(F(1, 3), F(2, 3))])

    def test_touching_point(self):
        # runner 1: (-1/4, 1/4); runner 2 with s = 1/4: ||2t + 1/4|| < 1/4 gives (1/4, 1/2) and
        # (3/4, 1). The arcs meet at 1/4, which stays uncovered; [1/2, 3/4] too.
        g = pl.exact_gaps([1, 2], [0, F(1, 4)], F(1, 4))
        self.assertEqual(g, [(F(1, 4), F(1, 4)), (F(1, 2), F(3, 4))])

    def test_cover_has_no_gaps(self):
        self.assertEqual(pl.exact_gaps([1, 2, 3], [0, 0, 0], F(1, 3)), [])
        # route 15's certified neighbour of Callens's cover (sanity tier sC63, both checkers)
        v, s = pl.c63_certified()
        self.assertTrue(slr.covers_sweep(v, s, F(1, 64))[0])
        self.assertEqual(pl.exact_gaps(v, s, F(1, 64)), [])

    def test_certified_c63_shape(self):
        v, s = pl.c63_certified()
        v0, S0, D = dj.c63()
        self.assertEqual(v, list(v0))
        moved = [w for w, x, a in zip(v, s, S0) if x != F(a, D)]
        self.assertEqual(sorted(moved), [1, 81, 104, 120])

    def test_callens_at_65_matches_float(self):
        v, s = pl.c63_certified()
        g = pl.exact_gaps(v, s, F(1, 65))
        self.assertGreater(len(g), 0)
        meas = float(sum(b - a for a, b in g))
        self.assertAlmostEqual(meas, dk.measure(v, [float(x) for x in s], 1.0 / 65), places=11)
        for a, b in g:
            self.assertLessEqual(a, b)
        ok, x = slr.covers_sweep(v, s, F(1, 65))
        self.assertFalse(ok)
        self.assertTrue(any(a <= x % 1 <= b or a <= x % 1 + 1 <= b for a, b in g))


class TestAddOne(unittest.TestCase):
    def test_two_speeds_work(self):
        # gap [2/5, 3/5] of length 1/5 at R = 2/5. Speed w needs h = 2/5 - w/10 > 0: w <= 3.
        # w = 2, s = 1/10 and w = 3, s = 1/2 cover it (checked by hand at 2/5, 1/2, 3/5).
        out = pl.add_one_exact([1], [0], F(2, 5), focus=())
        self.assertEqual(out["W"], 3)
        self.assertTrue(out["complete"])
        self.assertEqual([d["w"] for d in out["feasible"]], [2, 3])
        for d in out["feasible"]:
            self.assertTrue(d["sweep"] and d["endpoints"])
        self.assertEqual(out["feasible"][0]["s"], "1/10")
        self.assertEqual(out["feasible"][1]["s"], "1/2")

    def test_exact_length_is_not_enough(self):
        # gap [1/3, 2/3] at R = 1/3: w = 2 has arcs of length exactly 1/3 (h = 0): no cover
        out = pl.add_one_exact([1], [0], F(1, 3), focus=(2,))
        self.assertEqual(out["W"], 1)
        self.assertEqual(out["feasible"], [])
        self.assertTrue(out["complete"])
        self.assertEqual(out["focus"][2]["hmin"], 0.0)
        self.assertFalse(out["focus"][2]["exact"])

    def test_exact_point(self):
        self.assertEqual(pl._exact_point([(F(4, 5), F(2, 5))]), F(1, 10))
        self.assertEqual(pl._exact_point([(F(2, 5), F(1, 5))]), F(1, 2))
        self.assertIsNone(pl._exact_point([(F(0), F(1, 4)), (F(1, 2), F(1, 4))]))
        # (0.1, 0.5) and (0.4, 0.9) share (0.4, 0.5)
        self.assertEqual(pl._exact_point([(F(1, 10), F(2, 5)), (F(2, 5), F(1, 2))]), F(9, 20))


class TestChainPolish(unittest.TestCase):
    def test_easy_cover(self):
        ch, why = pl.chain_of([1, 2, 3], [0, 0, 0], F(1, 3))
        self.assertIsNone(why)
        self.assertGreaterEqual(len(ch), 3)
        p = pl.polish([1, 2, 3], [0, 0, 0], F(1, 3))
        self.assertGreater(p["lam"], 0)
        self.assertTrue(p["cover"])

    def test_three_runners_never_cover_at_quarter(self):
        # the shifted conjecture holds for 3 runners (Cslovjecsek, Malikiosis, Naszodi,
        # Schymura), so no chain at radius 1/4 can have a positive margin
        for shifts in ([0.2, 0.5, 0.9], [0.0, 0.0, 0.0], [0.13, 0.71, 0.4]):
            p = pl.polish([1, 2, 3], shifts, F(1, 4), tol=0.5)
            self.assertIsNotNone(p["lam"], shifts)
            self.assertLessEqual(p["lam"], 0, shifts)
            self.assertFalse(p["cover"])

    def test_callens_calibration(self):
        v, s = pl.c63_certified()
        p = pl.polish(v, s, F(1, 64))
        self.assertGreater(p["lam"], 0)
        self.assertTrue(p["cover"])
        c = dk.certify_k(v, p["s_new"], 63)
        self.assertTrue(c["ok"])


class TestTier(unittest.TestCase):
    def test_run_tier_short(self):
        st = pl.run_tier_l("kC62", time.time() + 30, random.Random(3), {}, {})
        self.assertGreaterEqual(st["polishes"], 1)
        self.assertIn(st["status"], ("UNKNOWN", "FOUND"))
        self.assertEqual(len(st["v"]), 62)
        self.assertEqual(len(set(st["v"])), 62)
        self.assertEqual(st["seed"], "init")
        self.assertIn("lam0", st)


class TestReport(unittest.TestCase):
    def test_lines(self):
        a = {"G": 40, "npts": 3, "meas": 5.86e-4, "Lmax": 2e-5, "W": 1500, "done": 1500,
             "complete": True, "feasible": [], "tight": [256], "top": [[40, 256], [39, 128]],
             "focus": {"256": {"cnt": 40, "hmin": 0.0, "exact": False}}}
        line = pl.a_line(a)
        self.assertIn("complete=True", line)
        self.assertIn("tight=256", line)
        self.assertIn("w256=40/40", line)
        st = {"n": 62, "status": "UNKNOWN", "seed": "k16", "lam0": "0", "chain0": 900,
              "lam_best": "-1e-09", "lam_last": "-2e-09", "chain": 910, "cyc": [2, 6],
              "polishes": 4, "slices": 3, "unc": 1e-9, "sweeps": 9, "swaps": 1,
              "seconds": 400, "turns": 1}
        line = pl.line_l("kC62", st)
        self.assertIn("lam0=0", line)
        self.assertIn("cyc=2,6", line)
        self.assertEqual(pl.lam_txt(F(0)), "0")
        self.assertEqual(pl.lam_txt(None), "none")
        self.assertEqual(pl.lam_txt(F(1, 4)), "+0.25")


if __name__ == "__main__":
    unittest.main()
