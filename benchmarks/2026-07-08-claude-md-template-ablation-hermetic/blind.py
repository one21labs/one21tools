#!/usr/bin/env python3
"""Blind the hermetic-ablation outputs for grading.

Reads outputs/<task>.<arm>.<rep>.txt, joins each with its task prompt (tasks.json), and emits:
  graded/blinded.json  -> list of {bid, task, prompt, response} with the ARM WITHHELD (ADR 0019
                          blind-grading: the grader never sees which arm produced a response).
  graded/arm_map.json  -> bid -> {task, arm, rep}, revealed only at aggregation.
bid = sha256(filename)[:12] — deterministic, no RNG (workflow-resume safe), arm not inferable.
"""
import json, hashlib, os, glob

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "outputs")
G = os.path.join(BASE, "graded"); os.makedirs(G, exist_ok=True)
with open(os.path.join(BASE, "tasks.json"), encoding="utf-8") as fh:
    PROMPTS = json.load(fh)

items = []
for f in sorted(glob.glob(os.path.join(OUT, "*.txt"))):
    name = os.path.basename(f)[:-4]              # strip .txt
    parts = name.split(".")                      # task ids contain no dots
    if len(parts) < 3:
        continue
    task, arm, rep = ".".join(parts[:-2]), parts[-2], parts[-1]
    if arm not in ("with", "without"):
        continue
    with open(f, encoding="utf-8", errors="replace") as fh:
        text = fh.read().strip()
    bid = hashlib.sha256(name.encode()).hexdigest()[:12]
    items.append({"bid": bid, "task": task, "arm": arm, "rep": rep,
                  "prompt": PROMPTS.get(task, ""), "response": text})

items.sort(key=lambda x: x["bid"])               # shuffle away filesystem order
blinded = [{"bid": it["bid"], "task": it["task"], "prompt": it["prompt"],
            "response": it["response"]} for it in items]
arm_map = {it["bid"]: {"task": it["task"], "arm": it["arm"], "rep": it["rep"]} for it in items}

with open(os.path.join(G, "blinded.json"), "w", encoding="utf-8") as fh:
    json.dump(blinded, fh, indent=1)
with open(os.path.join(G, "arm_map.json"), "w", encoding="utf-8") as fh:
    json.dump(arm_map, fh, indent=1)

# per-item files so blind graders read one small file each (no arm, no giant round-trip)
IT = os.path.join(G, "items"); os.makedirs(IT, exist_ok=True)
for b in blinded:
    with open(os.path.join(IT, b["bid"] + ".json"), "w", encoding="utf-8") as fh:
        json.dump(b, fh, indent=1)
with open(os.path.join(G, "bids.json"), "w", encoding="utf-8") as fh:
    json.dump([b["bid"] for b in blinded], fh)
empty = [it["bid"] for it in items if not it["response"]]
print(f"blinded {len(blinded)} outputs -> graded/blinded.json ; arm map -> graded/arm_map.json")
if empty:
    print(f"WARNING: {len(empty)} empty responses (executor errors?): {empty}")
