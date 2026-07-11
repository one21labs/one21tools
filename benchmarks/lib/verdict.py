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


def merge_verdict(mean_diff, ci_lo, ci_hi, n, chars_delta):
    """ADR 0027's amended merge bar for a with-new-vs-with-old re-measure, WITH the cost prong
    (issue #142): PRIMARY `mean_diff > 0` -> directional MERGE, else NO MERGE. When the CI excludes
    0 (`ci_lo > 0`), confidence is "strong" and the merge stands regardless of cost. When the CI
    straddles 0 ("weak"), the merge is CONTINGENT on the cost prong (ADR 0024 step 2d,
    always-loaded/body chars only — not the full reference-inclusive treatment, ADR 0027 decision
    3): `chars_delta <= 0` (cost flat or down) keeps the weak merge; `chars_delta > 0` (benefit flat
    while always-loaded chars rise) reverts to NO MERGE. Without this prong, `aggregate.py` printed
    "MERGE (weak)" for `benchmarks/2026-07-09-bs-iter2-remeasure/` (+0.002 mean, CI
    [-0.137, +0.140], +187 always-loaded chars) where the settled bar says NO MERGE.

    Returns (merge: bool, confidence: "strong" | "weak" | None).
    """
    if not n or mean_diff <= 0:
        return False, None
    if ci_lo > 0:
        return True, "strong"
    if chars_delta > 0:
        return False, None
    return True, "weak"
