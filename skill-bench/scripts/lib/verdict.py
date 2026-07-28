#!/usr/bin/env python3
"""FROZEN 2026-07-27 — the HISTORICAL verdict rule. Do not use it for new work.

Eleven dated aggregators under `benchmarks/2026-07-*` import `verdict_of`, and those dirs are
append-only records (ADR 0041): the frozen literal IS the record, so changing this function would
make a re-run disagree with what was published. It therefore stays exactly as it was.

New work uses `benchstats.keep_verdict`, which is the rule the owner asked for on 2026-07-27:
significance from the interval, a pre-registered practical bar, a win rate, and CUT only on an
equivalence result. `verdict_of` fails that bar in one specific way a cross-family review named:
its `abs(mean) < 0.05` branch returns CUT-CANDIDATE when the interval is wide, announcing a small
effect on data that support no effect size at all. The 0.05 is an arbitrary constant, never
pre-registered, doing no inferential work.

No published verdict changes under the new rule except one: `2026-07-17-thirdparty-writing-plans`
cek-bare, recorded CUT-CANDIDATE at mean -0.014 with CI [-0.082, +0.055], is INCONCLUSIVE — that
design could only call a difference of 0.069 or larger. The dated README stays as written
(append-only); this is the recomputation of record.
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
