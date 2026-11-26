# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Tests for rule_search_e.py (PREREG_rules_e.md). Standard library only; nothing here needs
OR-Tools."""
import json
import os
import tempfile
import unittest
from fractions import Fraction as F

import rules_m
import rule_search_c as rc
import rule_search_e as re_

POL = rules_m.POLIAKOVA_9_8
H = F(1, 2)


def _true_keys(rule):
    """The clause keys a rule makes true: ('u', w) for untouched touchables is handled apart."""
    m, removed, reph, added = rules_m._norm_rule(rule)
    keys = set()
    for w, (s0, b) in reph.items():
        keys.add(("e", w, s0, b))
    for a, (s0, b) in added.items():
        keys.add(("o", a, s0, b))
    return removed, reph, keys


def _satisfies_sample(tc, rule, m, L, P, per_q=6):
    touch, fixed, added = rc.pools_c(m, L, P)
    betas = [F(j, 2) for j in range(-4, 5)]
    dens = rc.DENS_A
    removed, reph, keys = _true_keys(rule)
    X = set(removed) | set(reph)
    for q in sorted(X):
        for k in rc._spread(rules_m.responsible_classes(q, m), per_q):
            for clause in rc.class_clauses(q, k, touch, fixed, added, betas, dens):
                sat = False
                for key in clause:
                    if key[0] == "u":
                        sat = sat or key[1] not in X
                    else:
                        sat = sat or key in keys
                tc.assertTrue(sat, (q, k, clause[:4]))


class Plans(unittest.TestCase):
    def test_plans(self):
        for plan, san in ((re_.PLAN_E1, re_.SANITY_E1), (re_.PLAN_E2, re_.SANITY_E2),
                          (re_.PLAN_E3, [])):
            self.assertLessEqual(sum(s for _, s in plan) + sum(c[3] for c in san), 530)
            for tag, _ in plan:
                self.assertIn(tag, re_.TIERS_E)
        self.assertTrue(set(re_.ORDER_E) <= set(re_.TIERS_E))

    def test_sanity_cubes_hold_poliakova(self):
        for (tag, T, kind, _s), rule in ((re_.SANITY_E1[0], POL),
                                         (re_.SANITY_E2[0], rules_m.scale(POL, 3))):
            m, L, P, _bk, _dens, _e = re_.TIERS_E[tag]
            touch, _fixed, added = rc.pools_c(m, L, P)
            mr = re_.mirror_rule(rule)
            self.assertEqual(re_.cube_of(mr), (T, kind))
            for w in list(mr["removed"]) + list(mr["rephased"]):
                self.assertIn(w, touch)
            for a in mr["added"]:
                self.assertIn(a, added)
            self.assertEqual(L, T)


class Mirror(unittest.TestCase):
    def test_canonical(self):
        self.assertTrue(re_.canonical(H, -H))
        self.assertFalse(re_.canonical(H, H))
        self.assertTrue(re_.canonical(0, 0))
        self.assertTrue(re_.canonical(0, -1))
        self.assertFalse(re_.canonical(0, 1))
        self.assertTrue(re_.canonical(F(1, 4), 0))
        self.assertFalse(re_.canonical(F(3, 4), 0))
        # exactly one of a non-self-mirror pair is canonical
        for s0 in (F(0), F(1, 6), F(1, 3), H, F(2, 3), F(3, 4)):
            for b in (F(-2), F(-1, 2), F(0), F(3, 2)):
                ms0, mb = re_.mirror_opt(s0, b)
                if (ms0, mb) != (s0, b):
                    self.assertNotEqual(re_.canonical(s0, b), re_.canonical(ms0, mb))

    def test_mirror_of_poliakova_passes(self):
        mp = re_.mirror_rule(POL)
        ok, fails = rules_m.local_check(mp, untouched_upto=192)
        self.assertTrue(ok, fails[:3])
        self.assertEqual(rules_m.threshold(mp, untouched_upto=192), 95)
        self.assertEqual(rules_m.rule_to_json(re_.mirror_rule(mp)), rules_m.rule_to_json(POL))
        sc = re_.mirror_rule(rules_m.scale(POL, 3))
        ok, fails = rules_m.local_check(sc, untouched_upto=576)
        self.assertTrue(ok, fails[:3])

    def test_rephased_top_and_canonical_mirror(self):
        # Poliakova's rule without the removal of 192: top 96, rephased (1/2, 1/2), gain 0.
        r = {"m": 2, "removed": [8, 32], "rephased": dict(POL["rephased"]),
             "added": dict(POL["added"])}
        ok, fails = rules_m.local_check(r, untouched_upto=192)
        self.assertTrue(ok, fails[:3])
        self.assertEqual(re_.cube_of(r), (96, "S"))
        self.assertFalse(re_.canonical(*r["rephased"][96]))
        mr = re_.mirror_rule(r)
        ok, fails = rules_m.local_check(mr, untouched_upto=192)
        self.assertTrue(ok, fails[:3])
        self.assertTrue(re_.canonical(*mr["rephased"][96]))

    def test_cube_of_poliakova(self):
        self.assertEqual(re_.cube_of(POL), (192, "R"))
        self.assertEqual(re_.cube_of(rules_m.scale(POL, 3)), (576, "R"))


class ClauseSoundness(unittest.TestCase):
    """The clauses that the cube models use are satisfied by known valid rules (the escape
    literal unt[q] is false for every touched q, so a cover must come from the rule)."""

    def test_mirror_poliakova_satisfies_c2chk_clauses(self):
        _satisfies_sample(self, re_.mirror_rule(POL), 2, 192, (2, 3))

    def test_poliakova_satisfies_c2chk_clauses(self):
        _satisfies_sample(self, POL, 2, 192, (2, 3))


class Bookkeeping(unittest.TestCase):
    def test_frontier_and_status(self):
        touch = [2, 4, 6]
        st = {"2R": "INFEASIBLE", "2S": "INFEASIBLE", "4R": "INFEASIBLE", "4S": "UNKNOWN"}
        self.assertEqual(re_.frontier(touch, st), 2)
        self.assertEqual(re_.tier_status(touch, st), "UNKNOWN")
        allinf = {re_.ckey(T, k): "INFEASIBLE" for T, k in re_.cubes_of(touch)}
        self.assertEqual(re_.frontier(touch, allinf), 6)
        self.assertEqual(re_.tier_status(touch, allinf), "INFEASIBLE")
        self.assertEqual(re_.frontier(touch, {}), 0)
        allinf["4S"] = "FOUND"
        self.assertEqual(re_.tier_status(touch, allinf), "FOUND")
        self.assertEqual(len(re_.cubes_of(touch)), 6)

    def test_probe_reports_old_states_without_solver(self):
        d = tempfile.mkdtemp(prefix="mv2-test-rules-e-")
        dd = tempfile.mkdtemp(prefix="mv2-test-rules-ed-")
        with open(os.path.join(dd, "tiers.json"), "w", encoding="utf-8") as f:
            json.dump({"c3A94": {"status": "INFEASIBLE", "iterations_total": 3,
                                 "seconds_total": 99.4}}, f)
        rep = re_.probe_e([], budget=60, cache=d, d_cache=dd, c_cache="")
        self.assertIn("11b c3A94=INFEASIBLE/3/99s", rep)
        self.assertTrue(rep.rstrip().splitlines()[-1].startswith("STATUS"))

    def test_decided_before(self):
        dd = tempfile.mkdtemp(prefix="mv2-test-rules-ed2-")
        with open(os.path.join(dd, "tiers.json"), "w", encoding="utf-8") as f:
            json.dump({"c4A58": {"status": "UNKNOWN", "classes": [[8, 1], [12, 5]]},
                       "c3A94": {"status": "INFEASIBLE"}}, f)
        src, rec = re_._decided_before("c3A94", [("11b", dd), ("11", "")])
        self.assertEqual((src, rec["status"]), ("11b", "INFEASIBLE"))
        self.assertEqual(re_._decided_before("c4A58", [("11b", dd)]), (None, None))
        self.assertEqual(re_._old_classes("c4A58", [("11b", dd)]), {(8, 1), (12, 5)})


if __name__ == "__main__":
    unittest.main()
