#!/usr/bin/env python3
"""Blind the skill-benchmark outputs for grading (arm withheld; ADR 0019).

Reads outputs/<skill>.<eval_id>.<arm>.<rep>.txt, joins each with its eval prompt + expectations
(meta.json), and writes graded/items/<bid>.json = {bid, skill, eval_id, prompt, expectations,
response} (NO arm), graded/arm_map.json = bid -> {key, skill, eval_id, arm, rep}, graded/bids.json.
bid = sha256(filename)[:12] (deterministic; arm not inferable).
"""
import json, hashlib, os, glob

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "outputs")
G = os.path.join(BASE, "graded"); IT = os.path.join(G, "items")
os.makedirs(IT, exist_ok=True)
meta = json.load(open(os.path.join(BASE, "meta.json"), encoding="utf-8"))

items, arm_map = [], {}
for f in sorted(glob.glob(os.path.join(OUT, "*.txt"))):
    name = os.path.basename(f)[:-4]           # <skill>.<eval_id>.<arm>.<rep>  (skill has no dots)
    parts = name.split(".")
    if len(parts) != 4:
        continue
    skill, eval_id, arm, rep = parts
    if arm not in ("with", "without"):
        continue
    key = f"{skill}.{eval_id}"
    m = meta.get(key)
    if not m:
        continue
    text = open(f, encoding="utf-8", errors="replace").read().strip()
    bid = hashlib.sha256(name.encode()).hexdigest()[:12]
    json.dump({"bid": bid, "skill": skill, "eval_id": eval_id, "prompt": m["prompt"],
               "expectations": m["expectations"], "response": text},
              open(os.path.join(IT, bid + ".json"), "w", encoding="utf-8"), indent=1)
    arm_map[bid] = {"key": key, "skill": skill, "eval_id": eval_id, "arm": arm, "rep": rep}
    items.append(bid)

json.dump(arm_map, open(os.path.join(G, "arm_map.json"), "w", encoding="utf-8"), indent=1)
json.dump(sorted(items), open(os.path.join(G, "bids.json"), "w", encoding="utf-8"))
print(f"blinded {len(items)} outputs -> graded/items/ ; arm map + bids written")
empties = [b for b in items if not json.load(open(os.path.join(IT, b + ".json")))["response"]]
if empties:
    print(f"WARNING: {len(empties)} empty responses: {empties[:10]}")
