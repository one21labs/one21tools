#!/usr/bin/env python3
"""Select the 8 main-run tasks from the pre-screen (issue #41 pre-registration).

Tiering can only add value where the solo tiers diverge, so rank candidates by the
Haiku-solo vs Opus-solo fraction-met gap (mean over available pre-screen reps; 1 rep
baseline, escalated where the 1-rep gap was zero) and keep the top 8 with gap > 0
(saturated tasks — no gap or Haiku >= Opus — carry no signal and are dropped).
Reads prescreen/graded/verdicts.jsonl + arm_map.csv (ADR 0026 formats); writes tasks.txt.
"""
import csv, json, os

BASE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(BASE, "prescreen", "graded")
with open(os.path.join(G, "verdicts.jsonl"), encoding="utf-8") as fh:
    verdicts = {v["bid"]: v for v in (json.loads(l) for l in fh if l.strip())}
with open(os.path.join(G, "arm_map.csv"), encoding="utf-8", newline="") as fh:
    arm_map = {r["bid"]: r for r in csv.DictReader(fh)}

frac = {}
for bid, m in arm_map.items():
    v = verdicts.get(bid)
    if v is None:
        continue
    tot = v.get("total") or 0
    frac.setdefault((m["key"], m["arm"]), []).append(((v.get("met") or 0) / tot) if tot else 0.0)

keys = sorted({k for (k, _) in frac})
ranked = []
for k in keys:
    h, o = frac.get((k, "haiku")), frac.get((k, "opus"))
    if not h or not o:
        print(f"  {k}: MISSING ARM (haiku={h} opus={o}) — skipped")
        continue
    h, o = sum(h) / len(h), sum(o) / len(o)
    ranked.append((o - h, k, h, o))
ranked.sort(reverse=True)
for gap, k, h, o in ranked:
    print(f"  {k}: haiku={h:.2f} opus={o:.2f} gap={gap:+.2f}")

selected = [k for gap, k, _, _ in ranked if gap > 0][:8]
if len(selected) < 8:
    print(f"WARNING: only {len(selected)} tasks with a positive gap; main run proceeds with those")
with open(os.path.join(BASE, "tasks.txt"), "w", encoding="utf-8", newline="") as fh:
    fh.write("\n".join(selected) + "\n")
print(f"selected {len(selected)} tasks -> tasks.txt: {selected}")
