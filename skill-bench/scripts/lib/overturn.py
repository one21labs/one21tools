#!/usr/bin/env python3
"""Arm-asymmetric judge-overturn check (#191 item 5). Stdlib only, pure core + thin CLI.

The scar (#185): the prosecutor overturned arm P's "300/day" decision on anchoring while
arm C's identical "300/day" passed — same decision, different verdict, split across arms.
Post-grading, this check flags such pairs so a human samples them for judge consistency
BEFORE interpreting a bar. It is an inspection aid, not a gate: flagged pairs are
candidates, and cross-arm splits can be legitimate (surrounding record quality differs).

The decision signature is extracted from each cell's normalized text by a PRE-REGISTERED
regex (scenario-specific, e.g. r"\\b\\d+\\s*/\\s*day\\b" for a rate-limit decision). Cells in
the same scenario with equal signatures, different arms, and a different verdict on the
same expectation are overturn candidates.

Usage: python3 overturn.py --dir <benchmark dir> --pattern <regex> [--out <path>]
Reads graded/verdicts.jsonl + graded/arm_map.tsv read-only; always exits 0 with a report.
"""
import re


def decision_signature(norm, pattern):
    """First match of the pre-registered regex in the normalized text, or None."""
    m = re.search(pattern, norm or "")
    return m.group(0) if m else None


def overturn_candidates(cells, norms, pattern):
    """Flag same-decision-different-verdict splits across arms.

    cells: [{bid, arm, scenario, met: {exp_id: bool}}]; norms: {bid: normalized text}.
    Returns [{scenario, signature, exp, passed, failed}] sorted for stable output, where
    passed/failed are [(arm, bid)] lists and at least one passing and one failing cell sit
    in DIFFERENT arms (same-arm splits are rep noise, not judge asymmetry).
    """
    groups = {}
    for c in cells:
        sig = decision_signature(norms.get(c["bid"]), pattern)
        if sig is None:
            continue
        for exp, met in c["met"].items():
            groups.setdefault((c["scenario"], sig, exp), []).append((c["arm"], c["bid"], met))
    out = []
    for (scenario, sig, exp), members in sorted(groups.items(), key=lambda kv: str(kv[0])):
        passed = [(a, b) for a, b, met in members if met]
        failed = [(a, b) for a, b, met in members if not met]
        cross_arm = any(pa != fa for pa, _ in passed for fa, _ in failed)
        if passed and failed and cross_arm:
            out.append({"scenario": scenario, "signature": sig, "exp": exp,
                        "passed": sorted(passed), "failed": sorted(failed)})
    return out


def main(argv):
    import argparse
    import json
    import os
    import sys
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--pattern", required=True,
                    help="pre-registered decision-signature regex (state it in the pre-registration)")
    ap.add_argument("--out", default="-")
    a = ap.parse_args(argv[1:])

    amap = {}
    with open(os.path.join(a.dir, "graded/arm_map.tsv")) as f:
        for line in f:
            if line.startswith("bid"):
                continue
            b, arm, scn, _ = line.strip().split("\t")
            amap[b] = (arm, scn)
    cells, norms = [], {}
    with open(os.path.join(a.dir, "graded/verdicts.jsonl")) as f:
        for line in f:
            v = json.loads(line)
            if v.get("bid") not in amap or "error" in v:
                continue
            arm, scn = amap[v["bid"]]
            norms[v["bid"]] = v.get("norm", "")
            cells.append({"bid": v["bid"], "arm": arm, "scenario": scn,
                          "met": {e["id"]: e["met"] for e in v.get("expectations", [])}})

    flagged = overturn_candidates(cells, norms, a.pattern)
    report = {"dir": a.dir, "pattern": a.pattern, "n_cells": len(cells),
              "n_flagged": len(flagged), "candidates": flagged,
              "note": "inspection aid: sample flagged pairs for judge consistency before "
                      "interpreting any bar they contribute to"}
    js = json.dumps(report, indent=1)
    if a.out == "-":
        print(js)
    else:
        with open(a.out, "w") as f:
            f.write(js)
        print(f"wrote {a.out}", file=sys.stderr)


if __name__ == "__main__":
    import sys
    main(sys.argv)
