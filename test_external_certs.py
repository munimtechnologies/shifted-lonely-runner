# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Independent exact check of the published shifted Lonely Runner certificates for 18 <= n <= 54.

Source: results/shifted-lonely-runner-counterexamples/certificates.json in
github.com/1337isnot1337/solved-conjectures (by aadrianvv, merged 2026-11-22, MIT licence of that
repository). The file is downloaded, not copied here. Each certificate must have n distinct
positive speeds, recorded gamma < 1/(n+1), and pass three exact checks written by MV2 before
the file was seen: slr.covers_sweep and slr.covers_endpoints (the open arcs of radius 1/(n+1)
cover the circle, so gamma(v; s) < 1/(n+1)) and slr_br.exact_cover at the recorded gamma
(closed arcs, so gamma(v; s) <= recorded gamma). Needs network access.
"""
import unittest

import slr_sbr


class PublishedCertificates(unittest.TestCase):
    def test_all_18_to_54(self):
        certs, sha = slr_sbr.load_external()
        self.assertEqual(sorted(certs), list(range(18, 55)), sha)
        bad = [row for row in slr_sbr.verify_external(certs) if not all(row[1:])]
        self.assertEqual(bad, [], "sha256 %s" % sha)


if __name__ == "__main__":
    unittest.main()
