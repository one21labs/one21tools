#!/usr/bin/env python3
"""Statistics for the 5-model x 2-arm x 3-rep feedback assay. Stdlib only (house constraint).

WHY NOT FIVE SEPARATE n=3 t-TESTS. The obvious reading of "3 runs each" is five independent
two-sample tests at df=4, where the smallest reliably detectable effect is 3.03 standard
deviations. Worse, three identical rep scores make a cell's own SD exactly 0 — which the July 2026
run of this benchmark family produced in EVERY cell — and a t-test on a zero variance estimate is
degenerate, reporting infinite significance for any difference at all.

This module instead treats MODEL as a blocking factor and pools the within-cell variance across
all ten cells, giving df=20 instead of df=4. Three consequences, all improvements:
  - the per-model detectable effect falls from 3.03 to 2.40 pooled SDs;
  - the skill's average effect across models is testable at 1.08 pooled SDs;
  - a cell that happens to show zero rep-to-rep variation no longer breaks its own comparison,
    because the variance estimate is borrowed from the other nine cells.
Each cell's OWN standard deviation is still reported, separately, as the consistency figure.

EVERY comparison carries `mde80`: the smallest true difference this design would call reliably
(80% of the time). A result below its own mde80 means the design was underpowered for the effect
it saw, NOT that the effect is absent. That distinction is the whole point of the exercise.
"""
import math
import statistics
from collections import defaultdict

# Critical values shared with skill-bench/scripts/lib/benchstats.py (ADR 0019/0025 shape).
_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306,
        9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
        16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086, 21: 2.080, 22: 2.074,
        23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045,
        30: 2.042}
_T80 = {1: 1.3764, 2: 1.0607, 3: 0.9785, 4: 0.9410, 5: 0.9195, 6: 0.9057, 7: 0.8960,
        8: 0.8889, 9: 0.8834, 10: 0.8791, 11: 0.8755, 12: 0.8726, 13: 0.8702, 14: 0.8681,
        15: 0.8662, 16: 0.8647, 17: 0.8633, 18: 0.8620, 19: 0.8610, 20: 0.8600, 21: 0.8591,
        22: 0.8583, 23: 0.8575, 24: 0.8569, 25: 0.8562, 26: 0.8557, 27: 0.8551, 28: 0.8546,
        29: 0.8542, 30: 0.8538}


def t95(df):
    return _T95.get(df, 1.96) if df >= 1 else float("nan")


def t80(df):
    return _T80.get(df, 0.8416) if df >= 1 else float("nan")


# ------------------------------------------------------------------ distributions
# Exact tail probabilities via the regularized incomplete beta, so a p-value never has to be
# eyeballed against a hard-coded critical value.

def _betacf(a, b, x, itmax=300, eps=3e-16):
    """Continued fraction for the incomplete beta (modified Lentz)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, itmax + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def betainc(a, b, x):
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_two_sided_p(t, df):
    """P(|T| > |t|) for Student t on df degrees of freedom."""
    if df < 1 or t != t:
        return float("nan")
    if math.isinf(t):
        return 0.0
    return betainc(df / 2.0, 0.5, df / (df + t * t))


def f_upper_p(f, df1, df2):
    """P(F > f) for the F distribution."""
    if f != f or f < 0 or df1 < 1 or df2 < 1:
        return float("nan")
    if math.isinf(f):
        return 0.0
    return betainc(df2 / 2.0, df1 / 2.0, df2 / (df2 + df1 * f))


# ------------------------------------------------------------------ design analysis

def cell_table(rows, value_key="score"):
    """{(lane, arm): [values...]} from flat graded rows."""
    out = defaultdict(list)
    for r in rows:
        out[(r["lane"], r["arm"])].append(r[value_key])
    return dict(out)


def pooled_within(cells):
    """Pooled within-cell SD and its df. This is the error term every comparison below uses.

    df = sum over cells of (reps - 1). With 10 cells x 3 reps that is 20, versus the df=4 a single
    cell's own variance would carry.
    """
    ss, df = 0.0, 0
    for vals in cells.values():
        if len(vals) < 2:
            continue
        m = statistics.mean(vals)
        ss += sum((v - m) ** 2 for v in vals)
        df += len(vals) - 1
    if df < 1:
        return float("nan"), 0
    return math.sqrt(ss / df), df


def _interval(delta, se, df):
    """Point estimate + 95% interval + the two precision numbers, never confused.

    half_width is what this run's own standard error allows; a true difference exactly that size
    clears zero only about half the time. mde80 is the smallest difference the design would call
    RELIABLY. Reporting half_width as "what we could detect" overstates the design by ~40%.
    """
    if se != se or se <= 0:
        return {"delta": round(delta, 4), "se": None, "df": df, "ci95": [None, None],
                "half_width": None, "mde80": None, "t": None, "p": None,
                "note": "no usable variance estimate — interval undefined"}
    hw = t95(df) * se
    return {"delta": round(delta, 4), "se": round(se, 4), "df": df,
            "ci95": [round(delta - hw, 4), round(delta + hw, 4)],
            "half_width": round(hw, 4),
            "mde80": round((t95(df) + t80(df)) * se, 4),
            "t": round(delta / se, 3),
            "p": round(t_two_sided_p(delta / se, df), 5)}


def per_model_effects(cells, treatment="wp", control="bare"):
    """Treatment effect for each model, using the POOLED error term (df=20, not df=4)."""
    s_p, df_w = pooled_within(cells)
    lanes = sorted({ln for ln, _ in cells})
    out = {}
    for ln in lanes:
        tv, cv = cells.get((ln, treatment), []), cells.get((ln, control), [])
        if not tv or not cv:
            continue
        d = statistics.mean(tv) - statistics.mean(cv)
        se = s_p * math.sqrt(1.0 / len(tv) + 1.0 / len(cv)) if s_p == s_p else float("nan")
        row = _interval(d, se, df_w)
        row.update({
            "lane": ln,
            "mean_control": round(statistics.mean(cv), 4),
            "mean_treatment": round(statistics.mean(tv), 4),
            "sd_control": round(statistics.stdev(cv), 4) if len(cv) > 1 else 0.0,
            "sd_treatment": round(statistics.stdev(tv), 4) if len(tv) > 1 else 0.0,
        })
        out[ln] = row
    return out


def arm_main_effect(cells, treatment="wp", control="bare"):
    """The skill's average effect across models — the best-powered question this design asks."""
    s_p, df_w = pooled_within(cells)
    lanes = sorted({ln for ln, _ in cells}
                   & {ln for ln, a in cells if a == treatment}
                   & {ln for ln, a in cells if a == control})
    deltas = [statistics.mean(cells[(ln, treatment)]) - statistics.mean(cells[(ln, control)])
              for ln in lanes]
    if not deltas:
        return {"note": "no paired lanes"}
    reps = statistics.mean([len(cells[(ln, treatment)]) for ln in lanes])
    D = statistics.mean(deltas)
    se = s_p * math.sqrt(2.0 / (len(lanes) * reps)) if s_p == s_p else float("nan")
    row = _interval(D, se, df_w)
    row.update({"n_models": len(lanes), "per_model_delta": {ln: round(d, 4)
                                                            for ln, d in zip(lanes, deltas)}})
    return row


def interaction(cells, treatment="wp", control="bare"):
    """Does the skill's effect DIFFER by model? Two-way model x arm interaction F test.

    This is the formal version of the owner's question "effect size for each model type": a
    non-significant interaction means the per-model differences observed are within what noise
    alone produces, so the models should not be ranked against each other on this data.
    """
    s_p, df_w = pooled_within(cells)
    lanes = sorted({ln for ln, a in cells if a == treatment}
                   & {ln for ln, a in cells if a == control})
    if len(lanes) < 2 or s_p != s_p or s_p <= 0:
        return {"note": "interaction not estimable"}
    deltas = [statistics.mean(cells[(ln, treatment)]) - statistics.mean(cells[(ln, control)])
              for ln in lanes]
    r = statistics.mean([len(cells[(ln, treatment)]) for ln in lanes])
    D = statistics.mean(deltas)
    # With two arms the interaction sum of squares reduces to the spread of the per-model deltas.
    ss = r * sum((d - D) ** 2 for d in deltas) / 2.0
    df1 = len(lanes) - 1
    f = (ss / df1) / (s_p ** 2)
    return {"F": round(f, 3), "df1": df1, "df2": df_w,
            "p": round(f_upper_p(f, df1, df_w), 5),
            "delta_spread": round(max(deltas) - min(deltas), 4)}


def model_main_effect(cells):
    """Do the models differ in feedback quality overall, averaging over arms?"""
    s_p, df_w = pooled_within(cells)
    lanes = sorted({ln for ln, _ in cells})
    if len(lanes) < 2 or s_p != s_p or s_p <= 0:
        return {"note": "not estimable"}
    per_lane, n_per_lane = {}, {}
    for ln in lanes:
        vals = [v for (l2, _), vs in cells.items() if l2 == ln for v in vs]
        per_lane[ln] = statistics.mean(vals)
        n_per_lane[ln] = len(vals)
    grand = statistics.mean([v for vs in cells.values() for v in vs])
    ss = sum(n_per_lane[ln] * (per_lane[ln] - grand) ** 2 for ln in lanes)
    df1 = len(lanes) - 1
    f = (ss / df1) / (s_p ** 2)
    return {"F": round(f, 3), "df1": df1, "df2": df_w,
            "p": round(f_upper_p(f, df1, df_w), 5),
            "lane_means": {ln: round(v, 4) for ln, v in sorted(per_lane.items())}}


def consistency(cells):
    """Run-to-run variability per cell — a primary deliverable, not a nuisance parameter."""
    out = {}
    for (ln, arm), vals in sorted(cells.items()):
        out[f"{ln}-{arm}"] = {
            "n": len(vals),
            "mean": round(statistics.mean(vals), 4),
            "sd": round(statistics.stdev(vals), 4) if len(vals) > 1 else 0.0,
            "min": round(min(vals), 4),
            "max": round(max(vals), 4),
            "range": round(max(vals) - min(vals), 4),
            "values": [round(v, 4) for v in vals],
        }
    return out


def verdict(effect, practical=0.0):
    """THE VERDICT IS THE INTERVAL, never the point estimate (skill-bench keep_verdict rule).

    INCONCLUSIVE carries the reason, including what this design could actually have detected, so a
    null is never silently read as an established absence of effect.
    """
    if effect.get("ci95", [None])[0] is None:
        return {"verdict": "NO-INTERVAL", "why": effect.get("note", "no variance estimate")}
    lo, hi, m, mde = effect["ci95"][0], effect["ci95"][1], effect["delta"], effect["mde80"]
    if lo > practical:
        return {"verdict": "KEEP", "why": f"95% interval lower bound {lo:+.3f} clears {practical:+.3f}"}
    if hi < 0:
        return {"verdict": "HARMFUL", "why": f"95% interval upper bound {hi:+.3f} is below zero"}
    if practical > 0 and -practical < lo and hi < practical:
        return {"verdict": "CUT", "why": f"interval lies inside +/-{practical:.3f}"}
    return {"verdict": "INCONCLUSIVE",
            "why": (f"the interval [{lo:+.3f}, {hi:+.3f}] does not clear zero; this comparison "
                    f"could only reliably detect {mde:.3f} or larger, and the observed effect is "
                    f"{m:+.3f}. That bounds the effect — it does not establish its absence.")}
