#!/usr/bin/env python3
"""report.py ROUND BASELINE_ARM -> per-prompt table + each arm vs baseline (abs, relative, 95% t CI)."""
import json, os, sys, statistics as st, math
BASE = os.path.dirname(os.path.abspath(__file__)); rnd, base = sys.argv[1], sys.argv[2]
T = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179}
f = {}
for l in open(os.path.join(BASE, "rounds", rnd, "verdicts.jsonl")):
    r = json.loads(l); g, p = r["grader"], r["prosecutor"]
    if g and p: f.setdefault((r["key"], r["arm"]), []).append(min(g["met"], p["met"]) / g["total"])
keys = sorted({k for k, _ in f}, key=lambda k: (k[:2], int(''.join(c for c in k if c.isdigit()))))
arms = sorted({a for _, a in f}, key=lambda a: (a != "without", a != base, a))
pm = {(k, a): st.fmean(f[(k, a)]) for k, a in f}
print("prompt  " + "".join(f"{a:>14}" for a in arms))
for k in keys: print(f"{k:8}" + "".join(f"{pm[(k, a)]:14.2f}" for a in arms))
print("mean    " + "".join(f"{st.fmean(pm[(k, a)] for k in keys):14.3f}" for a in arms))
b = st.fmean(pm[(k, base)] for k in keys)
for a in arms:
    if a == base: continue
    d = [pm[(k, a)] - pm[(k, base)] for k in keys]; n = len(d); m = st.fmean(d)
    h = T[n - 1] * st.stdev(d) / math.sqrt(n)
    print(f"{a} vs {base}: {m:+.3f} abs, {m / b * 100:+.1f}% relative, 95% CI [{m - h:+.3f}, {m + h:+.3f}]")
