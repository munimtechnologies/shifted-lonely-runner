# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Exact re-check of cover_n063_simple.json, a 63-runner shifted Lonely Runner counterexample
(n = 63 was first settled by Xavier Callens, Zenodo 24051700; this is a smaller second cover).

Four checks: a fresh Fraction endpoint checker written in this file, both exact checkers of
slr.py, and top_o.fixed_check (the fixed-N closed-cover criterion at N = 64). Also: the file's
explicit speeds and shifts are exactly the configuration of top_q.SIMPLE_63 on 2, 4, ..., 128."""
import json
import os
import unittest
from fractions import Fraction as F

import rules_m
import slr
import top_o as to
import top_q as tq

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    with open(os.path.join(HERE, "cover_n063_simple.json"), encoding="utf-8") as f:
        d = json.load(f)
    v = [int(x) for x in d["speeds"]]
    nz = {int(k): F(x) for k, x in d["nonzero_shifts"].items()}
    s = [nz.get(w, F(0)) for w in v]
    return d, v, s


def dist(x):
    x = x % 1
    return min(x, 1 - x)


def fresh_cover(v, s, R):
    """Open arcs cover iff every arc endpoint lies strictly inside another runner's arc (an
    uncovered set would be closed with a boundary point, which is an endpoint). Fractions."""
    for i, (vi, si) in enumerate(zip(v, s)):
        for j in range(vi):
            for e in (R, -R):
                t = (j + e - si) / vi
                if not any(dist(vl * t + sl) < R for l, (vl, sl) in enumerate(zip(v, s))
                           if l != i):
                    return False, t % 1
    return True, None


class TestFresh(unittest.TestCase):
    def test_fresh_hand(self):
        # (-1/3, 1/3) and (1/6, 5/6) cover; (-1/4, 1/4) and (1/4, 3/4) miss 1/4
        self.assertTrue(fresh_cover([1, 1], [F(0), F(1, 2)], F(1, 3))[0])
        self.assertFalse(fresh_cover([1, 1], [F(0), F(1, 2)], F(1, 4))[0])


class TestCover63(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d, cls.v, cls.s = load()
        cls.R = F(cls.d["R"])

    def test_shape(self):
        self.assertEqual(self.R, F(1, 64))
        self.assertEqual(len(self.v), 63)
        self.assertEqual(len(set(self.v)), 63)
        want = (set(range(2, 129, 2)) - {8, 32, 96}) | {3, 9}
        self.assertEqual(set(self.v), want)

    def test_same_as_rule(self):
        # 12: 1/2 + 1/130 = 33/65; 16: -3/130 = 127/130; 64: -1/65 = 64/65; 128: 1/65
        v, s, delta, k = rules_m.build_config(tq.SIMPLE_63, 64)
        self.assertEqual(delta, F(1, 65))
        self.assertEqual(k, 63)
        self.assertEqual(v, self.v)
        self.assertEqual([x % 1 for x in s], [x % 1 for x in self.s])
        self.assertEqual(rules_m.rule_from_json(self.d["rule"]),
                         rules_m.rule_from_json(rules_m.rule_to_json(tq.SIMPLE_63)))

    def test_fresh_checker(self):
        ok, x = fresh_cover(self.v, self.s, self.R)
        self.assertTrue(ok, x)

    def test_slr_checkers(self):
        a, xa = slr.covers_sweep(self.v, self.s, self.R)
        b, xb = slr.covers_endpoints(self.v, self.s, self.R)
        self.assertTrue(a, xa)
        self.assertTrue(b, xb)

    def test_top_q_checker(self):
        self.assertTrue(tq.indep_cover(self.v, self.s, self.R)[0])

    def test_fixed_n_criterion(self):
        ok, fails = to.fixed_check(tq.SIMPLE_63, 64)
        self.assertTrue(ok, fails[:3])


if __name__ == "__main__":
    unittest.main()
