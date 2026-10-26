#!/usr/bin/env python3
"""Secondary metric (metadata.json): numbers a reply states that its task never gave.

The failure #328 names is an invented setpoint or trip value. This counts the mechanical floor of
it: numeric values in the reply absent from the task text. Identifiers are not values, so a digit
run glued to letters or a hyphenated tag (SP-07, LT-201, FR-K100-003, ISA-106) is skipped, as are
list and step ordinals 0-20. A count is a pointer for reading cells, never a grade.

Usage: python3 invented.py --dirs outputs  -> graded/invented-<dirs>.json + per-arm table
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
NUM = re.compile(r"(?<![\w.-])(\d+(?:[.,]\d+)*)(?![\w-])")
ORDINAL_MAX = 20


def values(text):
    out = set()
    for m in NUM.finditer(text):
        v = m.group(1).replace(",", "")
        try:
            f = float(v)
        except ValueError:
            continue
        if f.is_integer() and 0 <= f <= ORDINAL_MAX:
            continue
        out.add(f)
    return out


def absent(task, reply):
    return sorted(values(reply) - values(task))


def main():
    from grid import EVALS
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="+", default=["outputs"])
    args = ap.parse_args()
    cells, by_arm = [], defaultdict(list)
    for d in args.dirs:
        for p in sorted((HERE / d).glob("*.json")):
            r = json.loads(p.read_text(encoding="utf-8"))
            if r["summary"]["error"]:
                continue
            extra = absent(EVALS[r["scenario"]]["task"], r["response"] or "")
            cells.append({"cell": r["cell"], "model": r["model"], "arm": r["arm"], "absent": extra})
            by_arm[(r["model"], r["arm"])].append(len(extra))
    tag = "-".join(Path(d).name for d in args.dirs)
    (HERE / "graded").mkdir(exist_ok=True)
    (HERE / "graded" / f"invented-{tag}.json").write_text(json.dumps(cells, indent=1) + "\n",
                                                          encoding="utf-8")
    for (model, arm), ns in sorted(by_arm.items()):
        print(f"{model:18s} {arm:8s} cells={len(ns):3d} mean_absent={sum(ns) / len(ns):.2f} "
              f"cells_with_any={sum(1 for n in ns if n)}")


if __name__ == "__main__":
    main()
