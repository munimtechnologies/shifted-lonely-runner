# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""A third n = 63 cover, found from scratch by route 19d's sanity tier r64 (gate probe R1,
2026-11-28 00:42 UTC; RESULTS_rules_r.md). n = 63 is Xavier Callens's case (Zenodo 24051700);
this is another certificate, not a new case.

On the base 2, 4, ..., 128 at shift 0 (N = 64, delta = 1/65): remove 8, 32, 72, 96 (4); rephase
12, 24, 36 to 1/2 - delta/2, 48 to 1/2 + delta/2, 16 and 128 to +delta, 64 to -delta (7); add 3 at
3/4 - delta/2 and 9, 27 at 3/4 (3). Gain 4 - 3 = 1, so 64 - 1 = 63 runners."""
import unittest
from fractions import Fraction as F

import rules_m
import top_o as to
import top_q as tq
import top_r as tr

H = F(1, 2)
Q34 = F(3, 4)

RULE_R64 = {
    "m": 2,
    "removed": [8, 32, 72, 96],
    "rephased": {12: (H, -H), 16: (F(0), F(1)), 24: (H, -H), 36: (H, -H), 48: (H, H),
                 64: (F(0), F(-1)), 128: (F(0), F(1))},
    "added": {3: (Q34, -H), 9: (Q34, F(0)), 27: (Q34, F(0))},
}


class TestCoverR64(unittest.TestCase):
    def test_shape(self):
        self.assertEqual(rules_m.gain(RULE_R64), 1)
        v, _s, _d, k = rules_m.build_config(RULE_R64, 64)
        # 64 base speeds - 4 removed + 3 added = 63 distinct runners
        self.assertEqual(k, 63)
        self.assertEqual(len(set(v)), 63)
        # every touched speed is 3-smooth
        touched = set(RULE_R64["removed"]) | set(RULE_R64["rephased"]) | set(RULE_R64["added"])
        self.assertEqual(len(touched), 14)
        for w in touched:
            x = w
            for p in (2, 3):
                while x % p == 0:
                    x //= p
            self.assertEqual(x, 1, w)

    def test_fixed_n_criterion(self):
        self.assertTrue(to.fixed_check(RULE_R64, 64, g=1)[0])

    def test_three_global_checkers(self):
        c = tq.full_cert(RULE_R64, 64, 63)
        self.assertTrue(c["sweep"])
        self.assertTrue(c["endpoints"])
        self.assertTrue(c["indep"])
        self.assertTrue(c["distinct"])
        self.assertTrue(c["ok"])
        self.assertEqual(c["R"], "1/64")

    def test_falsifies_no_clause(self):
        # the clause generator must be sound on this cover too (PREREG_rules_r.md)
        self.assertEqual(tr.violations(RULE_R64, 64, 1, to.P3), [])
        self.assertEqual(tr.violations(RULE_R64, 64, 1, to.P5), [])


if __name__ == "__main__":
    unittest.main()
