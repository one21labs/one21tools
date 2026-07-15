#!/usr/bin/env python3
"""Operator-side blinding for the poker grid (pre-registration: README.md).

Same recipe as the audited I2/armd blinding: outputs/*.json -> graded/items/<bid>.json
{bid, scenario, response} (NO arm; cell-written decision artifacts folded into the response
text so artifact presence cannot tell the arm; framer/advisor/round-2 poker records are cell
INPUTS and are never included), arm_map.tsv, keys.json from the frozen I2 scenarios.json,
audit_bids.json (9 = 3 per arm A/C/P, deterministic rep-1 sample).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "skill-bench" / "scripts" / "lib"))
import bench_io  # noqa: E402
from blind import write_blinded  # noqa: E402

I2 = HERE.parent / "2026-07-12-pdca-decide-outcome"
SCENARIO_SRC = {
    "B1": "scenario-b1/snapshot", "B2": "scenario-b1/snapshot",
    "B3": "scenario-b3/snapshot", "B4": "scenario-b4/snapshot",
    "S1": "scenario-s1/workdir", "S2": "scenario-s2/workdir",
    "S3": "scenario-s3/workdir", "S4": "scenario-s4/workdir",
}
_preexisting = {}


def preexisting(scenario):
    if scenario not in _preexisting:
        src = I2 / SCENARIO_SRC[scenario]
        _preexisting[scenario] = {str(p.relative_to(src))
                                  for p in src.rglob("*.md")
                                  if str(p.relative_to(src)).startswith(("docs/decisions/",
                                                                         "decisions/"))}
    return _preexisting[scenario]


def merged_response(r):
    text = r["response"] or ""
    old = preexisting(r["scenario"])
    for rel, body in (r.get("artifacts") or {}).items():
        if rel not in old:
            text += f"\n\n--- recorded decision file {rel} ---\n{body}"
    return text


def main():
    records = [json.loads(p.read_text(encoding="utf-8"))
               for p in sorted((HERE / "outputs").glob("*.json"))]
    records = [r for r in records if not r["summary"]["error"]]
    graded = HERE / "graded"
    arm_map = write_blinded(records, graded, lambda r: r["cell"],
                            lambda r: {"scenario": r["scenario"],
                                       "response": merged_response(r)})
    for m, r in zip(arm_map, records):
        m["scenario"], m["rep"] = r["scenario"], r["rep"]
    bench_io.dump_records(arm_map, str(graded / "arm_map.tsv"), fmt="tsv")

    spec = json.loads((I2 / "scenarios.json").read_text(encoding="utf-8"))
    keys = {}
    for b in spec["backtests"]:
        keys[b["id"]] = {"type": "backtest", "question": b["question_as_faced"],
                         "outcome_key": b["outcome_key"]}
    for s in spec["synthetic"]:
        keys[s["id"]] = {"type": "synthetic", "shape": s["shape"], "trap": s["trap"],
                         "expectations": s["expectations"]}
    (graded / "keys.json").write_text(json.dumps(keys, indent=1), encoding="utf-8")

    by_arm = {}
    for m, r in zip(arm_map, records):
        if r["rep"] == 1:
            by_arm.setdefault(r["arm"], []).append(m["bid"])
    audit = sorted(sum((sorted(v)[:3] for v in by_arm.values()), []))
    (graded / "audit_bids.json").write_text(json.dumps(audit), encoding="utf-8")
    print(f"blinded {len(records)} cells -> {graded}; audit sample {len(audit)}")


if __name__ == "__main__":
    main()
