#!/usr/bin/env python3
"""Pre-registration guard: the prevent rung for self-favouring experiment designs.

WHY THIS EXISTS (owner direction, 26-Jul-2026: "Find a way to poke yoke hedging and reward
hacking"). An agent designing a measurement against its own artifact produces designs that cannot
falsify it and does not notice -- four instances in one session, none caught by the author, all
caught by a foreign-family reviewer. The doctrine and the recorded instances live in
`skills/bench/references/evaluating-your-own-work.md`; this file is the executable half, because
ADR 0083 already established that a vigilance rule alone does not hold (task focus narrows past
it) and ADR 0047 puts prevention above detection.

It checks the two failures that are DECIDABLE from the design alone -- no judgement, no prose
analysis:

  1. UNREACHABLE THRESHOLD. A design that states an equivalence/indifference margin, a cluster
     count, and a variance estimate has a computable CI half-width. If the half-width exceeds the
     margin, no run can ever conclude equivalence: the branch is decoration. Decoration is never
     neutral -- in the recorded instance the unreachable branch awarded ties to the author's own
     arm.
  2. UNFALSIFIABLE ARM. If the design declares that the author wrote an arm, some pre-registered
     outcome must be a LOSS for that arm. A design whose every branch preserves the author's
     artifact is not a measurement.

Pure functions, stdlib only, so the decision logic is testable offline (CLAUDE.md: never ship a
process-gating script without a test of its decision logic).
"""
import math

# Two-sided 95% t critical values by df. Same table and reasoning as benchstats.t95 -- at the
# cluster counts these designs use, the normal approximation understates the interval by 31-62%,
# which would make thresholds look reachable when they are not. Duplicated rather than imported
# because ADR 0050 keeps plugin content dependency-free; the parity risk is one constant table.
_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306,
        9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
        16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086, 25: 2.060, 30: 2.042}


def t95(df):
    if df < 1:
        return float("nan")
    return _T95.get(df, 1.96)


def half_width(clusters, sd):
    """95% CI half-width for a cluster-mean contrast: t(df=G-1) * sd / sqrt(G)."""
    if clusters < 2:
        return float("inf")
    return t95(clusters - 1) * sd / math.sqrt(clusters)


def clusters_needed(margin, sd, cap=500):
    """Smallest G whose half-width fits inside `margin` -- the honest cost of the stated claim."""
    g = 2
    while g <= cap and half_width(g, sd) >= margin:
        g += 1
    return g if g <= cap else None


def check(design):
    """`design` is a dict describing the pre-registration:
        clusters:int, sd_hi:float           -- power inputs (sd_hi = the conservative estimate)
        equivalence_margin:float|None       -- the indifference/tie threshold, if any
        author_arms:list[str]               -- arms the design's author wrote
        losing_outcomes:list[str]           -- arms that at least one outcome branch records as
                                               losing
    Returns a list of problem strings; empty means the design clears both mechanical checks.
    Neither check can pass a design by being silent: an absent field is a failure, because the
    common way to dodge this guard is to omit the number.
    """
    problems = []
    g, sd = design.get("clusters"), design.get("sd_hi")
    if not g or not sd:
        problems.append("prereg: no clusters/sd_hi — power is unstated, so no threshold in this "
                        "design can be shown reachable. State both.")
    margin = design.get("equivalence_margin")
    if margin is not None and g and sd:
        hw = half_width(g, sd)
        if hw >= margin:
            need = clusters_needed(margin, sd)
            problems.append(
                f"prereg: equivalence margin {margin} is UNREACHABLE at {g} clusters — the 95% CI "
                f"half-width is {hw:.3f}, so the branch can never fire. It would need "
                f"{need if need else '>500'} clusters. Remove the branch or resize the design; do "
                f"not widen the margin to fit, which just moves the decoration "
                f"(evaluating-your-own-work.md).")
    authored = design.get("author_arms")
    if authored is None:
        problems.append("prereg: author_arms unstated — say which arms the design's author wrote, "
                        "or [] if none. Omission is the cheapest way past this check.")
    else:
        losing = set(design.get("losing_outcomes") or [])
        unfalsifiable = [a for a in authored if a not in losing]
        if unfalsifiable:
            problems.append(
                f"prereg: {', '.join(unfalsifiable)} — the author wrote this arm and NO "
                f"pre-registered outcome records it losing. Add an outcome branch where it loses "
                f"and say what that triggers, or the design cannot falsify its author's work "
                f"(evaluating-your-own-work.md).")
    return problems
