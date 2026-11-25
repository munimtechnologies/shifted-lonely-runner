# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Tests for slr_chain.py (route 7). Standard library only; about ten seconds."""
import os
import tempfile
import unittest

import slr_chain as C


class Encoding(unittest.TestCase):
    def test_width(self):
        self.assertEqual(C.width_for(10 ** 6), 4)   # 36^3 = 46656 < 10^6 <= 36^4 = 1679616
        self.assertEqual(C.width_for(10 ** 8), 6)   # 36^5 = 60466176 < 10^8
        self.assertEqual(C.width_for(36), 1)

    def test_roundtrip(self):
        for den in (10 ** 6, 10 ** 8, 7):
            nums = [0, 1, den - 1, den // 2, den // 3]
            text = C.encode_shifts(nums, den)
            self.assertEqual(len(text), C.width_for(den) * len(nums))
            self.assertEqual(C.decode_shifts(text, den, len(nums)), nums)

    def test_known_value(self):
        # 997019 = 21*36^3 + 13*36^2 + 10*36 + 35 -> "ldaz"
        self.assertEqual(21 * 36 ** 3 + 13 * 36 ** 2 + 10 * 36 + 35, 997019)
        self.assertEqual(C.encode_shifts([997019], 10 ** 6), "ldaz")

    def test_bad_input(self):
        with self.assertRaises(ValueError):
            C.encode_shifts([10 ** 6], 10 ** 6)
        with self.assertRaises(ValueError):
            C.decode_shifts("abc", 10 ** 6, 1)


class Certs(unittest.TestCase):
    def test_repo_cert(self):
        cs = C.read_certs(C.CERTS)
        self.assertEqual([c["n"] for c in cs], [55])
        self.assertTrue(C.exact_ok(cs[0], full=True))

    def test_cert_lines(self):
        c = C.read_certs(C.CERTS)[0]
        v, s = C.cert_lines(c)
        self.assertTrue(v.startswith("C55 V:1,44,25,"))
        enc = s.split("S36:")[1]
        self.assertEqual(C.decode_shifts(enc, 10 ** 6, 55), c["shift_num"])

    def test_state_and_base(self):
        c = C.read_certs(C.CERTS)[0]
        with tempfile.TemporaryDirectory() as d:
            st = os.path.join(d, "x", "certs.json")
            base, src = C.best_base([C.CERTS, st])         # state missing: repo cert
            self.assertEqual((base["n"], src), (55, C.CERTS))
            bad = {"n": 56, "speeds": c["speeds"] + [1], "shift_den": c["shift_den"],
                   "shift_num": c["shift_num"] + [0]}     # repeated speed: never valid
            self.assertFalse(C.exact_ok(bad))
            self.assertTrue(C.save_state(bad, st))
            self.assertTrue(C.save_state(c, st))
            self.assertEqual(sorted(x["n"] for x in C.read_certs(st)), [55, 56])
            base, src = C.best_base([C.CERTS, st])         # invalid n = 56 is skipped
            self.assertEqual(base["n"], 55)
            rep = C.show([55, 56, 57], state=st)
            self.assertIn("n=56 FAILS exact check", rep)
            self.assertIn("n=57 missing", rep)
            self.assertIn("C55 V:", rep)


class Worker(unittest.TestCase):
    def test_worker_smoke(self):
        task = {"n": 6, "base_speeds": [1, 2, 3, 4, 5], "base_shifts": [0.0, 0.1, 0.2, 0.3, 0.4],
                "add": [6], "seed": 7, "seconds": 3.0, "vmax": 20, "pool": None, "g_stop": 0.0}
        r = C.worker(task)
        self.assertEqual(len(r["speeds"]), 6)
        self.assertEqual(len(set(r["speeds"])), 6)
        self.assertLessEqual(r["E0"], r["E"] + 1e-9)    # the loneliness never goes up
        res, mode = C.run_workers([task], 1)
        self.assertEqual(mode, "serial")
        self.assertEqual(len(res), 1)


if __name__ == "__main__":
    unittest.main()
