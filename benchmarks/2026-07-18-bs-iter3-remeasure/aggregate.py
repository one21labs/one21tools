#!/usr/bin/env python3
"""Aggregate the iter-3 re-measure: per-judge d_old / d_new / diff + the ADR 0027 merge bar.

Inputs: graded/cells-{grok,claude}.jsonl ({bid, arm, scenario, rep, met{...}}),
treatments/costs.json (chars_delta for the cost prong). Metric = fraction-met per cell;
per (eval, arm) mean over reps; eval-clustered mean + 95% CI on d_old/d_new/diff;
merge_verdict from the shared lib on BOTH judges + the cross-judge flip diagnostic.
Writes results.jsonl.
"""
import json
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skill-bench" / "scripts" / "lib"))
from verdict import merge_verdict, verdict_of  # noqa: E402

ARMS = ("without", "with-old", "with-new")


def ci95(vals):
    n = len(vals)
    mean = statistics.fmean(vals) if n else 0.0
    sd = statistics.stdev(vals) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n else 0.0
    return round(mean, 3), round(mean - 1.96 * se, 3), round(mean + 1.96 * se, 3)


def judge_stats(jname, chars_delta, out):
    rows = [json.loads(l) for l in
            (HERE / "graded" / f"cells-{jname}.jsonl").read_text(encoding="utf-8").splitlines() if l]
    frac = {}
    for r in rows:
        met = r["met"]
        frac.setdefault((r["scenario"], r["arm"]), []).append(
            sum(1 for v in met.values() if v) / len(met) if met else 0.0)
    evs = sorted({e for (e, _) in frac}, key=lambda x: int(x[1:]))
    d_old, d_new, diffs = [], [], []
    for e in evs:
        m = {a: (statistics.fmean(frac[(e, a)]) if frac.get((e, a)) else 0.0) for a in ARMS}
        d_old.append(m["with-old"] - m["without"])
        d_new.append(m["with-new"] - m["without"])
        diffs.append(d_new[-1] - d_old[-1])
        out.append({"record": "eval", "judge": jname, "eval_id": e,
                    "without": round(m["without"], 3), "with_old": round(m["with-old"], 3),
                    "with_new": round(m["with-new"], 3), "d_old": round(d_old[-1], 3),
                    "d_new": round(d_new[-1], 3), "diff": round(diffs[-1], 3)})
    summary = {}
    for name, vals in (("d_old", d_old), ("d_new", d_new), ("diff", diffs)):
        mean, lo, hi = ci95(vals)
        summary[name] = {"mean": mean, "ci95": [lo, hi],
                         "keep": verdict_of(mean, lo, hi, len(vals))}
    dm, (dlo, dhi) = summary["diff"]["mean"], summary["diff"]["ci95"]
    merge, conf = merge_verdict(dm, dlo, dhi, len(diffs), chars_delta)
    label = f"MERGE-{conf}" if merge else "NO-MERGE"
    out.append({"record": "verdict", "judge": jname, "evals": len(evs), **summary,
                "chars_delta": chars_delta, "merge": merge, "confidence": conf, "label": label})
    return summary, label


def main():
    chars_delta = json.loads((HERE / "treatments" / "costs.json").read_text(encoding="utf-8"))["chars_delta"]
    out = []
    labels = {}
    for jname in ("grok", "claude"):
        summary, label = judge_stats(jname, chars_delta, out)
        labels[jname] = label
        print(f"=== {jname} ===")
        for r in [r for r in out if r["record"] == "eval" and r["judge"] == jname]:
            print(f"  {r['eval_id']}: without={r['without']:.2f} old={r['with_old']:.2f} "
                  f"new={r['with_new']:.2f}  d_old={r['d_old']:+.2f} d_new={r['d_new']:+.2f} "
                  f"diff={r['diff']:+.2f}")
        for name in ("d_old", "d_new", "diff"):
            s = summary[name]
            print(f"  {name}: mean {s['mean']:+.3f} CI [{s['ci95'][0]:+.3f},{s['ci95'][1]:+.3f}] "
                  f"({s['keep']})")
        print(f"  VERDICT ({jname}): {label}")
    flip = labels["grok"].startswith("MERGE") != labels["claude"].startswith("MERGE")
    strong_both = labels["grok"] == "MERGE-strong" and labels["claude"] == "MERGE-strong"
    out.append({"record": "cross-judge", "labels": labels, "flip": flip,
                "unambiguous_bar_met": strong_both,
                "bar": "pre-registered: MERGE with diff CI excluding 0 under BOTH judges"})
    with open(HERE / "results.jsonl", "w", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r) + "\n")
    print(f"\ncross-judge flip: {flip}; 'unambiguously better' bar met: {strong_both}")


if __name__ == "__main__":
    main()
