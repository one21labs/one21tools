#!/usr/bin/env python3
"""Blind the tiered-execution outputs for grading (arm withheld; ADR 0019 item 5).

Reads harness.py's per-cell driver records from <cells-dir>/*.json -- one file per
(arm, skill, eval_id, rep) cell: {skill, eval_id, arm, rep, response, ...}. Default --cells-dir is
outputs/cells/ under this benchmark directory; harness.py itself writes to ~/tiered-run/cells
inside WSL by default, so the operator copies (or robocopies) that directory here after each arm's
run -- see README "Reproduce". Discovery is by file CONTENT (skill/eval_id/arm/rep fields), not by
filename parsing, so any filename harness.py used is fine as long as every *.json in the directory
is one cell record.

Also writes the raw per-cell response text to outputs/<skill>.<eval_id>.<arm>.<rep>.txt -- the same
filename convention prior hermetic benchmarks use, so archive_raw.py's (skill, eval_id, arm) sample
grouping and the ADR 0023 on-main audit sample work unchanged.

Writes graded/items/<bid>.json = {bid, skill, eval_id, prompt, expectations, response} (NO arm),
graded/arm_map.tsv (flat records -> TSV per ADR 0026), graded/bids.json.
bid = sha256(filename)[:12] (deterministic; arm not inferable).
"""
import argparse
import hashlib
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "outputs")
G = os.path.join(BASE, "graded")
IT = os.path.join(G, "items")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cells-dir", default=os.path.join(OUT, "cells"),
        help="directory of harness.py per-cell JSON records (default: outputs/cells/)",
    )
    args = parser.parse_args()

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(IT, exist_ok=True)
    with open(os.path.join(BASE, "meta.json"), encoding="utf-8") as fh:
        meta = json.load(fh)

    if not os.path.isdir(args.cells_dir):
        print(f"WARNING: {args.cells_dir} missing -- run harness.py for all 3 arms and copy its "
              f"cells/ output here first (see README)")
        cell_files = []
    else:
        cell_files = sorted(f for f in os.listdir(args.cells_dir) if f.endswith(".json"))

    items, arm_rows = [], []
    for fname in cell_files:
        with open(os.path.join(args.cells_dir, fname), encoding="utf-8") as fh:
            r = json.load(fh)
        skill, eval_id = r.get("skill"), r.get("eval_id")
        arm, rep = r.get("arm"), r.get("rep")
        if not (skill and eval_id is not None and arm and rep is not None):
            print(f"WARNING: {fname} missing skill/eval_id/arm/rep -- skipped")
            continue
        eval_id, rep = str(eval_id), str(rep)
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


if __name__ == "__main__":
    main()
