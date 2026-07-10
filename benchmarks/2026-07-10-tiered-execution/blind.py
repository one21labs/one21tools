#!/usr/bin/env python3
"""Blind the tiered-execution benchmark outputs for grading (arm withheld; ADR 0019).

Reads <OUTDIR>/<skill>.<eval_id>.<arm>.<rep>.txt (arm in haiku|sonnet|opus|tiered), joins each
with its prompt + expectations (meta.json), writes <GRADEDIR>/items/<bid>.json = {bid, key,
prompt, expectations, response} (NO arm — the grader cannot know which configuration produced
the text), <GRADEDIR>/arm_map.csv (flat record table -> CSV per ADR 0026), <GRADEDIR>/bids.json.
bid = sha256(filename)[:12]. OUTDIR/GRADEDIR env-overridable so the pre-screen and the main
run keep separate grade sets.
"""
import csv, json, hashlib, os, glob

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("OUTDIR", os.path.join(BASE, "outputs"))
G = os.environ.get("GRADEDIR", os.path.join(BASE, "graded"))
IT = os.path.join(G, "items")
os.makedirs(IT, exist_ok=True)
with open(os.path.join(BASE, "meta.json"), encoding="utf-8") as fh:
    meta = json.load(fh)

ARMS = {"haiku", "sonnet", "opus", "tiered"}
items, arm_map = [], {}
for f in sorted(glob.glob(os.path.join(OUT, "*.txt"))):
    name = os.path.basename(f)[:-4]            # <skill>.<eval_id>.<arm>.<rep> (skill has no dots)
    parts = name.split(".")
    if len(parts) != 4 or parts[2] not in ARMS:
        continue
    skill, eval_id, arm, rep = parts
    key = f"{skill}.{eval_id}"
    m = meta.get(key)
    if not m:
        continue
    with open(f, encoding="utf-8", errors="replace") as fh:
        text = fh.read().strip()
    bid = hashlib.sha256(name.encode()).hexdigest()[:12]
    with open(os.path.join(IT, bid + ".json"), "w", encoding="utf-8") as fh:
        json.dump({"bid": bid, "key": key, "prompt": m["prompt"],
                   "expectations": m["expectations"], "response": text}, fh, indent=1)
    arm_map[bid] = {"key": key, "skill": skill, "eval_id": eval_id, "arm": arm, "rep": rep}
    items.append(bid)

with open(os.path.join(G, "arm_map.csv"), "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["bid", "key", "skill", "eval_id", "arm", "rep"])
    for bid in sorted(arm_map):
        m = arm_map[bid]
        w.writerow([bid, m["key"], m["skill"], m["eval_id"], m["arm"], m["rep"]])
with open(os.path.join(G, "bids.json"), "w", encoding="utf-8") as fh:
    json.dump(sorted(items), fh)
print(f"blinded {len(items)} outputs -> {IT} ; arm map + bids written")
empties = [b for b in items
           if not json.load(open(os.path.join(IT, b + ".json"), encoding="utf-8"))["response"]]
if empties:
    print(f"WARNING: {len(empties)} empty responses: {empties[:10]}")
