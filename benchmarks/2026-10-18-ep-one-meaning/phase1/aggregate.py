#!/usr/bin/env python3
"""Eval-clustered read (n = evals): per eval, mean fraction-met per arm over reps; then
d_current, d_plain (vs without) and pc = plain - current, with 95% t CI (df = n-1)."""
import json, os, statistics, math

BASE = os.path.dirname(os.path.abspath(__file__))
T975 = {5: 2.571}
rows = [json.loads(l) for l in open(os.path.join(BASE, "graded", "verdicts.jsonl"))]
frac = {}
for r in rows:
    g, p = r["grader"], r["prosecutor"]
    if not g or not p:
        continue
    met = min(g["met"], p["met"]); tot = g["total"]
    frac.setdefault((r["eval_id"], r["arm"]), []).append(met / tot)

evals = sorted({e for e, _ in frac}, key=int)
mean = lambda k: statistics.fmean(frac[k])
print(f"{'eval':5}{'without':>9}{'current':>9}{'plain':>9}{'d_cur':>8}{'d_plain':>9}{'plain-cur':>11}")
S = {"d_current": [], "d_plain": [], "plain_minus_current": []}
for e in evals:
    w, c, p = mean((e, "without")), mean((e, "with-current")), mean((e, "with-plain"))
    S["d_current"].append(c - w); S["d_plain"].append(p - w); S["plain_minus_current"].append(p - c)
    print(f"{e:5}{w:9.2f}{c:9.2f}{p:9.2f}{c-w:+8.2f}{p-w:+9.2f}{p-c:+11.2f}")
for k, v in S.items():
    n = len(v); m = statistics.fmean(v); se = statistics.stdev(v) / math.sqrt(n)
    t = T975[n - 1]  # KeyError on any other prompt count, never a silent z fallback
    print(f"{k:22} mean {m:+.3f}  95% t-CI [{m - t*se:+.3f}, {m + t*se:+.3f}]")
arm_all = {a: statistics.fmean([x for (e, aa), xs in frac.items() if aa == a for x in xs])
           for a in ("without", "with-current", "with-plain")}
print("overall fraction met:", {a: round(v, 3) for a, v in arm_all.items()})
