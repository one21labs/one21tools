#!/usr/bin/env python3
"""Verdict math + judge-divergence diagnostics for skill-bench (ADR 0019/0025 shape). Stdlib only.

Pure functions, fully unit-testable offline. `cells` everywhere is a list of dicts:
  {"bid","arm","scenario","met":{1:bool,2:bool,3:bool,4:bool}}
"""
import math, statistics
from collections import defaultdict

EXP_IDS = (1, 2, 3, 4)


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
    ci = [m - 1.96 * se, m + 1.96 * se] if se == se else [float("nan")] * 2
    return {"mean": m, "ci95": ci, "per_scenario": per, "n_clusters": len(deltas)}


def per_expectation(cells):
    out = {}
    for i in EXP_IDS:
        out[i] = {a: statistics.mean([c["met"][i] for c in cells if c["arm"] == a] or [float("nan")])
                  for a in sorted({c["arm"] for c in cells})}
    return out


def keep_verdict(delta):
    """KEEP/CUT-CANDIDATE on the clustered C-B point estimate; CI is the confidence signal, not a gate
    (ADR 0052 bar). Direction + whether the CI clears zero."""
    m, lo, hi = delta["mean"], delta["ci95"][0], delta["ci95"][1]
    if m != m:
        return {"verdict": "NO-DATA", "confidence": "none"}
    strong = (lo > 0) or (hi < 0)
    return {"verdict": "KEEP" if m > 0 else "CUT-CANDIDATE",
            "mean": round(m, 4), "ci95": [round(lo, 4), round(hi, 4)],
            "confidence": "strong" if strong else "weak"}


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
