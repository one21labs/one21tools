#!/usr/bin/env python3
"""Judge-robust / judge-fragile classification for the #224 Stage 1 cross-judge re-grade.

Recomputes each source dir's committed statistics from graded/<source>.grok.jsonl with the SAME
math as that dir's aggregate.py (per-eval arm means, per-skill mean + 95% CI clustered over
evals; shared verdict_of / merge_verdict), pairs each with the recorded sonnet-judged statistic
(parsed from the source's committed results.jsonl), and applies the pre-registered rule
(README.md): fragile = decision-class flip OR recorded CI-excludes-0 becoming CI-straddling.
Merge-bar comparisons use the CURRENT shared merge_verdict on BOTH sides (README deviation 3).

Writes results.jsonl; prints the classification table.
"""
import json
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
sys.path.insert(0, str(BENCH.parent / "skill-bench" / "scripts" / "lib"))
from verdict import merge_verdict, verdict_of  # noqa: E402

BATTERY = "2026-07-08-skills-hermetic"
REMEASURES = ["2026-07-09-three-skills-remeasure", "2026-07-09-bs-iter2-remeasure",
              "2026-07-09-ep-remeasure-hermetic"]


def rows_of(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def grok_frac(src):
    """(skill, eval_id, arm) -> [met_final/total per rep] from this run's grok verdicts."""
    frac = {}
    for r in rows_of(HERE / "graded" / f"{src}.grok.jsonl"):
        tot = r["total"] or 0
        frac.setdefault((r["skill"], r["eval_id"], r["arm"]), []).append(
            (r["met"] / tot) if tot else 0.0)
    return frac


def ci95(vals):
    n = len(vals)
    mean = statistics.fmean(vals) if n else 0.0
    sd = statistics.stdev(vals) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n else 0.0
    return round(mean, 3), round(mean - 1.96 * se, 3), round(mean + 1.96 * se, 3)


def excludes0(lo, hi):
    return lo > 0 or hi < 0


def keep_class(label):
    return {"KEEP": "positive-shown", "HARMFUL": "negative-shown"}.get(label, "not-shown")


def classify(rec_label, rec_lo, rec_hi, grok_label, grok_lo, grok_hi, merge_axis=False):
    """Pre-registered rule. Returns (classification, reason)."""
    if merge_axis:
        flip = (rec_label.startswith("MERGE")) != (grok_label.startswith("MERGE"))
        strong_to_weak = rec_label == "MERGE-strong" and grok_label != "MERGE-strong"
    else:
        flip = keep_class(rec_label) != keep_class(grok_label)
        strong_to_weak = excludes0(rec_lo, rec_hi) and not excludes0(grok_lo, grok_hi)
    if flip:
        return "judge-fragile", f"decision flip {rec_label} -> {grok_label}"
    if strong_to_weak:
        return "judge-fragile", "strong -> weak (recorded CI excluded 0; grok CI straddles)"
    return "judge-robust", f"{rec_label} -> {grok_label}"


def battery_comparisons(out):
    frac = grok_frac(BATTERY)
    recorded = {r["skill"]: r for r in rows_of(BENCH / BATTERY / "results.jsonl")
                if r.get("record") == "skill" and r.get("metric") == "fraction_met"}
    rec_overall = next(r for r in rows_of(BENCH / BATTERY / "results.jsonl")
                       if r.get("record") == "overall" and r.get("metric") == "fraction_met")
    all_deltas = []
    for sk in sorted({s for (s, _, _) in frac}):
        evs = sorted({e for (s, e, _) in frac if s == sk}, key=int)
        deltas = []
        for e in evs:
            wi, wo = frac.get((sk, e, "with"), []), frac.get((sk, e, "without"), [])
            d = (statistics.fmean(wi) if wi else 0.0) - (statistics.fmean(wo) if wo else 0.0)
            deltas.append(d)
            out.append({"record": "grok-eval", "source": BATTERY, "skill": sk, "eval_id": e,
                        "with": round(statistics.fmean(wi), 3) if wi else None,
                        "without": round(statistics.fmean(wo), 3) if wo else None,
                        "delta": round(d, 3)})
        all_deltas.extend(deltas)
        mean, lo, hi = ci95(deltas)
        g_label = verdict_of(mean, lo, hi, len(deltas))
        rec = recorded[sk]
        r_lo, r_hi = rec["delta_ci95"]
        cls, why = classify(rec["verdict"], r_lo, r_hi, g_label, lo, hi)
        out.append({"record": "comparison", "source": BATTERY, "skill": sk,
                    "statistic": "with-without delta (fraction-met)",
                    "recorded": {"mean": rec["mean_delta"], "ci95": rec["delta_ci95"],
                                 "label": rec["verdict"]},
                    "grok": {"mean": mean, "ci95": [lo, hi], "label": g_label},
                    "classification": cls, "reason": why})
    mean, lo, hi = ci95(all_deltas)
    g_label = verdict_of(mean, lo, hi, len(all_deltas))
    r_lo, r_hi = rec_overall["delta_ci95"]
    cls, why = classify(rec_overall["verdict"], r_lo, r_hi, g_label, lo, hi)
    out.append({"record": "comparison", "source": BATTERY, "skill": "OVERALL",
                "statistic": "with-without delta (fraction-met)",
                "recorded": {"mean": rec_overall["mean_delta"], "ci95": rec_overall["delta_ci95"],
                             "label": rec_overall["verdict"]},
                "grok": {"mean": mean, "ci95": [lo, hi], "label": g_label},
                "classification": cls, "reason": why})


def merge_label(mean, lo, hi, n, chars_delta):
    merge, conf = merge_verdict(mean, lo, hi, n, chars_delta)
    return f"MERGE-{conf}" if merge else "NO-MERGE"


def remeasure_comparisons(src, out):
    frac = grok_frac(src)
    committed = rows_of(BENCH / src / "results.jsonl")
    verdict_rows = [r for r in committed if r.get("record") == "verdict"]
    cost_row = next((r for r in committed if r.get("record") == "cost"), None)
    for vr in verdict_rows:
        sk = vr.get("skill") or "engineering-principles"
        chars = (vr.get("cost") or cost_row or {}).get("body_chars") \
            if (vr.get("cost") or cost_row) else None
        chars_delta = chars["with-new"] - chars["with-old"]
        evs = sorted({e for (s, e, _) in frac if s == sk}, key=int)
        d_old, d_new, diffs = [], [], []
        for e in evs:
            m = {a: (statistics.fmean(frac[(sk, e, a)]) if frac.get((sk, e, a)) else 0.0)
                 for a in ("without", "with-old", "with-new")}
            d_old.append(m["with-old"] - m["without"])
            d_new.append(m["with-new"] - m["without"])
            diffs.append(d_new[-1] - d_old[-1])
            out.append({"record": "grok-eval", "source": src, "skill": sk, "eval_id": e,
                        "without": round(m["without"], 3), "with_old": round(m["with-old"], 3),
                        "with_new": round(m["with-new"], 3), "d_old": round(d_old[-1], 3),
                        "d_new": round(d_new[-1], 3), "diff": round(diffs[-1], 3)})
        # PRIMARY: the merge decision, current bar on both sides (README deviation 3)
        gm, glo, ghi = ci95(diffs)
        g_label = merge_label(gm, glo, ghi, len(diffs), chars_delta)
        rm, (rlo, rhi) = vr["diff"]["mean"], vr["diff"]["ci95"]
        r_label = merge_label(rm, rlo, rhi, vr["evals"], chars_delta)
        historical = f"MERGE-{vr['confidence']}" if vr.get("merge") else "NO-MERGE"
        cls, why = classify(r_label, rlo, rhi, g_label, glo, ghi, merge_axis=True)
        out.append({"record": "comparison", "source": src, "skill": sk,
                    "statistic": "merge decision on diff = d_new - d_old (current ADR 0027 bar)",
                    "recorded": {"mean": rm, "ci95": [rlo, rhi], "label": r_label,
                                 "historical_label": historical, "chars_delta": chars_delta},
                    "grok": {"mean": gm, "ci95": [glo, ghi], "label": g_label},
                    "classification": cls, "reason": why})
        # SECONDARY: d_old / d_new keep-verdicts (context for Stage 2, not gates)
        for name, gvals in (("d_old", d_old), ("d_new", d_new)):
            gm2, glo2, ghi2 = ci95(gvals)
            g2 = verdict_of(gm2, glo2, ghi2, len(gvals))
            rm2, (rlo2, rhi2) = vr[name]["mean"], vr[name]["ci95"]
            r2 = verdict_of(rm2, rlo2, rhi2, vr["evals"])
            cls2, why2 = classify(r2, rlo2, rhi2, g2, glo2, ghi2)
            out.append({"record": "comparison-secondary", "source": src, "skill": sk,
                        "statistic": f"{name} (with-arm minus without, fraction-met)",
                        "recorded": {"mean": rm2, "ci95": [rlo2, rhi2], "label": r2},
                        "grok": {"mean": gm2, "ci95": [glo2, ghi2], "label": g2},
                        "classification": cls2, "reason": why2})


def cell_agreement(src, out):
    """Diagnostic: per-cell fraction under grok vs the committed sonnet grading."""
    g = {r["bid"]: (r["met"] / r["total"] if r["total"] else 0.0)
         for r in rows_of(HERE / "graded" / f"{src}.grok.jsonl")}
    graded = BENCH / src / "graded"
    s = {}
    if (graded / "verdicts.json").exists():
        for bid, v in json.loads((graded / "verdicts.json").read_text(encoding="utf-8")).items():
            s[bid] = (v["met"] / v["total"]) if v.get("total") else 0.0
    else:
        vs = {r["bid"]: r for r in rows_of(graded / "verdicts.jsonl")}
        ps = {r["bid"]: r for r in rows_of(graded / "prosecute_counts.jsonl")}
        for bid, v in vs.items():
            tot = v.get("total") or 0
            met = min(v.get("met") or 0, (ps.get(bid) or {}).get("met") or 0)
            s[bid] = (met / tot) if tot else 0.0
    both = [(g[b], s[b]) for b in g if b in s]
    d = [gv - sv for gv, sv in both]
    out.append({"record": "cell-agreement", "source": src, "cells": len(both),
                "mean_delta_grok_minus_sonnet": round(statistics.fmean(d), 3) if d else None,
                "mean_abs_delta": round(statistics.fmean(map(abs, d)), 3) if d else None})


def main():
    out = []
    battery_comparisons(out)
    for src in REMEASURES:
        remeasure_comparisons(src, out)
    for src in [BATTERY] + REMEASURES:
        cell_agreement(src, out)
    with open(HERE / "results.jsonl", "w", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r) + "\n")

    comps = [r for r in out if r["record"] in ("comparison", "comparison-secondary")]
    fragile = [r for r in comps if r["classification"] == "judge-fragile"]
    print("=== #224 Stage 1: cross-judge verdict classification (grok vs recorded sonnet) ===")
    for r in comps:
        tag = "PRIMARY  " if r["record"] == "comparison" else "secondary"
        rec, gk = r["recorded"], r["grok"]
        print(f"[{tag}] {r['source']} / {r['skill']} — {r['statistic']}\n"
              f"    recorded {rec['label']:<14} mean {rec['mean']:+.3f} CI [{rec['ci95'][0]:+.3f},{rec['ci95'][1]:+.3f}]"
              + (f" (historical: {rec['historical_label']})" if rec.get("historical_label") else "") + "\n"
              f"    grok     {gk['label']:<14} mean {gk['mean']:+.3f} CI [{gk['ci95'][0]:+.3f},{gk['ci95'][1]:+.3f}]\n"
              f"    -> {r['classification'].upper()} ({r['reason']})")
    for r in [r for r in out if r["record"] == "cell-agreement"]:
        print(f"[agreement] {r['source']}: {r['cells']} cells, grok-sonnet mean delta "
              f"{r['mean_delta_grok_minus_sonnet']:+.3f}, mean |delta| {r['mean_abs_delta']:.3f}")
    n_primary = sum(1 for r in comps if r["record"] == "comparison")
    print(f"\n{n_primary} primary verdicts: "
          f"{sum(1 for r in fragile if r['record'] == 'comparison')} fragile; "
          f"{len(comps) - n_primary} secondary: "
          f"{sum(1 for r in fragile if r['record'] == 'comparison-secondary')} fragile")


if __name__ == "__main__":
    main()
