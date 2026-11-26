# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Tests for rule_search_s.py (PREREG_rules_s.md, sanity checks S1 and S2).

Standard library only; the one solver test is skipped when OR-Tools is not installed."""
import json
import math
import os
import tempfile
import unittest

import rules_m
import rule_search_m
import rule_search_s as rs

POL = rules_m.POLIAKOVA_9_8
POL_X = sorted(set(POL["removed"]) | set(POL["rephased"]))


class Pools(unittest.TestCase):
    def test_smooth(self):
        self.assertTrue(rs.smooth(1, (2,)))
        self.assertTrue(rs.smooth(108, (2, 3)))  # 2^2 3^3
        self.assertFalse(rs.smooth(14, (2, 3, 5)))
        self.assertTrue(rs.smooth(7, None))

    def test_small_pool(self):
        # even 3-smooth numbers <= 24: 2, 4, 6, 8, 12, 16, 18, 24 (10, 14, 20, 22 have 5, 7, 11);
        # odd 3-smooth <= 49: 1, 3, 9, 27.
        self.assertEqual(rs.pools_s(24, 49, 2, (2, 3)),
                         ([2, 4, 6, 8, 12, 16, 18, 24], [1, 3, 9, 27]))

    def test_tier_s5A2_pool(self):
        # 5-smooth numbers <= 59: 1 2 3 4 5 6 8 9 10 12 15 16 18 20 24 25 27 30 32 36 40 45 48
        # 50 54 (25 of them), doubled for the evens <= 118; odd 5-smooth <= 237:
        # 1 3 5 9 15 25 27 45 75 81 125 135 225 (13).
        m, L, A = rs.tier_size("s5A2")
        self.assertEqual((m, L, A), (2, 118, 237))
        base, added = rs.pools_s(L, A, m, (2, 3, 5))
        self.assertEqual(len(base), 25)
        self.assertEqual(added, [1, 3, 5, 9, 15, 25, 27, 45, 75, 81, 125, 135, 225])

    def test_every_tier_targets_58(self):
        # a gain-1 rule with L = U = 59 m has threshold ceil(L/m) - 1 = 58
        for tag in rs.ORDER:
            m, L, A = rs.tier_size(tag)
            self.assertEqual(-(-L // m) - 1, rs.TARGET_N, tag)
            self.assertEqual(A, 2 * L + 1)
        self.assertEqual(set(rs.ORDER) | {"chk192"}, set(rs.TIERS))


class EncodingCompleteness(unittest.TestCase):
    """S1: the known rule satisfies every clause the restricted encoder makes."""

    def test_poliakova_in_3smooth_m2_pool(self):
        base, added = rs.pools_s(192, 9, 2, (2, 3))
        cl, lits = rs.all_clauses_s(base, added, 2, rule_search_m.halves(), rs.DENS_A, qs=POL_X)
        self.assertGreater(lits, 0)
        self.assertEqual(rule_search_m.clauses_satisfied(POL, cl), [])

    def test_broken_rule_detected(self):
        # without the added speed 9 the classes k = 1, 5 (1 mod 4) of q = 12 lose their cover
        broken = {"m": 2, "removed": POL["removed"], "rephased": POL["rephased"],
                  "added": {3: POL["added"][3]}}
        base, added = rs.pools_s(192, 9, 2, (2, 3))
        cl, _ = rs.all_clauses_s(base, added, 2, rule_search_m.halves(), rs.DENS_A, qs=POL_X)
        self.assertEqual(sorted(rule_search_m.clauses_satisfied(broken, cl)), [(12, 1), (12, 5)])

    def test_poliakova_scaled_in_5smooth_m6_pool(self):
        sc = rules_m.scale(POL, 3)  # modulus 6: speeds times 3, same shifts
        X = sorted(set(sc["removed"]) | set(sc["rephased"]))
        self.assertEqual(X, [24, 36, 48, 72, 96, 144, 192, 288, 576])
        base, added = rs.pools_s(576, 27, 6, (2, 3, 5))
        self.assertIn(9, added)
        self.assertIn(27, added)
        cl, _ = rs.all_clauses_s(base, added, 6, rule_search_m.halves(), rs.DENS_A, qs=X)
        self.assertEqual(rule_search_m.clauses_satisfied(sc, cl), [])


class KnownRule(unittest.TestCase):
    """S2: the criterion, the threshold and the global certificate on Poliakova's rule."""

    def test_local_and_threshold(self):
        ok, fails = rules_m.local_check(POL)
        self.assertTrue(ok, fails[:3])
        self.assertEqual(rules_m.threshold(POL), 95)  # ceil(192/2) - 1

    def test_certify_95(self):
        rec = rs.certify_n(POL, None, 95)
        self.assertEqual((rec["n"], rec["N"]), (95, 96))
        self.assertEqual(rec["R"], "2/193")
        self.assertTrue(rec["ok"] and rec["endpoints"] and rec["sweep"])

    def test_probe_certification_path(self):
        # a cached rule skips the solver; the probe then certifies from its threshold
        d = tempfile.mkdtemp(prefix="mv2-test-rules-s-")
        with open(os.path.join(d, "rule.json"), "w", encoding="utf-8") as f:
            json.dump({"tag": "test", "L": 192, "rule": rules_m.rule_to_json(POL),
                       "threshold": 95}, f)
        rep = rs.probe([], budget=200, cache=d, nmax=95)
        self.assertIn("cached rule from test", rep)
        self.assertIn("CERTIFIED n=95 FAILED=- S4_disagree=-", rep)
        self.assertIn("missing_58_94=58-94", rep)

    def test_ranges_and_fmt(self):
        self.assertEqual(rs._ranges([60, 58, 59, 62]), "58-60,62")
        self.assertEqual(rs._ranges([]), "-")
        s = rs.fmt_rule(rules_m.rule_to_json(rules_m.TOY_M4))
        self.assertEqual(s, "m=4 R=[8] S={} A={2:3/4,0;6:3/4,0}")


def _have_ortools():
    try:
        import ortools.sat.python.cp_model  # noqa: F401
        return True
    except Exception:
        return False


@unittest.skipUnless(_have_ortools(), "OR-Tools not installed")
class SolverSensitivity(unittest.TestCase):
    """The solver must find some verified gain-1 rule where one is known to exist (L = 192)."""

    def test_finds_a_rule_at_192(self):
        import time
        info = rs.run_tier("chk192", time.time() + 400, workers=2)
        self.assertIn(info["status"], ("OPTIMAL", "FEASIBLE"), info)
        self.assertTrue(info["local_ok"], info.get("local_fails"))
        self.assertGreaterEqual(info["gain"], 1)
        self.assertLessEqual(info["threshold"], 95)


if __name__ == "__main__":
    unittest.main()
