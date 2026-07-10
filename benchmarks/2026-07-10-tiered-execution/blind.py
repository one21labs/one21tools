#!/usr/bin/env python3
"""Blind the tiered-execution outputs for grading (arm withheld; ADR 0019 item 5).

Reads outputs/<arm>.json for each arm in ARMS -- the `result` persisted from a harness.workflow.js
Workflow run for that arm (benchmarks/lib/README.md persist convention: task .output "result"
field). Each record is {skill, eval_id, arm, rep, response, ...tiered-only diagnostics}.

Also writes the raw per-cell response text to outputs/<skill>.<eval_id>.<arm>.<rep>.txt -- the same
filename convention prior hermetic benchmarks use, so archive_raw.py's (skill, eval_id, arm) sample
grouping and the ADR 0023 on-main audit sample work unchanged.

Writes graded/items/<bid>.json = {bid, skill, eval_id, prompt, expectations, response} (NO arm),
graded/arm_map.tsv (flat records -> TSV per ADR 0026), graded/bids.json.
bid = sha256(filename)[:12] (deterministic; arm not inferable).
"""
import json, hashlib, os

ARMS = ("sonnet-solo", "haiku-solo", "tiered")
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "outputs")
G = os.path.join(BASE, "graded"); IT = os.path.join(G, "items")
os.makedirs(OUT, exist_ok=True)
os.makedirs(IT, exist_ok=True)
with open(os.path.join(BASE, "meta.json"), encoding="utf-8") as fh:
    meta = json.load(fh)

items, arm_rows = [], []
for arm in ARMS:
    path = os.path.join(OUT, f"{arm}.json")
    if not os.path.exists(path):
        print(f"WARNING: {path} missing -- run + persist the Workflow for arm={arm} first (see README)")
        continue
    with open(path, encoding="utf-8") as fh:
        result = json.load(fh)
    records = result.get("records", []) if isinstance(result, dict) else result
    for r in records:
        skill, eval_id, rep = r["skill"], str(r["eval_id"]), str(r["rep"])
        key = f"{skill}.{eval_id}"
        m = meta.get(key)
        if not m:
            print(f"WARNING: no meta.json entry for {key} -- skipped")
            continue
        text = (r.get("response") or "").strip()
        name = f"{skill}.{eval_id}.{arm}.{rep}"
        with open(os.path.join(OUT, name + ".txt"), "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        bid = hashlib.sha256(name.encode()).hexdigest()[:12]
        with open(os.path.join(IT, bid + ".json"), "w", encoding="utf-8") as fh:
            json.dump({"bid": bid, "skill": skill, "eval_id": eval_id, "prompt": m["prompt"],
                       "expectations": m["expectations"], "response": text}, fh, indent=1)
        arm_rows.append((bid, key, skill, eval_id, arm, rep))
        items.append(bid)

with open(os.path.join(G, "arm_map.tsv"), "w", encoding="utf-8", newline="") as fh:
    fh.write("bid\tkey\tskill\teval_id\tarm\trep\n")
    for row in arm_rows:
        fh.write("\t".join(row) + "\n")
with open(os.path.join(G, "bids.json"), "w", encoding="utf-8") as fh:
    json.dump(sorted(items), fh)
print(f"blinded {len(items)} outputs -> graded/items/ ; arm_map.tsv + bids.json written")

empties = []
for b in items:
    with open(os.path.join(IT, b + ".json"), encoding="utf-8") as fh:
        if not json.load(fh)["response"]:
            empties.append(b)
if empties:
    print(f"WARNING: {len(empties)} empty responses: {empties[:10]}")
