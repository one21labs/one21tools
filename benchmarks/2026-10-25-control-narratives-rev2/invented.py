#!/usr/bin/env python3
"""Secondary metric (metadata.json): numbers a reply states that its task never gave.

The failure #328 names is an invented setpoint or trip value. This counts the mechanical floor of
it: numeric values in the reply absent from the task text. Negatives (-40), both ends of a range
(85-95) and clock times (10:30, one value) count. Identifiers and citations are not values, so a
digit run glued to letters or a hyphenated tag (SP-07, LT-201, FR-K100-003, ISA-106), a standards
designation (IEC 61511-1, ISO 9001:2015, ISA 18.2) and a written date (Jan 2025, 30 Nov 2026) are
skipped, as are list and step ordinals 0-20. Blind spots: an invented value of 0-20, one glued to
its unit or a word (85C, 30-second), or one spelled out. A number the treatment itself states
("25 max", "5.06 sequence tables") is not counted in EITHER arm, so the skill text cannot bias
the with arm. Cells grade.py excluded are skipped, so both metrics cover the same cells. A count
is a pointer for reading cells, never a grade.

Each cell also lists the standards it cites that neither its task nor the treatment gave
(`cites`): the input to the citation fact-check (metadata.json metrics), not a count of errors.

Usage: python3 invented.py --dirs outputs  -> graded/invented-<dirs>.json + per-arm table
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BODIES = "ANSI|API|ASME|EN|IEC|IEEE|ISA|ISO|NFPA"
MONTHS = ("Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?"
          "|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?")
NUM = r"\d+(?:[.,]\d+)*"
# The leftmost match wins, so a citation or date consumes its digits before the value branches.
TOKEN = re.compile(
    rf"\b(?:{BODIES})(?:/(?:{BODIES}))*\s+\d+(?:[.:-]\d+)*"
    rf"|\b(?:\d{{1,2}}\s+)?(?:{MONTHS})\.?\s+(?:\d{{1,2}},?\s+)?(?:19|20)\d\d\b"
    r"|(?<![\w.:])(?P<clock>(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?)(?!\w|[:.,]\d)"
    rf"|(?<![\w.\-\u2212])(?P<lo>[-\u2212]?{NUM})(?:-(?P<hi>{NUM}))?(?![\w-])")
ORDINAL_MAX = 20


def values(text):
    out = set()
    # A tolerance is not a negative: +/-2 reads as the plus-minus sign does, unsigned.
    for m in TOKEN.finditer(text.replace("+/-", "\u00b1")):
        if m["clock"]:
            hour, _, rest = m["clock"].partition(":")
            out.add(f"{int(hour)}:{rest}")
        for v in filter(None, (m["lo"], m["hi"])):
            try:
                f = float(v.replace(",", "").replace("\u2212", "-"))
            except ValueError:
                continue
            if f.is_integer() and 0 <= f <= ORDINAL_MAX:
                continue
            out.add(f)
    return out


def absent(task, reply, given=frozenset()):
    """Values in reply that neither the task nor `given` (the treatment's own values) states."""
    # Clock times are strings; they sort after the numbers.
    return sorted(values(reply) - values(task) - given, key=lambda v: (isinstance(v, str), v))


# Wider than TOKEN's citation branch: hyphenated and prefixed forms too (ISA-18.2, ASD-STE100,
# ANSI/ISA-5.06.01-2007, NAMUR NE 107), since this lists citations rather than skipping digits.
CITE = re.compile(rf"\b(?:ANSI/)?(?:{BODIES}|ASD|NAMUR)(?:/(?:{BODIES}))*[- ]?"
                  r"(?:TR|STE|NE ?)?\d+(?:[.:-]\d+)*")


def cites(text):
    return {re.sub(r"\s+", " ", m.group(0)) for m in CITE.finditer(text)}


def new_cites(task, reply, given=frozenset()):
    return sorted(cites(reply) - cites(task) - given)


def main():
    from grid import EVALS
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="+", default=["outputs"])
    args = ap.parse_args()
    tag = "-".join(Path(d).name for d in args.dirs)
    errs = HERE / "graded" / f"error-cells-{tag}.json"
    if not errs.exists():
        sys.exit(f"{errs.name} missing: run grade.py --dirs {' '.join(args.dirs)} first, so this "
                 "metric covers the same cells as the grade")
    excluded = {e["cell"] for e in json.loads(errs.read_text(encoding="utf-8"))}
    treatment = (HERE / "treatments" / "control-narratives.txt").read_text(encoding="utf-8")
    given_vals, given_cites = frozenset(values(treatment)), frozenset(cites(treatment))
    cells, by_arm = [], defaultdict(list)
    for d in args.dirs:
        for p in sorted((HERE / d).glob("*.json")):
            r = json.loads(p.read_text(encoding="utf-8"))
            if r["summary"]["error"] or r["cell"] in excluded:
                continue
            task, reply = EVALS[r["scenario"]]["task"], r["response"] or ""
            extra = absent(task, reply, given_vals)
            cells.append({"cell": r["cell"], "model": r["model"], "arm": r["arm"], "absent": extra,
                          "cites": new_cites(task, reply, given_cites)})
            by_arm[(r["model"], r["arm"])].append(len(extra))
    (HERE / "graded").mkdir(exist_ok=True)
    (HERE / "graded" / f"invented-{tag}.json").write_text(json.dumps(cells, indent=1) + "\n",
                                                          encoding="utf-8")
    for (model, arm), ns in sorted(by_arm.items()):
        print(f"{model:18s} {arm:8s} cells={len(ns):3d} mean_absent={sum(ns) / len(ns):.2f} "
              f"cells_with_any={sum(1 for n in ns if n)}")


if __name__ == "__main__":
    main()
