# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Standard-library tests for route 13b (rule_search_h.py, PREREG_rules_h.md). No PySAT: the
CNF encoding is checked against brute force with a small DPLL written here."""
import itertools
import random
import unittest
from fractions import Fraction as F

import rule_search_g as rg
import rule_search_h as rh
import slr


def dpll(clauses, nv):
    """Tiny complete SAT check (unit propagation + branching)."""
    def solve(assign):
        changed = True
        while changed:
            changed = False
            for c in clauses:
                free = []
                sat = False
                for l in c:
                    v = assign.get(abs(l))
                    if v is None:
                        free.append(l)
                    elif v == (l > 0):
                        sat = True
                        break
                if sat:
                    continue
                if not free:
                    return False
                if len(free) == 1:
                    assign[abs(free[0])] = free[0] > 0
                    changed = True
        for v in range(1, nv + 1):
            if v not in assign:
                for val in (False, True):
                    a2 = dict(assign)
                    a2[v] = val
                    if solve(a2):
                        return True
                return False
        return True
    return solve({})


class _Box:
    def __init__(self):
        self.nv = 0
        self.cls = []

    def new(self):
        self.nv += 1
        return self.nv


class TestCounter(unittest.TestCase):
    def test_least_fixpoint_is_exact_count(self):
        rng = random.Random(1)
        for k in range(1, 8):
            for cap in range(1, k + 2):
                box = _Box()
                lits = [box.new() for _ in range(k)]
                outs = rh.counter(lits, cap, box)
                self.assertEqual(len(outs), cap)
                for _ in range(20):
                    on = set(x for x in lits if rng.random() < 0.5)
                    pos = set(on)
                    changed = True
                    while changed:
                        changed = False
                        for c in box.cls:
                            if any((l > 0 and l in pos) or (l < 0 and -l not in pos) for l in c):
                                continue
                            aux = [l for l in c if l > 0 and l not in lits]
                            self.assertEqual(len(aux), 1)
                            pos.add(aux[0])
                            changed = True
                    for j in range(cap):
                        want = len(on) >= j + 1
                        got = outs[j] is not None and outs[j] in pos
                        self.assertEqual(want, got, (k, cap, j, len(on)))

    def test_negated_inputs(self):
        box = _Box()
        xs = [box.new() for _ in range(4)]
        outs = rh.counter([-x for x in xs], 4, box)
        # all four false -> count 4 -> outs[3] forced: clauses + "outs[3] false" + all x false
        cls = box.cls + [[-outs[3]]] + [[-x] for x in xs]
        self.assertFalse(dpll(cls, box.nv))
        cls = box.cls + [[-outs[3]]] + [[-x] for x in xs[:3]]
        self.assertTrue(dpll(cls, box.nv))


class TestGainEncoding(unittest.TestCase):
    def brute(self, touch, added, clauses, need, menus_t, menus_a):
        opts_t = [["rem", "unt"] + ["e:%d:%d" % (w, S) for S in menus_t[w]] for w in touch]
        opts_a = [[None] + ["o:%d:%d" % (a, S) for S in menus_a[a]] for a in added]
        for ct in itertools.product(*opts_t):
            for ca in itertools.product(*opts_a):
                lits = set()
                rem = 0
                for w, c in zip(touch, ct):
                    if c == "rem":
                        rem += 1
                    elif c == "unt":
                        lits.add("u:%d" % w)
                    else:
                        lits.add(c)
                nadd = sum(1 for c in ca if c is not None)
                lits.update(c for c in ca if c is not None)
                if rem - nadd >= need and all(lits.intersection(k) for k in clauses):
                    return True
        return False

    def test_random_small_instances_match_brute_force(self):
        rng = random.Random(7)
        touch, added = [2, 4, 6], [1, 3]
        menus_t = {w: [5, 7] for w in touch}
        menus_a = {a: [0, 9] for a in added}
        keys = (["u:%d" % w for w in touch] +
                ["e:%d:%d" % (w, S) for w in touch for S in menus_t[w]] +
                ["o:%d:%d" % (a, S) for a in added for S in menus_a[a]])
        seen = {True: 0, False: 0}
        for trial in range(140):
            need = rng.choice([0, 1, 1, 2])
            clauses = [sorted(rng.sample(keys, rng.randrange(1, 4)))
                       for _ in range(rng.randrange(1, 6))]
            enc = rh.Enc(touch, added, need)
            for c in clauses:
                enc.clause(c)
            got = dpll(enc.cls, enc.nv)
            want = self.brute(touch, added, clauses, need, menus_t, menus_a)
            self.assertEqual(got, want, (trial, need, clauses))
            seen[want] += 1
        self.assertGreater(seen[True], 10)
        self.assertGreater(seen[False], 10)

    def test_gain_violation_detected(self):
        enc = rh.Enc([2, 4, 6], [1, 3], 1)
        pos = enc.assignment_of({"removed": [], "rephased": {}, "added": {}})
        self.assertIsNotNone(enc.satisfied(pos))
        pos = enc.assignment_of({"removed": [2], "rephased": {}, "added": {}})
        self.assertIsNone(enc.satisfied(pos))


class TestPoliakovaInEncoding(unittest.TestCase):
    def test_poliakova_satisfies_seed_encoding(self):
        m, n, N, P, _h, _e = rh.TIERS_H["g2H"]
        touch, fixed, added = rg.pools_g(m, N, P)
        Md, shifts = rg.shift_menu(N)
        enc = rh.Enc(touch, added, N - n)
        pts = rg.seed_points(m, n, N, touch)
        k = 0
        for t in pts:
            for x in (t, (-t) % 1):
                c = rg.point_clause(x, n, touch, fixed, added, Md, shifts)
                if c is not None:
                    enc.clause(c)
                    k += 1
        self.assertGreater(k, 100)
        cand = rg.poliakova_cand(N)
        for key in sorted(rg.lits_of(cand, touch)):  # as cegar_h does for its hint
            enc.var(key)
        pos = enc.assignment_of(cand)
        self.assertIsNone(enc.satisfied(pos))
        back = enc.decode(pos)
        self.assertEqual(sorted(back["removed"]), sorted(cand["removed"]))
        self.assertEqual(back["rephased"], cand["rephased"])
        self.assertEqual(back["added"], cand["added"])
        # the decoded candidate never has more runners than n
        v, _s = rg.config_of(back, m, N, Md)
        self.assertLessEqual(len(v), n)

    def test_broken_rule_violates_its_gap_clause(self):
        m, n, N, P, _h, _e = rh.TIERS_H["g2H"]
        touch, fixed, added = rg.pools_g(m, N, P)
        Md, shifts = rg.shift_menu(N)
        cand = {"removed": [8, 32, 192], "rephased": {}, "added": {}}
        v, s = rg.config_of(cand, m, N, Md)
        ok, x = slr.covers_sweep(v, s, F(1, n + 1))
        self.assertFalse(ok)
        enc = rh.Enc(touch, added, N - n)
        enc.clause(rg.point_clause(F(x) % 1, n, touch, fixed, added, Md, shifts))
        self.assertIsNotNone(enc.satisfied(enc.assignment_of(cand)))

    def test_mirror_clause_is_necessary(self):
        # Poliakova's cover is symmetric enough that it covers -t too: every mirror clause of a
        # gap point of a broken rule is satisfied by the true cover
        m, n, N, P, _h, _e = rh.TIERS_H["g2H"]
        touch, fixed, added = rg.pools_g(m, N, P)
        Md, shifts = rg.shift_menu(N)
        good = rg.lits_of(rg.poliakova_cand(N), touch)
        bad = {"removed": [8, 32, 192, 64], "rephased": {}, "added": {3: 291}}
        v, s = rg.config_of(bad, m, N, Md)
        gaps, _t = rg.float_scan(v, s, 1.0 / (n + 1))
        pts = rg.gap_points(gaps, 40)
        self.assertTrue(pts)
        for x in pts:
            for y in (x, (-x) % 1):
                c = rg.point_clause(y, n, touch, fixed, added, Md, shifts)
                if c is not None:
                    self.assertTrue(good.intersection(c), str(y))


class TestTiers(unittest.TestCase):
    def test_tiers(self):
        for tag in rh.ORDER_H:
            m, n, N, P, _h, _e = rh.TIERS_H[tag]
            self.assertLessEqual(n, 95)
            self.assertGreaterEqual(N - n, 1)
            touch, _f, added = rg.pools_g(m, N, P)
            self.assertTrue(touch and added)
        self.assertEqual(rh.TIERS_H["g6N"], rg.TIERS_G["g6N"])

    def test_line_format(self):
        r = {"m": 6, "n": 94, "N": 95, "status": "UNKNOWN", "iterations_total": 3,
             "n_clauses": 10, "literals": 99, "best_unc": 1.5e-4, "src": "g10",
             "solver": "cadical195", "seconds_total": 12.3}
        line = rh._line("g6N", r)
        self.assertIn("st=UNKNOWN", line)
        self.assertIn("best=1.50e-04", line)


if __name__ == "__main__":
    unittest.main()
