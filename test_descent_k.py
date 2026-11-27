# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Standard-library tests for route 16 (descent_k.py, PREREG_rules_k.md)."""
import os
import random
import tempfile
import time
import unittest
from fractions import Fraction as F

import descent_j as dj
import descent_k as dk
import rule_search_s as rs
import slr


class TestTiers(unittest.TestCase):
    def test_targets_are_open(self):
        self.assertEqual(set(dk.ORDER_K), set(dk.TIERS_K))
        for tag, (src, n, mode) in dk.TIERS_K.items():
            if tag.startswith("k"):
                self.assertIn(n, dj.OPEN, tag)
            else:
                self.assertNotIn(n, dj.OPEN, tag)  # calibration: a known cover exists

    def test_sources(self):
        v, s = dk.source("C")
        self.assertEqual(len(v), 63)
        self.assertEqual(len(set(v)), 63)
        self.assertTrue(all(0.0 <= x < 1.0 for x in s))
        # route 15's sanity tier sC63 certified a cover at 1/64 on exactly these 63 speeds
        # (shifts within 4/520 of these), so the calibration tier cC63 has a cover to find
        v, s = dk.source("P")
        self.assertEqual(len(v), 95)
        self.assertLess(dk.measure(v, s, 1.0 / 96), 1e-9)


class TestInit(unittest.TestCase):
    def test_down_c62(self):
        v, s, st = dk.init_down("C", 62)
        self.assertEqual(len(v), 62)
        self.assertEqual(len(set(v)), 62)
        self.assertEqual(len(st["del"]), 1)
        self.assertNotIn(st["del"][0], v)
        self.assertGreaterEqual(st["m0"], 0.0)
        self.assertAlmostEqual(st["m0"], dk.measure(v, s, 1.0 / 63), places=12)
        # greedy: no other single deletion leaves less
        v0, s0 = dk.source("C")
        for i in range(0, 63, 9):
            m = dk.measure(v0[:i] + v0[i + 1:], s0[:i] + s0[i + 1:], 1.0 / 63)
            self.assertGreaterEqual(m, st["m0"] - 1e-15)

    def test_down_c61_deletes_two(self):
        v, s, st = dk.init_down("C", 61)
        self.assertEqual(len(v), 61)
        self.assertEqual(len(st["del"]), 2)
        self.assertLessEqual(st["m1"], st["m0"] + 1e-15)

    def test_up_c64(self):
        v, s, st = dk.init_up("C", 64, random.Random(1))
        self.assertEqual(len(v), 64)
        self.assertEqual(len(set(v)), 64)
        self.assertLessEqual(st["m0"], st["m_src"] + 1e-15)
        self.assertLessEqual(st["add"], 256)
        self.assertAlmostEqual(st["m0"], dk.measure(v, s, 1.0 / 65), places=9)


class TestSearch(unittest.TestCase):
    def test_finds_easy_cover_and_checks_it(self):
        # speeds 1, 2, 3 at radius 1/3 are covered with all shifts 0 (t near 1/3: ||3t|| < 1/3)
        rng = random.Random(5)
        res = dk.search_k([1, 2, 3], [0.37, 0.11, 0.73], F(1, 3), time.time() + 20, rng, 6)
        self.assertEqual(res["status"], "COVER")
        self.assertTrue(dk.exact_ok(res["v"], res["s"], F(1, 3)))
        self.assertEqual(len(set(res["v"])), 3)

    def test_no_false_cover(self):
        # the shifted conjecture holds for 3 runners: no cover at radius 1/4
        rng = random.Random(6)
        res = dk.search_k([1, 2, 3], [0.2, 0.5, 0.9], F(1, 4), time.time() + 2, rng, 6)
        self.assertEqual(res["status"], "NONE")
        self.assertGreater(res["best_unc"], 0.0)
        self.assertGreater(res["sweeps"], 0)

    def test_swap_keeps_speeds_distinct_and_improves(self):
        v, s, _st = dk.init_down("C", 62)
        r = (1.0 / 63) * (1 - dk.SHRINK)
        arcs = dk.arcs_of(v, s, r)
        unc = slr._unc_measure(arcs)
        rng = random.Random(9)
        for _ in range(3):
            if dk.try_swap(v, s, arcs, r, rng, 256, unc):
                new = slr._unc_measure(arcs)
                self.assertLess(new, unc)
                unc = new
            self.assertEqual(len(set(v)), len(v))
            self.assertEqual(len(v), 62)
            self.assertLessEqual(max(v), 256)

    def test_run_tier_resumes(self):
        rng = random.Random(2)
        st = dk.run_tier_k("kC62", time.time() + 3, rng)
        self.assertEqual(st["turns"], 1)
        self.assertEqual(len(st["v"]), 62)
        self.assertIn(st["status"], ("UNKNOWN", "FOUND"))
        st2 = dk.run_tier_k("kC62", time.time() + 2, rng, st)
        self.assertEqual(st2["turns"], 2)
        self.assertLessEqual(st2["best_unc"], st["best_unc"])
        self.assertEqual(len(st2["hist"]), 2)


class TestCertify(unittest.TestCase):
    def test_compact_and_certify_poliakova(self):
        v, s = dk.source("P")
        D, S = dk.compact_k(v, s, F(1, 96))
        self.assertIsNotNone(D)
        self.assertTrue(slr.covers_sweep(v, [F(a, D) for a in S], F(1, 96))[0])
        c = dk.certify_k(v, s, 95)
        self.assertTrue(c["ok"])
        self.assertEqual(c["pad"], 0)
        self.assertTrue(c["sweep"] and c["endpoints"])

    def test_certify_refuses_non_cover(self):
        c = dk.certify_k([1, 2, 3], [0.2, 0.5, 0.9], 3)
        self.assertFalse(c["ok"])


class TestReport(unittest.TestCase):
    def test_lines(self):
        st = {"n": 62, "status": "UNKNOWN", "best_unc": 1.5e-5, "gaps": 7, "sweeps": 10,
              "swaps": 2, "kicks": 3, "rejected": 0, "seconds": 12.3, "turns": 1,
              "start": {"del": [124], "m0": 3e-4, "m1": 3e-4}, "hist": [2e-5, 1.5e-5]}
        line = dk.line_k("kC62", st)
        self.assertIn("st=UNKNOWN", line)
        self.assertIn("del=124", line)
        self.assertIn("h=2e-05>1.5e-05", line)
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(dk.r15_line(d), "R15 none")
            rs._save(os.path.join(d, "t_dC62.json"), {"status": "UNKNOWN",
                     "iterations_total": 9, "n_clauses": 99,
                     "diag": {"min": 0.0021, "at": 124}})
            self.assertEqual(dk.r15_line(d), "R15 dC62=UNK/9/99/0.0021@124")
        c = {"cert": {"n": 62, "ok": True, "sweep": True, "endpoints": True, "pad": 0,
                      "D": 520, "v0": [2, 6], "S": [0, 5]}}
        self.assertIn("open=True", dk.rule_line("kC62", c))
        self.assertIn("v=2,6 S=0,5", dk.rule_line("kC62", c))


if __name__ == "__main__":
    unittest.main()
