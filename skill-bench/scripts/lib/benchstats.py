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


def clusters_for(sd, target, max_g=4000):
    """Scenario clusters needed before a TRUE difference of `target` clears zero, at `sd` between
    clusters. Iterative because the t multiplier depends on the answer. None means `max_g` is not
    enough — the honest result for a target this design cannot reach at any affordable size.

    A pre-registration states this number (references/pre-registration.md, "Power the design"). A
    grid sized below it can only return INCONCLUSIVE for the effect it is looking for, so it is
    spend with a known-null outcome: measured here as 6-8 scenarios against skill-VERSION deltas,
    which need ~25-97 at the observed spread. Skill-vs-bare deltas (0.18-0.44 recorded) clear at
    6, which is why that question has always worked and version comparisons never could."""
    if sd != sd or sd <= 0 or target <= 0:
        return None
    for g in range(2, max_g + 1):
        if t95(g - 1) * sd / math.sqrt(g) <= target:
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
        interval alone cannot tell you which you have.

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

    `detectable` is the smallest true difference this design could have called — exactly the CI
    half-width, since KEEP requires `mean > t*SE`. It costs nothing to report and makes an
    INCONCLUSIVE verdict readable on sight: an observed mean below it means the run was
    underpowered for the effect it saw, NOT that the effect is absent. Size the next one with
    `clusters_for(sd_between(delta), target)`."""
    m, lo, hi = delta["mean"], delta["ci95"][0], delta["ci95"][1]
    per = list((delta.get("per_scenario") or {}).values())
    win = (sum(1 for d in per if d > 0) / len(per)) if per else None
    if m != m:
        return {"verdict": "NO-DATA"}
    if lo != lo:
        return {"verdict": "INCONCLUSIVE", "mean": round(m, 4), "ci95": [None, None],
                "detectable": None, "practical": practical, "win_rate": win,
                "why": "a single cluster carries no interval, so no difference is callable"}
    if lo > practical:
        verdict = "KEEP"
    elif hi < 0:
        verdict = "HARMFUL"
    elif practical > 0 and -practical < lo and hi < practical:
        # EQUIVALENCE (TOST shape): the whole interval sits inside the practical band, so the
        # data positively support "no difference worth having" rather than merely failing to
        # find one. This is the ONLY honest route to CUT — the deleted rule reached it from a
        # point estimate near zero, which is indistinguishable from an underpowered run and is
        # why a null could be laundered into a decision. Unreachable at practical=0: you cannot
        # prove a difference is smaller than nothing.
        verdict = "CUT"
    else:
        verdict = "INCONCLUSIVE"
    half = (hi - lo) / 2
    out = {"verdict": verdict, "mean": round(m, 4), "ci95": [round(lo, 4), round(hi, 4)],
           "detectable": round(half, 4), "practical": practical,
           "win_rate": None if win is None else round(win, 3)}
    if verdict == "INCONCLUSIVE":
        bar = "zero" if practical == 0 else f"the practical bar of {practical:+.3f}"
        out["why"] = (f"the 95% interval does not clear {bar}; this design could only call a "
                      f"difference of {half:.3f} or larger, and the observed mean is {m:+.3f}")
    elif verdict == "KEEP" and win is not None and win < 0.6:
        out["why"] = (f"clears the bar on the mean, but the treatment won only "
                      f"{win:.0%} of scenarios — check `attribution` before calling it consistent")
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
