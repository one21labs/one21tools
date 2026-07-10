#!/usr/bin/env python3
"""Blind the never-section re-run outputs for grading (issue #72, ADR 0034), WITHOUT touching the
original run's graded/ artifacts.

Adapted from blind.py. The original run's 24 never.* cells used the SAME task ids this re-run
reuses for n1-n4 (only n4b is new), so blind.py's bid = sha256(filename)[:12] would collide:
"never.n1_ci_gate.with.1.txt" hashes identically whether it's the OLD run's file or this re-run's
file, silently overwriting graded/items/<bid>.json and graded/arm_map.tsv rows the original
verdicts.jsonl / verdicts-2026-07-09-regrade.jsonl still key off. This script instead:
  - bids the "rerun." + filename string (a distinct namespace; no collision with blind.py's bids)
  - writes items into the SAME graded/items/ dir (safe: bids differ, so no file is overwritten)
  - writes a SEPARATE arm-map extension graded/arm_map-2026-07-10-neverrerun.tsv (same 6-column
    schema as graded/arm_map.tsv) instead of appending to/overwriting the original arm_map.tsv
  - writes graded/bids-2026-07-10-neverrerun.json (the bids list to pass to grade.workflow.js's
    `bids` arg) instead of overwriting graded/bids.json

Reads rerun-outputs/<section>.<task_id>.<arm>.<rep>.txt, joins each with its prompt + single
expectation (meta.json -- prep.py must have been (re-)run against the redesigned tasks.json first).
ALL writes use newline='' (avoids CRLF corruption on Windows).
"""
import json, hashlib, os, glob

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "rerun-outputs")
G = os.path.join(BASE, "graded"); IT = os.path.join(G, "items")
LABEL = "2026-07-10-neverrerun"
os.makedirs(IT, exist_ok=True)
with open(os.path.join(BASE, "meta.json"), encoding="utf-8") as fh:
    meta = json.load(fh)

items, arm_rows = [], []
for f in sorted(glob.glob(os.path.join(OUT, "*.txt"))):
    name = os.path.basename(f)[:-4]           # <section>.<task_id>.<arm>.<rep>  (no dots in parts)
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
    bid = hashlib.sha256(("rerun." + name).encode()).hexdigest()[:12]   # distinct namespace
    with open(os.path.join(IT, bid + ".json"), "w", encoding="utf-8", newline="") as wfh:
        json.dump({"bid": bid, "section": section, "task_id": task_id, "prompt": m["prompt"],
                   "expectations": m["expectations"], "response": text},
                  wfh, ensure_ascii=False, separators=(",", ":"))
    arm_rows.append((bid, key, section, task_id, arm, rep))
    items.append(bid)

with open(os.path.join(G, f"arm_map-{LABEL}.tsv"), "w", encoding="utf-8", newline="") as fh:
    fh.write("bid\tkey\tsection\ttask_id\tarm\trep\n")
    for row in arm_rows:
        fh.write("\t".join(row) + "\n")
with open(os.path.join(G, f"bids-{LABEL}.json"), "w", encoding="utf-8", newline="") as fh:
    json.dump(sorted(items), fh, separators=(",", ":"))

print(f"blinded {len(items)} never-rerun outputs -> graded/items/ ; "
      f"arm_map-{LABEL}.tsv + bids-{LABEL}.json written (original arm_map.tsv/bids.json untouched)")
empties = []
for b in items:
    with open(os.path.join(IT, b + ".json"), encoding="utf-8") as fh:
        if not json.load(fh)["response"]:
            empties.append(b)
if empties:
    print(f"WARNING: {len(empties)} empty responses: {empties[:10]}")
