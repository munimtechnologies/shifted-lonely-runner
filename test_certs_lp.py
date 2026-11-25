# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Exact re-check of certs_lp.json: counterexamples to the shifted Lonely Runner Conjecture.

A certificate (v, s) with distinct positive integer speeds v_1..v_n and rational shifts s_i is a
counterexample for n if the OPEN arcs {t : ||v_i t + s_i|| < 1/(n+1)} cover the circle R/Z:
then every time t has a runner closer than 1/(n+1) to the origin, so gamma(v; s) < 1/(n+1).

Four exact checks, each in exact rational or integer arithmetic:
  covers_int          written for this file: integer sweep after scaling time by
                      den * R_den * lcm(v) (no Fractions, no floats);
  slr.covers_sweep    Fraction sweep (slr.py);
  slr.covers_endpoints integer endpoint criterion (slr.py);
  slr_br.exact_cover  closed arcs of radius 1/(n+1) - 10^-11 (slr_br.py).
Standard library only; runs in a few seconds.
"""
import json
import math
import os
import unittest
from fractions import Fraction as F

import slr
import slr_br

HERE = os.path.dirname(os.path.abspath(__file__))


def covers_int(v, nums, den, Rn, Rd):
    """True iff the open arcs ||v_i t + nums_i/den|| < Rn/Rd cover the circle. Integers only.

    Time is scaled by Q = den * Rd * lcm(v): the arc of runner i around (k - s_i)/v_i becomes
    the open integer interval (c - h, c + h) with c = (k den - nums_i) Rd L / v_i and
    h = Rn den L / v_i. Lifts k = -1 .. v_i + 1 contain every arc meeting [0, Q]. The sweep
    keeps [0, cur) covered and needs cur itself strictly inside an interval; it ends when
    cur > Q, i.e. [0, Q] (the whole circle) is covered.
    """
    if not (0 < 2 * Rn < Rd):
        raise ValueError("radius must lie in (0, 1/2)")
    L = 1
    for x in v:
        L = L * x // math.gcd(L, x)
    Q = den * Rd * L
    iv = []
    for vi, k_s in zip(v, nums):
        if not (0 <= k_s < den):
            raise ValueError("shift numerator out of range")
        m = L // vi
        h = Rn * den * m
        for k in range(-1, vi + 2):
            c = (k * den - k_s) * Rd * m
            iv.append((c - h, c + h))
    iv.sort()
    cur, i, best = 0, 0, None
    while cur <= Q:
        while i < len(iv) and iv[i][0] < cur:
            if best is None or iv[i][1] > best:
                best = iv[i][1]
            i += 1
        if best is None or best <= cur:
            return False
        cur = best
    return True


def load():
    with open(os.path.join(HERE, "certs_lp.json"), encoding="utf-8") as fh:
        return json.load(fh)


class HandCases(unittest.TestCase):
    def test_two_runners(self):
        # v = (1, 2), s = (0, 0): gamma = 1/3, attained at t = 1/3 (||1/3|| = ||2/3|| = 1/3).
        self.assertFalse(covers_int([1, 2], [0, 0], 1, 1, 3))
        self.assertTrue(covers_int([1, 2], [0, 0], 1, 17, 50))
        self.assertFalse(slr.covers_sweep([1, 2], [0, 0], F(1, 3))[0])
        self.assertTrue(slr.covers_sweep([1, 2], [0, 0], F(17, 50))[0])

    def test_half_shift(self):
        # v = (1, 2), s = (0, 1/2): at t = 1/2 both distances are 1/2, so R = 1/3 cannot cover.
        self.assertFalse(covers_int([1, 2], [0, 1], 2, 1, 3))


class Certificates(unittest.TestCase):
    def test_well_formed(self):
        for c in load():
            n, v = c["n"], c["speeds"]
            self.assertEqual(len(v), n)
            self.assertEqual(len(c["shift_num"]), n)
            self.assertEqual(len(set(v)), n, "speeds must be distinct")
            self.assertGreaterEqual(min(v), 1)
            self.assertTrue(all(0 <= k < c["shift_den"] for k in c["shift_num"]))

    def test_counterexample_four_checkers(self):
        for c in load():
            n, v, den, nums = c["n"], c["speeds"], c["shift_den"], c["shift_num"]
            s = [F(k, den) for k in nums]
            R = F(1, n + 1)
            self.assertTrue(covers_int(v, nums, den, R.numerator, R.denominator), n)
            self.assertTrue(slr.covers_sweep(v, s, R)[0], n)
            self.assertTrue(slr.covers_endpoints(v, s, R)[0], n)
            self.assertTrue(slr_br.exact_cover(v, s, R - F(1, 10 ** 11)), n)

    def test_recorded_upper_bound(self):
        # The recorded gamma is an upper bound below 1/(n+1): the open arcs of that radius cover.
        for c in load():
            n, v, den, nums = c["n"], c["speeds"], c["shift_den"], c["shift_num"]
            g = F(c["gamma"])
            self.assertLess(g, F(1, n + 1))
            self.assertTrue(covers_int(v, nums, den, g.numerator, g.denominator), n)
            self.assertTrue(slr.covers_sweep(v, [F(k, den) for k in nums], g)[0], n)

    def test_not_too_good(self):
        # Sanity: the checkers can say no. The n = 55 certificate has loneliness about
        # 1/56.12 > 1/57 (float value from the probe), so arcs of radius 1/57 leave a gap.
        for c in load():
            if c["n"] != 55:
                continue
            n, v, den, nums = c["n"], c["speeds"], c["shift_den"], c["shift_num"]
            self.assertFalse(covers_int(v, nums, den, 1, n + 2), n)
            self.assertFalse(slr.covers_sweep(v, [F(k, den) for k in nums], F(1, n + 2))[0], n)


if __name__ == "__main__":
    unittest.main()
