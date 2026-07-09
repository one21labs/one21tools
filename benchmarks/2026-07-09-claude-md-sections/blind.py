#!/usr/bin/env python3
"""Blind the section-ablation outputs for grading (arm withheld; ADR 0019).

Reads outputs/<section>.<task_id>.<arm>.<rep>.txt, joins each with its prompt + single expectation
(meta.json), and writes graded/items/<bid>.json = {bid, section, task_id, prompt, expectations,
response} (NO arm; minified), graded/arm_map.tsv (bid<TAB>key<TAB>section<TAB>task_id<TAB>arm<TAB>rep
— uniform records, TSV is the cheapest form), and graded/bids.json. bid = sha256(filename)[:12]
(deterministic; arm not inferable). ALL writes use newline='' (avoids CRLF corruption on Windows).
"""
import json, hashlib, os, glob

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "outputs")
G = os.path.join(BASE, "graded"); IT = os.path.join(G, "items")
os.makedirs(IT, exist_ok=True)
with open(os.path.join(BASE, "meta.json"), encoding="utf-8") as fh:
    meta = json.load(fh)

items, arm_rows = [], []
for f in sorted(glob.glob(os.path.join(OUT, "*.txt"))):
    name = os.path.basename(f)[:-4]           # <section>.<task_id>.<arm>.<rep>  (no dots in the parts)
    parts = name.split(".")
    if len(parts) != 4:
        continue
    section, task_id, arm, rep = parts
    if arm not in ("with", "without"):
        continue
    key = f"{section}.{task_id}"
    m = meta.get(key)
    if not m:
        continue
    with open(f, encoding="utf-8", errors="replace") as rfh:
        text = rfh.read().strip()
    bid = hashlib.sha256(name.encode()).hexdigest()[:12]
    with open(os.path.join(IT, bid + ".json"), "w", encoding="utf-8", newline="") as wfh:
        json.dump({"bid": bid, "section": section, "task_id": task_id, "prompt": m["prompt"],
                   "expectations": m["expectations"], "response": text},
                  wfh, ensure_ascii=False, separators=(",", ":"))
    arm_rows.append((bid, key, section, task_id, arm, rep))
    items.append(bid)

with open(os.path.join(G, "arm_map.tsv"), "w", encoding="utf-8", newline="") as fh:
    fh.write("bid\tkey\tsection\ttask_id\tarm\trep\n")
    for row in arm_rows:
        fh.write("\t".join(row) + "\n")
with open(os.path.join(G, "bids.json"), "w", encoding="utf-8", newline="") as fh:
    json.dump(sorted(items), fh, separators=(",", ":"))

print(f"blinded {len(items)} outputs -> graded/items/ ; arm_map.tsv + bids.json written")
empties = []
for b in items:
    with open(os.path.join(IT, b + ".json"), encoding="utf-8") as fh:
        if not json.load(fh)["response"]:
            empties.append(b)
if empties:
    print(f"WARNING: {len(empties)} empty responses: {empties[:10]}")
