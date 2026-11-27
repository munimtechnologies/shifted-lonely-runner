# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Standard-library tests for top_o.py (route 19, PREREG_rules_o.md). Every expected value is
worked out by hand in a comment or follows from a theorem stated next to it."""
import random
import unittest
from fractions import Fraction as F

import rules_m
import slr
import top_o as to


class TestRadius(unittest.TestCase):
    def test_radius_below_one_over_n_plus_one(self):
        # 128/(128(n+1)+1) < 1/(n+1) because 128(n+1) < 128(n+1)+1
        for n in range(1, 100):
            self.assertLess(to.radius(n), F(1, n + 1))
        # n = 63: 128/8193 > 66/4225 (Callens's gamma) since 128*4225 = 540800 > 66*8193 = 540738
        self.assertGreater(to.radius(63), F(66, 4225))
        self.assertEqual(to.rho_of(64, 1), F(8320, 8193))  # 128*65/8193


class TestIntervals(unittest.TestCase):
    def test_top_trick_by_hand(self):
        # N = 4, delta = 1/5, q = 8 = 2N, class k = 1, rho = 6/5.
        # Speed 2 at t = (1 + z/5)/8: x = 1/4, c = 1/4, J = 0, A = 5/4;
        # |5/4 + z/4| <= 6/5  <=>  z in [-49/5, -1/5]  -> [-1, -1/5].
        self.assertEqual(to.z_intervals(2, F(0), F(0), 8, 1, 4, F(6, 5)), [(F(-1), F(-1, 5))])
        # Top speed 8 at shift -delta: x = 1, c = 1, J = 1, A = 0; |z - 1| <= 6/5 -> [-1/5, 1].
        self.assertEqual(to.z_intervals(8, F(0), F(-1), 8, 1, 4, F(6, 5)), [(F(-1, 5), F(1))])
        # At rho = 1 the speed-2 interval shrinks to the point z = -1 (hi = 4(1 - 5/4) = -1)
        # and the top covers [0, 1]: the gap (-1, 0) is what the slack closes.
        self.assertEqual(to.z_intervals(2, F(0), F(0), 8, 1, 4, F(1)), [(F(-1), F(-1))])
        self.assertEqual(to.z_intervals(8, F(0), F(-1), 8, 1, 4, F(1)), [(F(0), F(1))])

    def test_far_runner_gives_nothing(self):
        # N = 4, q = 8, k = 1: speed 4 sits at x = 1/2 + z/10, never within 6/25 of an integer.
        self.assertEqual(to.z_intervals(4, F(0), F(0), 8, 1, 4, F(6, 5)), [])

    def test_menus_and_pools(self):
        self.assertEqual(to.s0_menu(to.DENS_A),
                         [F(0), F(1, 6), F(1, 4), F(1, 3), F(1, 2), F(2, 3), F(3, 4), F(5, 6)])
        self.assertEqual(len(to.betas_of("h")), 9)   # -2, -3/2, ..., 2
        self.assertEqual(len(to.betas_of("x")), 21)  # 17 eighths on [-1, 1] and -2, -3/2, 3/2, 2
        touch, fixed, added = to.pools_o(64, to.P3)
        self.assertEqual(touch, [4, 8, 12, 16, 24, 32, 36, 48, 64, 72, 96, 108, 128])
        self.assertEqual(added, [1, 3, 9, 27, 81])
        self.assertEqual(len(touch) + len(fixed), 64)
        touch81, _f, _a = to.pools_o(81, to.P3)
        self.assertEqual(touch81, [4, 8, 12, 16, 24, 32, 36, 48, 64, 72, 96, 108, 128, 144, 162])


class TestKnownRules(unittest.TestCase):
    def test_poliakova_closed_delta_cover(self):
        # Poliakova's 9 -> 8 rule is a closed delta-cover for every N >= 96 (her Theorem 2).
        ok, fails = to.fixed_check(rules_m.POLIAKOVA_9_8, 96, rho=F(1))
        self.assertTrue(ok, fails[:3])

    def test_callens(self):
        # Callens: gamma = 66/4225 = delta (1 + delta) at N = 64 (route 17 measured the margin
        # 1/64 - gamma = 1/270400 = 3.7e-6). So it is a closed cover at 128/8193 > gamma, and
        # not at delta = 1/65 < gamma.
        ok, fails = to.fixed_check(to.CALLENS_63, 64)
        self.assertTrue(ok, fails[:3])
        self.assertFalse(to.fixed_check(to.CALLENS_63, 64, rho=F(1))[0])
        cert = to.certify(to.CALLENS_63, 64)
        self.assertTrue(cert["ok"])
        self.assertEqual(cert["n"], 63)

    def test_clauses_accept_callens(self):
        # Soundness of the encoding: a rule that passes fixed_check satisfies every clause.
        N, g = 64, 1
        rho = to.rho_of(N, g)
        touch, fixed, added = to.pools_o(N, to.P3)
        s0s, betas = to.s0_menu(to.DENS_A), to.betas_of("x")
        m, removed, reph, add = rules_m._norm_rule(to.CALLENS_63)
        chosen = {("e", w, s0, b) for w, (s0, b) in reph.items()}
        chosen |= {("o", a, s0, b) for a, (s0, b) in add.items()}
        chosen |= {("u", w) for w in touch if w not in reph and w not in removed}
        for q, k in [(128, 1), (128, 63), (4, 1), (4, 3), (108, 5), (32, 3), (64, 5), (12, 7)]:
            cls = to.class_clauses_o(q, k, N, rho, touch, fixed, added, s0s, betas)
            for keys in cls:
                self.assertTrue(any(key in chosen for key in keys), (q, k, keys[:4]))


class TestAgainstGlobal(unittest.TestCase):
    def test_sure_cases(self):
        # True: one runner moved by delta/2 still covers its own window at rho = 3/2,
        # because |z + 1/2| <= 3/2 for every z in [-1, 1]; nothing else changes.
        rule = {"m": 2, "removed": [], "rephased": {6: (F(0), F(1, 2))}, "added": {}}
        self.assertTrue(to.fixed_check(rule, 5, rho=F(3, 2))[0])
        # False: speeds 6 and 8 alone at N = 4 cover measure 2 * 2 * (1/5) = 4/5 < 1.
        rule = {"m": 2, "removed": [2, 4], "rephased": {}, "added": {}}
        self.assertFalse(to.fixed_check(rule, 4, rho=F(1))[0])
        self.assertFalse(slr.covers_sweep([6, 8], [F(0), F(0)], F(1, 5))[0])

    def test_random_rules(self):
        # fixed_check(rho) is exactly "closed cover at r = rho/(N+1)" (module docstring), so
        # True  => open arcs of radius r + 10^-6 cover;  False => open arcs of radius r do not.
        rng = random.Random(19)
        s0s = [F(0), F(1, 2), F(1, 4), F(3, 4), F(1, 3)]
        bs = [F(-1), F(-1, 2), F(0), F(1, 2), F(1)]
        for _trial in range(60):
            N = rng.randint(4, 9)
            evens = list(range(2, 2 * N + 1, 2))
            removed, reph = [], {}
            for w in rng.sample(evens, rng.randint(1, 3)):
                if rng.random() < 0.4:
                    removed.append(w)
                else:
                    s0, b = rng.choice(s0s), rng.choice(bs)
                    if s0 == 0 and b == 0:
                        b = F(1)
                    reph[w] = (s0, b)
            added = {}
            for a in rng.sample(list(range(1, 2 * N + 2, 2)), rng.randint(0, 2)):
                added[a] = (rng.choice(s0s), rng.choice(bs))
            rule = {"m": 2, "removed": removed, "rephased": reph, "added": added}
            rho = rng.choice([F(1), F(9, 8), F(5, 4)])
            ok, _ = to.fixed_check(rule, N, rho=rho)
            v, s, delta, _k = rules_m.build_config(rule, N)
            r = rho * delta
            if ok:
                self.assertTrue(slr.covers_sweep(v, s, r + F(1, 10 ** 6))[0], rule)
            else:
                self.assertFalse(slr.covers_sweep(v, s, r)[0], rule)


if __name__ == "__main__":
    unittest.main()
