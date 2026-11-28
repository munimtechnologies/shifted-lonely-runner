# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. (MV2, mv2@munimtech.com). Made with AI agents working in MV2's name.
"""Stand-alone exact checker for shifted Lonely Runner certificates (standard library only).

A certificate is a list of runners (v_i, s_i) with distinct positive integer speeds v_i and
rational shifts s_i, and a radius R. It shows that the shifted Lonely Runner Conjecture fails
for n runners when the open arcs

    A_i = {t in R/Z : ||v_i t + s_i|| < R}

cover the whole circle and R <= 1/(n+1): then at every time t some runner is closer than
1/(n+1) to the origin.

Method (written fresh for the n = 79 certificate; it shares no code with slr.py or top_q.py).
On the real line, runner i is closer than R to the integer j exactly for t in the open interval
((j - s_i - R)/v_i, (j - s_i + R)/v_i). With s_i reduced to [0, 1) and t in [0, 1], v_i t + s_i
lies in [0, v_i + 1), so j = -1, ..., v_i + 1 lists every interval that meets [0, 1]. The circle
is covered iff [0, 1] is covered (t and t + 1 are the same time). Sweep: keep c with [0, c)
covered (start c = 0); among the intervals with left end < c take the largest right end b; if
b <= c the point c lies in no interval (every interval containing c has left end < c and right
end > c), so c is uncovered; otherwise [0, b) is covered and c := b. Stop when c > 1.
Every number is a Fraction, so the answer is exact.
"""
import json
import sys
from fractions import Fraction as F


def intervals(speeds, shifts, R):
    """Open intervals (a, b) of times in which some runner is closer than R to an integer,
    every interval that meets [0, 1]."""
    R = F(R)
    out = []
    for v, s in zip(speeds, shifts):
        s = F(s) % 1
        for j in range(-1, v + 2):
            a = (j - s - R) / v
            b = (j - s + R) / v
            if b > 0 and a < 1:
                out.append((a, b))
    out.sort()
    return out


def first_gap(speeds, shifts, R):
    """None if the open arcs of radius R cover the circle, else a time t in [0, 1] that no
    runner covers (exact)."""
    if not 0 < F(R) < F(1, 2):
        raise ValueError("need 0 < R < 1/2")
    ivs = intervals(speeds, shifts, R)
    c = F(0)
    best = None
    i = 0
    while c <= 1:
        while i < len(ivs) and ivs[i][0] < c:
            if best is None or ivs[i][1] > best:
                best = ivs[i][1]
            i += 1
        if best is None or best <= c:
            return c
        c = best
    return None


def covers(speeds, shifts, R):
    return first_gap(speeds, shifts, R) is None


def check_certificate(cert):
    """Return a dict of exact facts about a certificate dict with keys runners, n, R."""
    v = [int(x) for x, _ in cert["runners"]]
    s = [F(y) for _, y in cert["runners"]]
    n = int(cert["n"])
    R = F(cert["R"])
    gap = first_gap(v, s, R)
    facts = {
        "runners": len(v),
        "distinct": len(set(v)) == len(v),
        "positive_integers": all(x >= 1 for x in v),
        "n_matches": len(v) == n,
        "R_ok": R <= F(1, n + 1),
        "covers": gap is None,
        "gap": None if gap is None else str(gap),
    }
    facts["counterexample"] = all(facts[k] for k in
                                  ("distinct", "positive_integers", "n_matches", "R_ok", "covers"))
    return facts


def main(argv):
    path = argv[1] if len(argv) > 1 else "cover_n079.json"
    with open(path, encoding="utf-8") as f:
        cert = json.load(f)
    facts = check_certificate(cert)
    for k, val in facts.items():
        print("%s: %s" % (k, val))
    print("COUNTEREXAMPLE n=%s" % cert["n"] if facts["counterexample"] else "NOT A CERTIFICATE")
    return 0 if facts["counterexample"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
