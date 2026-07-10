"""Regenerate graded/mechanized.csv from the run's cell records.

Applies benchmarks/lib/mechanized_checks.py to every cell's response text
(one CSV row per applicable check, ADR 0026 flat-table format). The compound
expectation (code-standards, 4, 1) is excluded: its realism check showed the
bundled silent-discard clause needs judgment a regex cannot own.
"""
import csv
import glob
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "..", "lib"))
import mechanized_checks as mc

EXCLUDED = {("code-standards", 4, 1)}


def main(cells_dir=os.path.join(BASE, "outputs", "cells")):
    checks = {k: v for k, v in mc.CHECKS.items() if k not in EXCLUDED}
    rows = []
    for f in sorted(glob.glob(os.path.join(cells_dir, "*.json"))):
        c = json.load(open(f, encoding="utf-8"))
        text = c.get("response", "")
        for (skill, eval_id, idx), fn in checks.items():
            if skill == c["skill"] and eval_id == int(c["eval_id"]):
                rows.append([c["skill"], c["eval_id"], c["arm"], c["rep"], idx, int(bool(fn(text)))])
    out = os.path.join(BASE, "graded", "mechanized.csv")
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["skill", "eval_id", "arm", "rep", "check_idx", "passed"])
        w.writerows(rows)
    print(f"{len(rows)} check rows -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:])
