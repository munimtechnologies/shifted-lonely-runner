# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Tests for route 9 (slr_consec.py). Standard library only; about a minute."""
import os
import tempfile
import unittest
from fractions import Fraction as F

import slr_br
import slr_chain
import slr_consec as C


class Basics(unittest.TestCase):
    def test_grid_size(self):
        for n in (5, 11, 30, 56, 94):
            G = C.grid_size(n)
            self.assertGreaterEqual(G, 300 * n * n)
            self.assertEqual(G & (G - 1), 0)
            self.assertLess(G, 600 * n * n + 8192)

    def test_zero_shifts_are_not_a_counterexample(self):
        # speeds 1..6 at shift 0: at t = 1/7 every runner is at distance >= 1/7, so the
        # loneliness is exactly 1/7 and nothing below 1/7 may be certified
        self.assertIsNone(C.certify_consec(6, [0.0] * 6))
        self.assertFalse(slr_br.exact_cover(list(range(1, 7)), [F(0)] * 6,
                                            F(1, 7) - F(1, 10 ** 9)))

    def test_state_roundtrip_keeps_the_better_E(self):
        path = os.path.join(tempfile.mkdtemp(), "s.json")
        c = {"n": 3, "speeds": [1, 2, 3], "shift_den": 10, "shift_num": [0, 1, 2]}
        self.assertTrue(C.save_state(c, 0.5, path))
        self.assertTrue(C.save_state(dict(c, shift_num=[0, 3, 4]), 0.2, path))
        got = C.load_state(path)
        self.assertEqual(sorted(got), [3])
        self.assertEqual(got[3][0]["shift_num"], [0, 1, 2])
        self.assertEqual(got[3][0]["speeds"], [1, 2, 3])
        self.assertAlmostEqual(got[3][1], 0.5)
        self.assertEqual(C.load_state(path + ".missing"), {})


class Search(unittest.TestCase):
    def test_worker_adds_runner_and_any_cert_is_exact(self):
        r = C.worker({"n": 6, "shifts": [0.0, 0.3, 0.6, 0.1, 0.8], "seed": 2, "seconds": 10,
                      "e_stop": 9.0, "e_prev": 0.0, "G": 1 << 13, "reserve": 2.0,
                      "polish0": 2.0})
        self.assertEqual(r["n"], 6)
        self.assertEqual(len(r["shifts"]), 6)
        self.assertGreaterEqual(r["E"], r["E0"])
        self.assertLess(r["E"], 6.0)  # E_n <= n - 1 (Poliakova)
        cert = C.certify_consec(6, r["shifts"]) if r["E"] > 0 else None
        if cert is not None:
            self.assertTrue(slr_chain.exact_ok(cert, full=True))

    def test_chain_runs_serial_and_saves_only_exact_certificates(self):
        path = os.path.join(tempfile.mkdtemp(), "consec.json")
        rep = C.chain(seconds=45, workers=1, seed=1, e_stop=0.3, step_max=12, state=path)
        self.assertIn("CONSEC top=", rep)
        self.assertTrue(rep.startswith("consec seed=1"))
        for n, (cert, E) in C.load_state(path).items():
            self.assertEqual(cert["speeds"], list(range(1, n + 1)))
            self.assertTrue(slr_chain.exact_ok(cert, full=True))
            self.assertGreater(E, 0)


if __name__ == "__main__":
    unittest.main()
