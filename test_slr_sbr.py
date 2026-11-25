# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Tests for route 5 (slr_sbr.py). Standard library only; about two minutes at most."""
import json
import os
import random
import tempfile
import time
import unittest
from fractions import Fraction as F

import slr
import slr_br
import slr_sbr


def measure(gaps):
    return sum(b - a for a, b in gaps)


class Moves(unittest.TestCase):
    def test_best_move_never_worse_and_measure_is_real(self):
        rng = random.Random(5)
        checked = 0
        for _ in range(40):
            n = 10
            speeds = rng.sample(range(1, 31), n)
            shifts = [rng.random() for _ in range(n)]
            r = 0.035
            ivs = [slr_sbr.runner_iv(v, s, r) for v, s in zip(speeds, shifts)]
            k = rng.randrange(n)
            g = slr_sbr.gaps_except(ivs, k)
            if not g:
                continue
            u, s, m, m_same = slr_sbr.best_move(k, speeds, g, r, rng, 40, 1.0, 30)
            self.assertGreaterEqual(m, m_same - 1e-12)
            self.assertTrue(u == speeds[k] or u not in speeds)
            others = [iv for j, lst in enumerate(ivs) if j != k for iv in lst]
            after = slr_br.gaps_of(others + slr_sbr.runner_iv(u, s, r))
            self.assertAlmostEqual(measure(g) - measure(after), m, delta=1e-9)
            checked += 1
        self.assertGreater(checked, 10)

    def test_add_runner_distinct(self):
        rng = random.Random(3)
        speeds = list(range(1, 9))
        shifts = [rng.random() for _ in speeds]
        sp, sh = slr_sbr.add_runner(speeds, shifts, 0.05, rng, 30)
        self.assertEqual(len(sp), 9)
        self.assertEqual(len(set(sp)), 9)
        self.assertEqual(sp[:8], speeds)
        self.assertTrue(1 <= sp[8] <= 30)


class Certify(unittest.TestCase):
    def test_dirichlet_is_not_a_certificate(self):
        # speeds 1..6 with zero shifts cover at exactly 1/7 and at no smaller radius
        self.assertIsNone(slr_sbr.certify(list(range(1, 7)), [0.0] * 6))

    def test_repeated_speed_rejected(self):
        self.assertIsNone(slr_sbr.certify([1, 1, 2], [0.0, 0.5, 0.25]))

    def _search(self, p_speed, seed):
        rng = random.Random(seed)
        speeds = list(range(1, 9))
        shifts = [rng.random() for _ in speeds]
        best, st = slr_sbr.sbr_search(speeds, shifts, 0.2, slr_sbr.TARGET / 9, rng,
                                      time.time() + 60, 24, p_speed=p_speed, n_cand=10)
        self.assertIsNotNone(best, st)
        self.assertLessEqual(best[0], slr_sbr.TARGET / 9)
        cert = slr_sbr.certify(best[1], best[2])
        self.assertIsNotNone(cert)
        ex = [F(k, cert["shift_den"]) for k in cert["shift_num"]]
        self.assertTrue(slr.covers_sweep(cert["speeds"], ex, F(1, 9))[0])
        self.assertTrue(slr.covers_endpoints(cert["speeds"], ex, F(1, 9))[0])
        self.assertEqual(len(set(cert["speeds"])), 8)
        return cert

    def test_n8_shifts_only(self):
        # gamma_sh(1..8) = 1/10 < 0.999/9 (Blanco-Criado-Santos), so such shifts exist
        cert = self._search(0.0, 1)
        self.assertEqual(sorted(cert["speeds"]), list(range(1, 9)))

    def test_n8_with_speed_moves(self):
        cert = self._search(0.5, 2)
        self.assertTrue(all(1 <= v <= 24 for v in cert["speeds"]))


class External(unittest.TestCase):
    def test_load_local_file(self):
        data = [{"n": 3, "speeds": [1, 2, 3], "shift_num": [0, 1, 2], "shift_den": 5,
                 "gamma": "1/5"}]
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "c.json")
            with open(p, "w") as fh:
                json.dump(data, fh)
            certs, sha = slr_sbr.load_external(p)
        self.assertEqual(set(certs), {3})
        self.assertEqual(certs[3]["shifts"], [F(0), F(1, 5), F(2, 5)])
        self.assertEqual(certs[3]["gamma"], F(1, 5))
        self.assertEqual(len(sha), 64)

    def test_verify_rejects_dirichlet(self):
        # (1..4) with zero shifts: gamma = 1/5 exactly, not < 1/5
        certs = {4: {"n": 4, "speeds": [1, 2, 3, 4], "shifts": [F(0)] * 4, "gamma": F(1, 5)}}
        (row,) = slr_sbr.verify_external(certs)
        self.assertEqual(row, (4, False, False, False, True))


if __name__ == "__main__":
    unittest.main()
