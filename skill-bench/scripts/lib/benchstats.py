#!/usr/bin/env python3
"""Verdict math + judge-divergence diagnostics for skill-bench (ADR 0019/0025 shape). Stdlib only.

Pure functions, fully unit-testable offline. `cells` everywhere is a list of dicts:
  {"bid","arm","scenario","met":{<expectation id>: bool}}
`met` arity is variable (fraction_met, clustered_delta); per_expectation and divergence assume
the fixed 4-expectation decision rubric (EXP_IDS) and KeyError on any other arity.
"""
import math, statistics
from collections import defaultdict

EXP_IDS = (1, 2, 3, 4)

# Two-sided 95% t critical values by degrees of freedom (df = clusters - 1). Every benchmark this
# repo has run clustered on 4-6 evals, where the normal approximation this replaced (a flat 1.96)
# understates the interval by 31-62% — at G=4 the correct multiplier is 3.182, not 1.96. Two
# recorded confidence labels were "strong" only because of that (see the ADR/issue for the
# recomputation; no recorded DECISION reversed). Small hard-coded table because the harness is
# stdlib-only by constraint; above df=30 the t and normal quantiles agree to ~2%.
_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306,
        9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
        16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086, 21: 2.080, 22: 2.074,
        23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045,
        30: 2.042}
Z95 = 1.96

# One-sided 80% t quantiles — the POWER term. Sizing uses the standard identity
# delta >= (t_{1-alpha/2} + t_{1-beta}) * SE; dropping the second term sizes for 50% power, which
# is the trap a cross-family review caught here on 2026-07-27: a design sized so that the true
# effect equals the half-width clears zero only about half the time.
_T80 = {1: 1.376, 2: 1.061, 3: 0.978, 4: 0.941, 5: 0.920, 6: 0.906, 7: 0.896, 8: 0.889,
        9: 0.883, 10: 0.879, 12: 0.873, 15: 0.866, 20: 0.860, 25: 0.856, 30: 0.854}
Z80 = 0.842


def t80(df):
    """One-sided 80% critical value at `df` — the power term in the sizing identity."""
    if df < 1:
        return float("nan")
    return _T80.get(df, Z80)


def t95(df):
    """Two-sided 95% critical value at `df` degrees of freedom. Exported so a consumer can show
    the multiplier its interval used; an interval whose width nobody can attribute is not a
    reported uncertainty. df < 1 has no interval (the caller returns NaN before reaching here)."""
    if df < 1:
        return float("nan")
    return _T95.get(df, Z95)


def fraction_met(met):
    """Arity-generic: fraction of this cell's expectations met. Works for the fixed 4-expectation
    decision rubric AND variable-length skill-eval rubrics (/bench-skill)."""
    return (sum(1 for v in met.values() if v) / len(met)) if met else 0.0


def arm_mean(cells, arm):
    v = [fraction_met(c["met"]) for c in cells if c["arm"] == arm]
    return statistics.mean(v) if v else float("nan")


def clustered_delta(cells, x, y):
    """Mean per-scenario (fraction_met[x] - fraction_met[y]), 95% CI over scenario clusters (ADR 0019)."""
    by = defaultdict(lambda: defaultdict(list))
    for c in cells:
        by[c["scenario"]][c["arm"]].append(fraction_met(c["met"]))
    deltas, per = [], {}
    for s in sorted(by):
        if by[s].get(x) and by[s].get(y):
            d = statistics.mean(by[s][x]) - statistics.mean(by[s][y])
            deltas.append(d); per[s] = d
    if not deltas:
        return {"mean": float("nan"), "ci95": [float("nan")] * 2, "per_scenario": {}, "n_clusters": 0}
    m = statistics.mean(deltas)
    se = (statistics.stdev(deltas) / math.sqrt(len(deltas))) if len(deltas) > 1 else float("nan")
    crit = t95(len(deltas) - 1)
    ci = [m - crit * se, m + crit * se] if se == se else [float("nan")] * 2
    return {"mean": m, "ci95": ci, "per_scenario": per, "n_clusters": len(deltas),
            # The multiplier is reported, not implied: at these cluster counts it is the single
            # largest determinant of whether a verdict reads "strong", and a reader who cannot see
            # it cannot tell a wide interval from a wrong one.
            "t_crit": crit}


def per_expectation(cells):
    out = {}
    for i in EXP_IDS:
        out[i] = {a: statistics.mean([c["met"][i] for c in cells if c["arm"] == a] or [float("nan")])
                  for a in sorted({c["arm"] for c in cells})}
    return out


def sd_between(delta):
    """Between-cluster SD implied by a COMPLETED run — the input `clusters_for` needs, recovered
    from the run itself so the next design is sized from a measured prior instead of a guess (ADR
    0076's derive-never-guess rule, applied to power). NaN when the run carries no interval."""
    lo, hi = delta["ci95"]
    g = delta["n_clusters"]
    if lo != lo or g < 2:
        return float("nan")
    return ((hi - lo) / 2 / t95(g - 1)) * math.sqrt(g)


def clusters_for(sd, target, power=0.80, max_g=4000):
    """Scenario clusters needed to call a TRUE difference of `target`, at `sd` between clusters,
    WITH the stated power. Iterative because both t multipliers depend on the answer. None means
    `max_g` is not enough — the honest result for a target this design cannot reach affordably.

    `power=0.80` is the default; `power=0.50` reproduces the naive sizing (target == half-width)
    and roughly HALVES the answer. Why 50% is not a design: `keep_verdict`'s docstring owns it.

    `sd` is a PLUG-IN estimate and usually comes from a G=6 run, where it carries df=5 — very
    noisy, and biased low when the realized spread happened to be small. Treat the result as a
    floor, not a plan: prefer an upper confidence bound on sd, or a conservative pre-registered
    value. A prior run on different scenarios or a different comparison class is not a draw from
    the same sd at all, which is the case that bites version-vs-version sizing.

    A pre-registration states this number (references/pre-registration.md). A grid sized below it
    can only return INCONCLUSIVE for the effect it is looking for — spend with a known-null
    outcome."""
    if power not in (0.50, 0.80):
        # Only two power levels have critical-value tables here, and a silently-honoured wrong
        # one is a mis-sized study in the function whose entire job is sizing: power=0.90 would
        # have been served 0.80's answer. Fail loud rather than generalize -- an arbitrary-beta
        # quantile table is machinery this has no measured need for.
        raise ValueError(f"power must be 0.50 or 0.80, got {power!r}. Only those two have "
                         f"critical values here; add a table before asking for another.")
    if sd != sd or sd <= 0 or target <= 0:
        return None
    for g in range(2, max_g + 1):
        crit = t95(g - 1) + (t80(g - 1) if power == 0.80 else 0.0)
        if crit * sd / math.sqrt(g) <= target:
            return g
    return None


def keep_verdict(delta, practical=0.0):
    """THE VERDICT IS THE INTERVAL, never the point estimate. KEEP iff the 95% CI clears the
    PRACTICAL threshold, HARMFUL iff it clears zero negative, INCONCLUSIVE otherwise.

    Verdicts: KEEP (clearly better), HARMFUL (clearly worse), CUT (equivalent to nothing, and
    only reachable with a practical bar set), INCONCLUSIVE (the data cannot tell you). There is no
    verdict meaning "probably a bit better" because no such claim is supportable.

    Three requirements, all from the owner, 2026-07-27 — a verdict must satisfy every one:
    (1) "within statistical significance" -> the interval decides, not the point estimate;
    (2) "the effect size to be significant, so that the skill is CLEARLY better" -> `practical`,
        the minimum difference worth having, tested against the interval's LOWER bound so KEEP
        means "at least this much, with 95% confidence" rather than "more than nothing";
    (3) "most of the time" -> `win_rate`, the share of scenarios the treatment actually won. A
        large mean carried by one scenario is not "clearly better most of the time", and the
        interval alone cannot tell you which you have. **`win_rate` carries NO inferential
        status** — over 6-8 scenarios it is a coin-flip count with no interval, so it is a
        prompt to look at `top_cell_attribution`, never a criterion. It deliberately has no
        threshold: a cross-family review pointed out that any cutoff here would be the same
        arbitrary constant this rule was written to delete.

    **`practical` is PRE-REGISTERED or it is worthless.** Set it before the run, in the
    pre-registration; picking it after seeing which way the numbers went is precisely the failure
    this whole audit exists to catch. Default 0.0 keeps the bar at bare significance, which is the
    weakest defensible setting, not the recommended one.

    Setting `practical > 0` raises the sample size needed: you must separate the true effect from
    the threshold, not from zero, so size with `clusters_for(sd, true_effect - practical)`.

    This restores ADR 0024 decision 1 ("CI excludes zero and positive means it is measurably
    earning its cost") and adds the practical bar 0024 never had.

    Two rules were deleted to get here, each of which a reviewer refuses:
    - KEEP on `mean > 0` alone (shipped here until 2026-07-27): under a true null a symmetric
      estimator is positive about half the time, so KEEP carried no error control at all. It cited
      "ADR 0052 bar"; 0052 defines no bar and its Enforced line names the competing rule.
    - CUT-CANDIDATE on `abs(mean) < 0.05` (verdict.py's floor): with a wide interval the data
      support no effect size, so naming a small one overclaims. The floor was an arbitrary
      constant doing no inferential work. A cross-family review named both defects independently.
    The `confidence` field went with them: under an interval rule a "weak KEEP" cannot exist.

    Two precision numbers, NOT one, because they are routinely confused:
    - `half_width` = t*SE, the boundary this run's own standard error allows. A true difference
      exactly this size clears zero about HALF the time, so it is a 50%-power figure, not a
      minimum detectable effect. Reporting it as "what the design could detect" overstates the
      design by ~40%, which is the error a cross-family review caught here on 2026-07-27.
    - `mde80` = (t95 + t80)*SE, the smallest difference this design would call RELIABLY (80% of
      the time). This is the number to compare an observed mean against.
    An observed mean below `mde80` means the run was underpowered for the effect it saw, NOT that
    the effect is absent. Size the next one with `clusters_for(sd_between(delta), target)`."""
    m, lo, hi = delta["mean"], delta["ci95"][0], delta["ci95"][1]
    per = list((delta.get("per_scenario") or {}).values())
    win = (sum(1 for d in per if d > 0) / len(per)) if per else None
    if m != m:
        return {"verdict": "NO-DATA"}
    if lo != lo:
        return {"verdict": "INCONCLUSIVE", "mean": round(m, 4), "ci95": [None, None],
                "half_width": None, "mde80": None, "practical": practical, "win_rate": win,
                "why": "a single cluster carries no interval, so no difference is callable"}
    if lo > practical:
        verdict = "KEEP"
    elif hi < 0:
        verdict = "HARMFUL"
    elif practical > 0 and -practical < lo and hi < practical:
        # CONSERVATIVE EQUIVALENCE, deliberately not TOST-at-5%: a 5% TOST is the 90% interval
        # inside the band, so requiring the 95% interval is STRICTER — fewer CUTs, less power
        # against true nulls, false-equivalence risk below alpha. Stated rather than dressed up
        # as TOST, per a cross-family review. It is one honest route to "not worth keeping", not
        # the only one (cost-benefit and Bayesian ROPE are others); it is the one shipped here.
        # The deleted rule reached CUT from a point estimate near zero, indistinguishable from an
        # underpowered run — that is how a null got laundered into a decision. Unreachable at
        # practical=0: nothing is provably smaller than nothing.
        verdict = "CUT"
    else:
        verdict = "INCONCLUSIVE"
    half = (hi - lo) / 2
    g = delta.get("n_clusters") or 0
    se = half / t95(g - 1) if g >= 2 else float("nan")
    mde80 = (t95(g - 1) + t80(g - 1)) * se if se == se else float("nan")
    out = {"verdict": verdict, "mean": round(m, 4), "ci95": [round(lo, 4), round(hi, 4)],
           "half_width": round(half, 4),
           "mde80": None if mde80 != mde80 else round(mde80, 4),
           "practical": practical, "win_rate": None if win is None else round(win, 3)}
    if verdict == "INCONCLUSIVE":
        bar = "zero" if practical == 0 else f"the practical bar of {practical:+.3f}"
        reach = (f"reliably call a difference of {mde80:.3f} or larger" if mde80 == mde80
                 else "reach no stated power (cluster count unknown)")
        out["why"] = (f"the 95% interval does not clear {bar}; this design could only {reach}, "
                      f"and the observed mean is {m:+.3f}")
    return out


def top_cell_attribution(cells, x, y, top_n=3):
    """Per-cell leave-one-out attribution on the clustered x-y delta (#191 item 3). Returns the
    top_n cells whose removal moves the mean most, each with its leave-one-out mean and whether
    removal flips the KEEP/CUT direction or halves the magnitude — either sets inspect=True:
    inspect those cells for infrastructure failure BEFORE interpreting the bar."""
    base = clustered_delta(cells, x, y)["mean"]
    rows = []
    for i, c in enumerate(cells):
        if c["arm"] not in (x, y):
            continue
        loo = clustered_delta(cells[:i] + cells[i + 1:], x, y)["mean"]
        if math.isnan(loo):  # cluster vanished — removal is maximally load-bearing
            flips, halves = True, True
        else:
            flips = (loo > 0) != (base > 0)
            halves = abs(loo) < abs(base) / 2
        rows.append({"bid": c.get("bid"), "arm": c["arm"], "scenario": c["scenario"],
                     "loo_mean": None if math.isnan(loo) else round(loo, 4),
                     "delta_vs_base": None if math.isnan(loo) else round(base - loo, 4),
                     "flips_or_halves": flips or halves})
    rows.sort(key=lambda r: (r["delta_vs_base"] is not None, -(abs(r["delta_vs_base"] or 0))))
    top = rows[:top_n]
    return {"base_mean": None if math.isnan(base) else round(base, 4), "top": top,
            "inspect": any(r["flips_or_halves"] for r in top)}


def divergence(cells_a, cells_b, label_a="A", label_b="B"):
    """Judge-vs-judge concordance across every (cell x expectation) call. cells_* keyed the same by bid."""
    ma = {c["bid"]: c["met"] for c in cells_a}
    mb = {c["bid"]: c["met"] for c in cells_b}
    bids = [b for b in ma if b in mb]
    agree = a_stricter = b_stricter = a1 = b1 = tot = 0
    for b in bids:
        for i in EXP_IDS:
            tot += 1
            va, vb = ma[b][i], mb[b][i]
            agree += (va == vb)
            a1 += va; b1 += vb
            if vb and not va: a_stricter += 1
            if va and not vb: b_stricter += 1
    if not tot:
        return {"n": 0}
    po = agree / tot
    pa, pb = a1 / tot, b1 / tot
    pe = pa * pb + (1 - pa) * (1 - pb)
    kappa = (po - pe) / (1 - pe) if pe != 1 else 1.0
    return {"n": tot, "agreement": round(po, 3), "kappa": round(kappa, 3),
            f"{label_a}_met_rate": round(pa, 3), f"{label_b}_met_rate": round(pb, 3),
            f"{label_a}_stricter_n": a_stricter, f"{label_b}_stricter_n": b_stricter}


def verdict_flip(delta_a, delta_b):
    """Did the KEEP/CUT direction change between two judges? The load-bearing #172 finding."""
    va, vb = keep_verdict(delta_a)["verdict"], keep_verdict(delta_b)["verdict"]
    return {"judge_a_verdict": va, "judge_b_verdict": vb, "flipped": va != vb,
            "delta_a": round(delta_a["mean"], 4), "delta_b": round(delta_b["mean"], 4)}
