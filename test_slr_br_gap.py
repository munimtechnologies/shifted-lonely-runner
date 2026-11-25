# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Open cases of the shifted Lonely Runner Conjecture: n = 18, 19, 20 with speeds 1..n.

Each test runs the deterministic search of slr_br.py (seed 1) and passes only if it returns
shifts whose closed bad sets at radius R = 1/(n+1) - 1/10^11 cover the circle, re-checked in
exact rational arithmetic on the exact binary values of the float shifts. A pass is therefore
a reproducible certificate: rerunning `slr_br.certify_consecutive(n, seed=1, max_sweeps=60000)`
without a time limit returns the same shifts. See PREREG_br.md (written before the first run).
"""
import unittest
from fractions import Fraction as F

import slr_br

SECONDS = 150


class OpenCases(unittest.TestCase):
    def _case(self, n):
        cert, st = slr_br.certify_consecutive(n, seed=1, max_sweeps=60000, seconds=SECONDS)
        print("n=%d %r" % (n, st), flush=True)
        if cert is not None:
            print("n=%d shifts %s" % (n, ",".join(cert["shifts_float"])), flush=True)
        self.assertIsNotNone(cert, "n=%d not found: %r" % (n, st))
        self.assertLess(F(cert["radius"]), F(1, n + 1))
        self.assertTrue(slr_br.exact_cover(cert["speeds"], [F(x) for x in cert["shifts"]],
                                           F(cert["radius"])))

    def test_n18(self):
        self._case(18)

    def test_n19(self):
        self._case(19)

    def test_n20(self):
        self._case(20)


if __name__ == "__main__":
    unittest.main()
