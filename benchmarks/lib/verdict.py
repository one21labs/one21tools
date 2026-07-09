#!/usr/bin/env python3
"""Shared KEEP/HARMFUL/CUT-CANDIDATE/INCONCLUSIVE verdict rule (ADR 0024), one home instead of the
duplicate verbatim in each harness's aggregate.py (github-code-quality finding, #57; dedup tracked
on #43).
"""


def verdict_of(mean, lo, hi, n):
    if n and lo > 0:
        return "KEEP"
    if n and hi < 0:
        return "HARMFUL"
    # guards above return unless the CI straddles 0, so lo <= 0 <= hi holds here
    if n and abs(mean) < 0.05:
        return "CUT-CANDIDATE"
    return "INCONCLUSIVE"
