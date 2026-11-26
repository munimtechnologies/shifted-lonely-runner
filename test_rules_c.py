# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Tests for rule_search_c.py (PREREG_rules_c.md, sanity checks C1-C3).

Standard library only; the solver test is skipped when OR-Tools is not importable."""
import json
import os
import random
import tempfile
import unittest
from fractions import Fraction as F

import rules_m
import rule_search_m
import rule_search_c as rc

POL = rules_m.POLIAKOVA_9_8
POL_X = sorted(set(POL["removed"]) | set(POL["rephased"]))


def all_class_clauses(rule, m, L, P, betas, dens):
    touch, fixed, added = rc.pools_c(m, L, P)
    X = sorted(set(rule["removed"]) | set(rule["rephased"]))
    cl = {}
    for q in X:
        for k in rules_m.responsible_classes(q, m):
            cl[(q, k)] = rc.class_clauses(q, k, touch, fixed, added, betas, dens)
    return cl


class Pools(unittest.TestCase):
    def test_small_pool(self):
        # m = 2, L = 24, P = {2, 3}: touchable evens 2 4 6 8 12 16 18 24; fixed 10 14 20 22;
        # added odd 3-smooth <= 49: 1 3 9 27
        self.assertEqual(rc.pools_c(2, 24, (2, 3)),
                         ([2, 4, 6, 8, 12, 16, 18, 24], [10, 14, 20, 22], [1, 3, 9, 27]))

    def test_m3_pool(self):
        t, f, a = rc.pools_c(3, 36, (2, 3))
        self.assertEqual(t, [3, 6, 9, 12, 18, 24, 27, 36])
        self.assertEqual(f, [15, 21, 30, 33])
        self.assertEqual(a, [1, 2, 4, 8, 16, 32, 64])

    def test_tiers_thresholds(self):
        for tag, (m, L, P, kind, dens, exp) in rc.TIERS.items():
            self.assertEqual(L % m, 0, tag)
            thr = L // m - 1  # gain 1
            if tag.endswith("58"):
                self.assertEqual(thr, 58, tag)
            if tag.endswith("94"):
                self.assertEqual(thr, 94, tag)
        self.assertEqual(rc.TIERS["c2chk"][1] // 2 - 1, 95)
        self.assertEqual(rc.TIERS["c2neg"][1] // 2 - 1, 94)
        self.assertEqual(set(rc.ORDER), set(rc.TIERS))


class Completeness(unittest.TestCase):
    """C1: the known rule satisfies every clause; a broken rule violates exactly the classes
    that local_check says it fails."""

    def test_poliakova_satisfies_all(self):
        cl = all_class_clauses(POL, 2, 192, (2, 3), rule_search_m.halves(), rc.DENS_A)
        self.assertEqual(rule_search_m.clauses_satisfied(POL, cl), [])
        ok, fails = rules_m.local_check(POL, untouched_upto=192)
        self.assertTrue(ok, fails[:3])

    def test_poliakova_scaled_m6(self):
        sc = rules_m.scale(POL, 3)
        cl = all_class_clauses(sc, 6, 576, (2, 3, 5), rule_search_m.halves(), rc.DENS_A)
        self.assertEqual(rule_search_m.clauses_satisfied(sc, cl), [])

    def test_broken_matches_local_check(self):
        broken = {"m": 2, "removed": POL["removed"], "rephased": POL["rephased"],
                  "added": {3: POL["added"][3]}}
        cl = all_class_clauses(broken, 2, 192, (2, 3), rule_search_m.halves(), rc.DENS_A)
        bad = sorted(rule_search_m.clauses_satisfied(broken, cl))
        ok, fails = rules_m.local_check(broken, untouched_upto=192)
        self.assertEqual(bad, sorted({(q, k) for q, k, _ in fails}))
        ok0, fails0 = rules_m.local_check(broken)  # without helpers: the known two failures
        self.assertEqual(sorted({(q, k) for q, k, _ in fails0}), [(12, 1), (12, 5)])


class RandomConsistency(unittest.TestCase):
    """C2: for random rules inside the menu, the classes with a violated clause are exactly
    the classes that local_check fails (both directions), for m = 2, 3, 4, 6."""

    def _trial(self, rnd, m, L, P, dens, betas):
        touch, fixed, added = rc.pools_c(m, L, P)
        s0s = sorted({F(a, d) for d in dens for a in range(d)})
        X = rnd.sample(touch, rnd.randint(2, min(5, len(touch))))
        nrem = rnd.randint(1, len(X) - 1)
        rem, reph = X[:nrem], {}
        for w in X[nrem:]:
            while True:
                s0, b = rnd.choice(s0s), rnd.choice(betas)
                if s0 != 0 or b != 0:
                    break
            reph[w] = (s0, b)
        add = {}
        for a in rnd.sample(added, rnd.randint(0, min(3, len(added)))):
            add[a] = (rnd.choice(s0s), rnd.choice(betas))
        rule = {"m": m, "removed": rem, "rephased": reph, "added": add}
        cl = all_class_clauses(rule, m, L, P, betas, dens)
        bad = sorted(rule_search_m.clauses_satisfied(rule, cl))
        ok, fails = rules_m.local_check(rule, untouched_upto=L)
        self.assertEqual(bad, sorted({(q, k) for q, k, _ in fails}), rule)
        return len(cl), len(bad)

    def test_random_rules(self):
        rnd = random.Random(20261126)
        total = failed = 0
        for m, L, P, dens in ((2, 48, (2, 3), rc.DENS_A), (3, 36, (2, 3), rc.DENS_A),
                              (4, 48, (2, 3, 5), rc.DENS_B), (6, 72, (2, 3, 5), rc.DENS_B)):
            betas = rule_search_m.halves() if dens == rc.DENS_A else rule_search_m.quarters()
            for _ in range(12):
                n, b = self._trial(rnd, m, L, P, dens, betas)
                total += n
                failed += b
        self.assertGreater(failed, 0)
        self.assertGreater(total - failed, 0)

    def test_fixed_helper_only_middle(self):
        # m = 2, L = 24, P = {2, 3}: the fixed helper 20 = 5 * 4 covers class (4, 1) on
        # |z| <= 1/5. The rephase options of 4 itself (beta = +-1/2) reach every point, so no
        # clause is empty, and no clause is needed for a segment inside [-1/5, 1/5] alone.
        touch, fixed, added = rc.pools_c(2, 24, (2, 3))
        cl = rc.class_clauses(4, 1, touch, fixed, added, rule_search_m.halves(), rc.DENS_A)
        self.assertTrue(cl)
        self.assertTrue(all(len(c) > 0 for c in cl))
        # removing 4 alone (no other change) must fail class (4, 1) in both views
        rule = {"m": 2, "removed": [4], "rephased": {}, "added": {}}
        self.assertEqual(rule_search_m.clauses_satisfied(rule, {(4, 1): cl}), [(4, 1)])
        ok, fails = rules_m.local_check(rule, untouched_upto=24)
        self.assertIn((4, 1), {(q, k) for q, k, _ in fails})


class Certification(unittest.TestCase):
    def test_probe_certification_path(self):
        d = tempfile.mkdtemp(prefix="mv2-test-rules-c-")
        with open(os.path.join(d, "rule.json"), "w", encoding="utf-8") as f:
            json.dump({"tag": "test", "L": 192, "rule": rules_m.rule_to_json(POL),
                       "threshold": 95}, f)
        rep = rc.probe([], budget=200, cache=d, nmax=95)
        self.assertIn("cached rule from test", rep)
        self.assertIn("CERTIFIED n=95 FAILED=- missing_58_94=58-94", rep)


def _have_ortools():
    try:
        import ortools.sat.python.cp_model  # noqa: F401
        return True
    except Exception:
        return False


@unittest.skipUnless(_have_ortools(), "OR-Tools not installed")
class SolverSensitivity(unittest.TestCase):
    def test_c2chk_finds(self):
        import time
        info = rc.run_tier("c2chk", time.time() + 400, workers=2)
        self.assertEqual(info["status"], "FOUND", {k: info[k] for k in info if k != "classes"})
        self.assertLessEqual(info["threshold"], 95)


if __name__ == "__main__":
    unittest.main()
