#!/usr/bin/env python3
"""/bench-verdict — re-run the verdict math on an existing graded benchmark dir, with a pluggable
judge, and NO new generation spend (ADR 0055). This is the generalized #172 cross-family prototype.

Two modes:
  --judge grok|claude   re-grade the committed normalized cells with that judge (grade+prosecute),
                        then compute arm means, clustered C-B (KEEP/CUT), per-expectation.
  --judge both          run the chosen judge AND load the committed baseline verdicts, then emit the
                        JUDGE-DIVERGENCE diagnostic (agreement, kappa, stricter-count, verdict flip).

Input dir must contain graded/verdicts.jsonl (bid, scenario, norm, expectations[baseline judge]),
graded/arm_map.tsv (bid arm scenario rep), graded/keys.json (scenario -> rubric key).

Normalization is REUSED from the committed cells (the only stage that sees raw output) so the judge
family is the sole changed variable. Reads the benchmark dir read-only; writes only to --out.
"""
import argparse, json, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
import rubric, benchstats  # noqa: E402
from judge import make_judge, met_map, JudgeError  # noqa: E402


def load_dir(d):
    amap = {}
    with open(os.path.join(d, "graded/arm_map.tsv")) as f:
        for line in f:
            if line.startswith("bid"):
                continue
            b, a, s, r = line.strip().split("\t")
            amap[b] = (a, s)
    cells, baseline = [], []
    with open(os.path.join(d, "graded/verdicts.jsonl")) as f:
        for line in f:
            v = json.loads(line)
            if v.get("bid") not in amap:
                continue
            arm, scn = amap[v["bid"]]
            cells.append({"bid": v["bid"], "arm": arm, "scenario": scn, "norm": v["norm"]})
            baseline.append({"bid": v["bid"], "arm": arm, "scenario": scn, "met": met_map(v)})
    with open(os.path.join(d, "graded/keys.json")) as f:
        keys = json.load(f)
    return cells, baseline, keys


def regrade_cell(judge, cell, key):
    g = judge.grade(rubric.grade_prompt(cell["norm"], key), rubric.GRADE_SCHEMA)
    p = judge.grade(rubric.prosecute_prompt(cell["norm"], key, g), rubric.GRADE_SCHEMA)
    gm, pm = met_map(g), met_map(p)
    return {"bid": cell["bid"], "arm": cell["arm"], "scenario": cell["scenario"],
            "met": {i: gm.get(i, False) and pm.get(i, False) for i in benchstats.EXP_IDS}}


def regrade(judge, cells, keys, workers, cache=None):
    if cache:  # reuse a prior run's per-cell met (offline demo / resumable)
        cm = {c["bid"]: c["met"] for c in cache}
        return [{**c, "met": cm[c["bid"]]} for c in cells if c["bid"] in cm], []
    out, errs = [], []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(regrade_cell, judge, c, keys[c["scenario"]]): c["bid"] for c in cells}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                out.append(fut.result())
            except (JudgeError, Exception) as e:
                errs.append({"bid": futs[fut], "error": str(e)[:200]})
            print(f"  [{i}/{len(cells)}] {'ok' if not errs or errs[-1]['bid']!=futs[fut] else 'ERR'}",
                  file=sys.stderr)
    return out, errs


def summarize(cells, x, y):
    d_xy = benchstats.clustered_delta(cells, x, y)
    return {"arm_means": {a: round(benchstats.arm_mean(cells, a), 3) for a in ("A", "B", "C")},
            f"{x}_minus_{y}": {**benchstats.keep_verdict(d_xy)},
            f"{x}_minus_A": round(benchstats.clustered_delta(cells, x, "A")["mean"], 4),
            "per_expectation": {i: {a: round(v, 2) for a, v in benchstats.per_expectation(cells)[i].items()}
                                for i in benchstats.EXP_IDS}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--judge", choices=["grok", "claude", "both"], default="grok")
    ap.add_argument("--out", default="-")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--cache", help="prior regrade jsonl (offline: skip live judge calls)")
    a = ap.parse_args()

    cells, baseline, keys = load_dir(a.dir)
    if a.limit:
        cells, baseline = cells[:a.limit], baseline[:a.limit]
    cache = None
    if a.cache:
        cache = [{"bid": j["bid"], "arm": dict((c["bid"], c["arm"]) for c in cells)[j["bid"]],
                  "scenario": dict((c["bid"], c["scenario"]) for c in cells)[j["bid"]],
                  "met": {int(k): v for k, v in ({e["id"]: e["met"] for e in j["expectations"]}).items()}}
                 for j in map(json.loads, open(a.cache)) if "error" not in j and j["bid"] in {c["bid"] for c in cells}]

    live = "grok" if a.judge in ("grok", "both") else "claude"
    judge = make_judge(live)
    print(f"re-grading {len(cells)} cells with judge={judge.name}"
          + (" (cached)" if cache else ""), file=sys.stderr)
    regraded, errs = regrade(judge, cells, keys, a.workers, cache=cache)

    report = {"dir": a.dir, "judge": judge.name, "n_cells": len(regraded), "errors": len(errs),
              "notional_cost_usd": {
                  "judge_calls": judge.calls, "usd": judge.cost_usd(),
                  "note": "shadow cost at published API rates (deterministic: tokens x rate); "
                          "$0 marginal under subscription; 0 here when --cache (no live calls)"},
              "regraded": summarize(regraded, "C", "B")}
    if a.judge == "both":
        report["baseline_judge"] = "committed (opus)"
        report["baseline"] = summarize(baseline, "C", "B")
        report["divergence"] = benchstats.divergence(baseline, regraded, "baseline", judge.name)
        report["verdict_flip"] = benchstats.verdict_flip(
            benchstats.clustered_delta(baseline, "C", "B"),
            benchstats.clustered_delta(regraded, "C", "B"))
    js = json.dumps(report, indent=1)
    if a.out == "-":
        print(js)
    else:
        open(a.out, "w").write(js)
        print(f"wrote {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
