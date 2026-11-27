# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Standard-library tests for route 15 (descent_j.py, PREREG_rules_j.md). No OR-Tools."""
import os
import random
import tempfile
import unittest
from fractions import Fraction as F

import descent_j as dj
import rule_search_g as rg
import rule_search_s as rs


def covers_one(v, S, Dg, t, R):
    x = (v * t + F(S, Dg)) % 1
    return min(x, 1 - x) < R


class TestCoverRes(unittest.TestCase):
    def test_matches_brute_force(self):
        rng = random.Random(15)
        for _ in range(60):
            v = rng.choice([1, 2, 3, 7, 27, 64, 128, 190])
            n1 = rng.choice([62, 63, 64, 65, 94, 95, 96])
            Dg = rng.choice([520, 1164, 97])
            t = F(rng.randrange(0, 10 ** 6), rng.randrange(1, 10 ** 6) + 1) % 1
            p, q = t.numerator, t.denominator
            brute = set(S for S in range(Dg) if rg.covered_int(v, S, p, q, Dg, n1))
            self.assertEqual(dj.cover_res(v, t, F(1, n1), Dg), brute, (v, n1, Dg, t))

    def test_boundary_is_open(self):
        # t = 0, v = 1: ||S/Dg|| < 1/65 with Dg = 520 means |S| < 8, so S = -7..7
        got = dj.cover_res(1, F(0), F(1, 65), 520)
        self.assertEqual(got, set(list(range(0, 8)) + list(range(513, 520))))


class TestSources(unittest.TestCase):
    def test_c63_shape(self):
        v, S, Dg = dj.c63()
        self.assertEqual(Dg, 520)
        self.assertEqual(len(v), 63)
        self.assertEqual(len(set(v)), 63)
        self.assertEqual(max(v), 128)
        self.assertTrue(all(0 <= x < 520 for x in S))
        for w in (4, 8, 32, 72, 96, 108):
            self.assertNotIn(w, v)
        self.assertEqual(sorted(w for w in v if w % 2), [1, 3, 9, 27, 81])

    def test_p95_is_poliakova_and_covers(self):
        v, S, Dg = dj.p95()
        self.assertEqual(Dg, 1164)
        self.assertEqual(len(v), 95)
        self.assertEqual(len(set(v)), 95)
        s = [F(x, Dg) for x in S]
        ok, x = dj.slr.covers_sweep(v, s, F(1, 96))
        self.assertTrue(ok, "uncovered %s" % (x,))


class TestModel(unittest.TestCase):
    def test_tiers(self):
        self.assertEqual(set(dj.ORDER_J), set(dj.TIERS_J))
        for tag, (src, n) in dj.TIERS_J.items():
            M = dj.model_of(tag)
            self.assertEqual(M["slack"], n - M["k"])
            self.assertEqual(M["R"], F(1, n + 1))
            if tag.startswith("s"):
                self.assertEqual(M["slack"], 0)
            else:
                self.assertIn(n, dj.OPEN, tag)
            have = set(M["v"])
            for a in M["adds"]:
                self.assertNotIn(a, have)
                self.assertTrue(rs.smooth(a, rg.P5))
            self.assertLessEqual(max(M["adds"]), (2 if n > M["k"] else 1) * max(M["v"]))
        self.assertEqual(dj.model_of("dC62")["k"], 63)
        self.assertEqual(dj.model_of("dP94")["k"], 95)
        self.assertNotIn(63, dj.OPEN)
        self.assertNotIn(57, dj.OPEN)

    def test_point_keys_exact_and_complete(self):
        M = dj.model_of("dC62")
        rng = random.Random(7)
        for _ in range(6):
            t = F(rng.randrange(1, 99991), 99991)
            keys = set(dj.point_keys(t, M))
            for i, (vi, Si) in enumerate(zip(M["v"], M["S"])):
                for j in range(-M["J"], M["J"] + 1):
                    want = covers_one(vi, (Si + j) % M["Dg"], M["Dg"], t, M["R"])
                    self.assertEqual("x:%d:%d" % (i, j) in keys, want, (t, i, j))
            for a in M["adds"]:
                for S in range(M["Dg"]):
                    want = covers_one(a, S, M["Dg"], t, M["R"])
                    self.assertEqual("y:%d:%d" % (a, S) in keys, want, (t, a, S))

    def test_hint_satisfies_points_of_a_true_cover(self):
        M = dj.model_of("sP95")
        hint = dj.hint_cand(M)
        lits = dj.lits_j(hint, M)
        self.assertEqual(len(lits), 95)
        rng = random.Random(3)
        for _ in range(12):
            t = F(rng.randrange(0, 77777), 77777)
            self.assertTrue(lits.intersection(dj.point_keys(t, M)), t)

    def test_config_round_trip(self):
        M = dj.model_of("dC62")
        v, s = dj.config_j(dj.hint_cand(M), M)
        self.assertEqual(v, M["v"])
        self.assertEqual(s, [F(x, 520) for x in M["S"]])
        cand = {"del": [0], "j": {1: -3}, "add": {5: 7}}
        v2, s2 = dj.config_j(cand, M)
        self.assertEqual(len(v2), 63)
        self.assertEqual(v2[0], M["v"][1])
        self.assertEqual(s2[0], F((M["S"][1] - 3) % 520, 520))
        self.assertEqual((v2[-1], s2[-1]), (5, F(7, 520)))
        self.assertIn("x:1:-3", dj.lits_j(cand, M))
        self.assertIn("y:5:7", dj.lits_j(cand, M))
        self.assertNotIn("x:0:0", dj.lits_j(cand, M))

    def test_certify_pads_and_refuses(self):
        c = dj.certify_j([2, 4], [F(0), F(0)], 5)
        self.assertEqual(c["n"], 5)
        self.assertTrue(c["distinct"])
        self.assertFalse(c["ok"])

    def test_scan_of_a_true_cover_has_no_gap(self):
        M = dj.model_of("sP95")
        pts, diag = dj.scan_j(M)
        self.assertEqual(diag["kind"], "self")
        self.assertLess(diag["min"], 1e-9)  # float gaps can only be rounding slivers
        self.assertEqual(pts, [])  # and no exact uncovered point comes out of them


class TestReport(unittest.TestCase):
    def test_lines(self):
        r = {"n": 62, "k": 63, "status": "UNKNOWN", "iterations_total": 2, "n_clauses": 9,
             "tl": 45.0, "seconds_total": 3.2, "turns": 1,
             "diag": {"kind": "del1", "min": 0.0123, "gaps": 4, "at": 126, "zero": []}}
        line = dj.line_j("dC62", r)
        self.assertIn("st=UNKNOWN", line)
        self.assertIn("del1=0.0123/4g@126", line)
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(dj.r14_line(os.path.join(d, "missing")), "R14 none")
            rs._save(os.path.join(d, "t_e6N72.json"),
                     {"status": "UNKNOWN", "iterations_total": 9, "n_clauses": 1500})
            self.assertEqual(dj.r14_line(d), "R14 e6N72=UNK/9/1500")


if __name__ == "__main__":
    unittest.main()
