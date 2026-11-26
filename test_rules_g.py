# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Standard-library tests for route 13 (rule_search_g.py, PREREG_rules_g.md). No OR-Tools."""
import random
import unittest
from fractions import Fraction as F

import rule_search_g as rg
import slr


def random_cand(rng, m, N, P, k_add=3):
    touch, _fixed, added = rg.pools_g(m, N, P)
    _Md, shifts = rg.shift_menu(N)
    nz = [S for S in shifts if S]
    cand = {"removed": [], "rephased": {}, "added": {}}
    for w in touch:
        r = rng.random()
        if r < 0.3:
            cand["removed"].append(w)
        elif r < 0.6:
            cand["rephased"][w] = rng.choice(nz)
    for a in rng.sample(added, min(k_add, len(added))):
        cand["added"][a] = rng.choice(shifts)
    return cand


class TestMenu(unittest.TestCase):
    def test_shift_menu(self):
        # sigma0 takes 8 values (0, 1/2, 1/3, 2/3, 1/4, 3/4, 1/6, 5/6), beta 9 values; the
        # sigma0 grid step (Md/12) exceeds the whole beta range (4 Md/(2(N+1)) * 2), so 72.
        for N, Md in ((95, 192), (96, 1164), (11, 24)):
            got_Md, shifts = rg.shift_menu(N)
            self.assertEqual(got_Md, Md)
            self.assertEqual(len(shifts), 72 if N != 11 else len(set(shifts)))
            self.assertIn(0, shifts)
        # Poliakova's shifts at N = 96: 1/2 + (1/2)/97 -> 582 + 6; -1/97 -> 1164 - 12
        self.assertEqual(rg.shift_key(F(1, 2), F(1, 2), 96), 588)
        self.assertEqual(rg.shift_key(0, -1, 96), 1152)
        self.assertEqual(rg.shift_key(F(1, 4), 0, 96), 291)

    def test_pools(self):
        touch, fixed, added = rg.pools_g(6, 95, rg.P5)
        self.assertEqual(len(touch), 32)  # 5-smooth j <= 95, counted by hand
        self.assertEqual(len(fixed), 63)
        self.assertTrue(all(a % 6 for a in added))
        self.assertIn(3, added)
        self.assertNotIn(6, added)
        self.assertTrue(max(added) <= 2 * 6 * 95 + 1)


class TestClauses(unittest.TestCase):
    def check_instance(self, m, n, N, P, trials, pts, seed):
        rng = random.Random(seed)
        touch, fixed, added = rg.pools_g(m, N, P)
        Md, shifts = rg.shift_menu(N)
        for _ in range(trials):
            cand = random_cand(rng, m, N, P)
            v, s = rg.config_of(cand, m, N, Md)
            lits = rg.lits_of(cand, touch)
            points = [F(rng.randrange(0, 10 ** 7), 10 ** 7) for _ in range(pts)]
            points += [F(c, m * (n + 1)) for c in range(0, m * (n + 1), 3)]
            gaps = rg.float_gaps(v, s, 1.0 / (n + 1))
            points += rg.gap_points(gaps, 30)
            for t in points:
                cov = not rg.uncovered_exact(t, v, s, n)
                c = rg.point_clause(t, n, touch, fixed, added, Md, shifts)
                by_clause = c is None or bool(lits.intersection(c))
                self.assertEqual(cov, by_clause, (m, n, N, str(t), cand))
            for t in rg.gap_points(gaps, 30):
                # a float gap point that is exactly uncovered violates its own clause
                if rg.uncovered_exact(t, v, s, n):
                    c = rg.point_clause(t, n, touch, fixed, added, Md, shifts)
                    self.assertIsNotNone(c)
                    self.assertFalse(lits.intersection(c))

    def test_clause_equals_exact_cover_m2(self):
        self.check_instance(2, 10, 11, rg.P3, 12, 60, 1)

    def test_clause_equals_exact_cover_m6(self):
        self.check_instance(6, 8, 9, rg.P5, 10, 60, 2)

    def test_clause_equals_exact_cover_m4(self):
        self.check_instance(4, 12, 14, rg.P5, 6, 40, 3)

    def test_integer_test_matches_fractions(self):
        rng = random.Random(4)
        for _ in range(3000):
            v = rng.randrange(1, 400)
            Md = rng.choice([24, 192, 1164])
            S = rng.randrange(Md)
            t = F(rng.randrange(10 ** 6), 10 ** 6 + rng.randrange(1, 50))
            n1 = rng.randrange(5, 100)
            x = (v * t + F(S, Md)) % 1
            self.assertEqual(rg.covered_int(v, S, t.numerator, t.denominator, Md, n1),
                             min(x, 1 - x) < F(1, n1))


class TestPoliakova(unittest.TestCase):
    def test_poliakova_is_a_cover_at_95(self):
        # Poliakova's rule at N = 96: 96 - 3 + 2 = 95 runners, closed 1/97-cover, so the
        # open arcs of radius 1/96 cover; both global checkers must agree.
        cand = rg.poliakova_cand(96)
        cert = rg.certify_g(cand, 2, 95, 96, rg.shift_unit(96))
        self.assertTrue(cert["ok"], {k: cert[k] for k in ("n", "sweep", "endpoints")})
        self.assertEqual(cert["n"], 95)

    def test_poliakova_satisfies_seed_clauses(self):
        m, n, N = 2, 95, 96
        touch, fixed, added = rg.pools_g(m, N, rg.P3)
        Md, shifts = rg.shift_menu(N)
        cand = rg.poliakova_cand(N)
        for w in cand["removed"] + list(cand["rephased"]):
            self.assertIn(w, touch)
        for a in cand["added"]:
            self.assertIn(a, added)
        lits = rg.lits_of(cand, touch)
        pts = rg.seed_points(m, n, N, touch)
        self.assertGreater(len(pts), 300)
        k = 0
        for t in pts:
            c = rg.point_clause(t, n, touch, fixed, added, Md, shifts)
            if c is not None:
                k += 1
                self.assertTrue(lits.intersection(c), str(t))
        self.assertGreater(k, 0)

    def test_broken_rule_fails(self):
        # removing 8, 32, 192 with nothing else leaves holes; the exact sweep finds one and
        # the clause of that point is violated
        m, n, N = 2, 95, 96
        touch, fixed, added = rg.pools_g(m, N, rg.P3)
        Md, shifts = rg.shift_menu(N)
        cand = {"removed": [8, 32, 192], "rephased": {}, "added": {}}
        v, s = rg.config_of(cand, m, N, Md)
        ok, x = slr.covers_sweep(v, s, F(1, n + 1))
        self.assertFalse(ok)
        self.assertTrue(rg.uncovered_exact(F(x) % 1, v, s, n))
        c = rg.point_clause(F(x) % 1, n, touch, fixed, added, Md, shifts)
        self.assertIsNotNone(c)
        self.assertFalse(rg.lits_of(cand, touch).intersection(c))


class TestFloatGaps(unittest.TestCase):
    def test_one_runner(self):
        g = rg.float_gaps([1], [0], 0.1)
        self.assertEqual(len(g), 1)
        self.assertAlmostEqual(g[0][0], 0.1)
        self.assertAlmostEqual(g[0][1], 0.9)
        pts = rg.gap_points(g, 5)
        self.assertEqual(len(pts), 3)
        self.assertTrue(all(F(1, 10) < p < F(9, 10) for p in pts))

    def test_base_has_no_wide_gap(self):
        # speeds 1..10 with radius 1/11: Dirichlet, only isolated points can be uncovered
        g = rg.float_gaps(list(range(1, 11)), [0] * 10, 1.0 / 11)
        self.assertTrue(all(b - a < 1e-9 for a, b in g))

    def test_touch_points_find_dirichlet_points(self):
        # speeds 1..10, open radius 1/11: c/11 is uncovered (||j c/11|| >= 1/11 for j <= 10),
        # and runner 10's arc around 1/10 starts exactly at 1/11, where runner 1's arc ends
        v = list(range(1, 11))
        s = [F(0)] * 10
        _g, touches = rg.float_scan(v, s, 1.0 / 11)
        pts = rg.touch_points(touches, v, s, 10, 100)
        self.assertTrue(pts)
        for t in pts:
            self.assertEqual((t * 11).denominator, 1, str(t))
        self.assertIn(F(1, 11), pts)


class TestTiers(unittest.TestCase):
    def test_tiers(self):
        for tag in rg.ORDER_G:
            m, n, N, P, _h, _e = rg.TIERS_G[tag]
            self.assertLessEqual(n, rg.NMAX + 1)
            self.assertGreaterEqual(N - n, 1)
        for plan in (rg.PLAN_G1, rg.PLAN_G2, rg.PLAN_G3):
            self.assertLessEqual(sum(s for _t, s in plan), 530)
            for t, _s in plan:
                self.assertIn(t, rg.TIERS_G)


if __name__ == "__main__":
    unittest.main()
