# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""The n = 79 counterexample (cover_n079.json): exact re-checks by four checkers.

Found by route 19d's pre-registered target tier r80 (gate probe R4, 2026-11-28 03:43 UTC;
RESULTS_n079.md). On the base 2, 4, ..., 160 at shift 0 (N = 80, delta = 1/81): remove 4, 16,
20, 40, 96, 120 (6); rephase 8 and 80 to -delta, 32 to -3 delta/2, 160 to +delta, and 12, 24,
48, 60 to 1/2 + delta/2 (8); add 3, 9, 15, 45 at 1/4 and 5 at 1/4 + delta/2 (5). Gain 6 - 5 = 1,
so 80 - 1 = 79 runners, and their open arcs of radius 1/80 cover the circle.

Checkers: verify_cover.first_gap (fresh, standard library, sweep over open intervals),
slr.covers_sweep and slr.covers_endpoints, top_q.indep_cover (endpoint criterion), and the
fixed-N criterion top_o.fixed_check at the slack radius. Every control value is proved by hand
in its comment."""
import json
import os
import unittest
from fractions import Fraction as F

import rules_m
import top_o as to
import top_q as tq
import verify_cover as vc

HERE = os.path.dirname(os.path.abspath(__file__))
H = F(1, 2)
Q4 = F(1, 4)

RULE_R80 = {
    "m": 2,
    "removed": [4, 16, 20, 40, 96, 120],
    "rephased": {8: (F(0), F(-1)), 12: (H, H), 24: (H, H), 32: (F(0), F(-3, 2)), 48: (H, H),
                 60: (H, H), 80: (F(0), F(-1)), 160: (F(0), F(1))},
    "added": {3: (Q4, F(0)), 5: (Q4, H), 9: (Q4, F(0)), 15: (Q4, F(0)), 45: (Q4, F(0))},
}


def load():
    with open(os.path.join(HERE, "cover_n079.json"), encoding="utf-8") as f:
        return json.load(f)


def dist(x):
    """||x||, distance to the nearest integer."""
    x = F(x) % 1
    return min(x, 1 - x)


class TestFreshChecker(unittest.TestCase):
    """Controls for verify_cover.first_gap, each proved by hand."""

    def test_dirichlet_positive(self):
        # speeds 1..10 at shift 0: for every t some q <= 10 has ||q t|| <= 1/11 < 1/10
        # (Dirichlet), so the open arcs of radius 1/10 cover.
        self.assertTrue(vc.covers(list(range(1, 11)), [0] * 10, F(1, 10)))

    def test_dirichlet_negative(self):
        # radius 1/11: at t = 1/11, ||q/11|| >= 1/11 for q = 1..10, so t is uncovered.
        v = list(range(1, 11))
        gap = vc.first_gap(v, [0] * 10, F(1, 11))
        self.assertIsNotNone(gap)
        # the reported point really is uncovered
        self.assertTrue(all(dist(q * gap) >= F(1, 11) for q in v), gap)

    def test_even_base(self):
        # 2, 4, ..., 160 at shift 0 is speeds 1..80 at time 2t: covers at 1/80 (Dirichlet,
        # some k <= 80 has ||k (2t)|| <= 1/81 < 1/80); not at 1/81 (t = 1/162 gives
        # ||2k/162|| = ||k/81|| >= 1/81 for k = 1..80).
        v = list(range(2, 161, 2))
        self.assertTrue(vc.covers(v, [0] * 80, F(1, 80)))
        gap = vc.first_gap(v, [0] * 80, F(1, 81))
        self.assertIsNotNone(gap)
        self.assertTrue(all(dist(w * gap) >= F(1, 81) for w in v), gap)

    def test_measure_bound(self):
        # 79 open arcs of total length 79 * 2/162 = 79/81 < 1 cannot cover the circle.
        c = load()
        v = [int(a) for a, _ in c["runners"]]
        s = [F(b) for _, b in c["runners"]]
        gap = vc.first_gap(v, s, F(1, 162))
        self.assertIsNotNone(gap)
        self.assertTrue(all(dist(w * gap + x) >= F(1, 162) for w, x in zip(v, s)), gap)


class TestCoverN079(unittest.TestCase):
    def test_json_is_the_rule(self):
        # the explicit runner list equals the rule applied to the base 2, ..., 160
        v, s, delta, k = rules_m.build_config(RULE_R80, 80)
        self.assertEqual(delta, F(1, 81))
        self.assertEqual(k, 79)
        built = sorted(zip(v, s))
        c = load()
        listed = sorted((int(a), F(b)) for a, b in c["runners"])
        self.assertEqual(built, listed)
        self.assertEqual(rules_m.rule_to_json(RULE_R80)["rephased"], c["rule"]["rephased"])
        self.assertEqual(rules_m.rule_to_json(RULE_R80)["added"], c["rule"]["added"])
        self.assertEqual(sorted(c["rule"]["removed"]), sorted(RULE_R80["removed"]))

    def test_shape(self):
        self.assertEqual(rules_m.gain(RULE_R80), 1)
        touched = set(RULE_R80["removed"]) | set(RULE_R80["rephased"]) | set(RULE_R80["added"])
        self.assertEqual(len(touched), 19)
        for w in touched:  # every touched speed is 5-smooth
            x = w
            for p in (2, 3, 5):
                while x % p == 0:
                    x //= p
            self.assertEqual(x, 1, w)

    def test_fresh_checker(self):
        facts = vc.check_certificate(load())
        self.assertEqual(facts["runners"], 79)
        self.assertTrue(facts["distinct"])
        self.assertTrue(facts["R_ok"])
        self.assertIsNone(facts["gap"], facts)
        self.assertTrue(facts["counterexample"], facts)

    def test_fixed_n_criterion(self):
        # closed cover at the slack radius 128/(128 * 80 + 1) < 1/80
        self.assertTrue(to.fixed_check(RULE_R80, 80, g=1)[0])

    def test_three_global_checkers(self):
        c = tq.full_cert(RULE_R80, 80, 79)
        self.assertTrue(c["sweep"])
        self.assertTrue(c["endpoints"])
        self.assertTrue(c["indep"])
        self.assertTrue(c["distinct"])
        self.assertTrue(c["ok"])
        self.assertEqual(c["R"], "1/80")


if __name__ == "__main__":
    unittest.main()
