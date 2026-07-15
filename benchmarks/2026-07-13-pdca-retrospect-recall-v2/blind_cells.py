#!/usr/bin/env python3
"""Operator-side blinding for the I1 v2 grid (pre-registration: README.md).

Successor to ../2026-07-12-pdca-retrospect-recall/blind_cells.py (frozen; never edited). Same
blinding shape -- lib/blind.py's write_blinded only passes each record's response text through
(it has no opinion on response SCHEMA), so this stays a response passthrough exactly like v1;
normalization to the v2 neutral schema {claim, evidence-cite, proposed-remedy} happens downstream
in the grading workflow's Normalize phase (the routing-aware successor to v1's
grade.workflow.js), not here.

Reads outputs/*.json cell records -> writes, via the lib layer (ADR 0052 decision 4):
  graded/items/<bid>.json   {bid, substrate, response} -- NO arm
  graded/arm_map.tsv        the aggregator's join (ADR 0026 flat-record format)
  graded/keys/<sub>.json    the grading key: that substrate's seeds with class, site,
                            found_iff predicate, AND (v2 delta 3) routing_key -- triage credit
                            (found+routed=1.0, found only=0.5) needs the routing target the
                            grader checks against, sourced from seeds.json + substrates/sites.json
  graded/audit_bids.json    8 bids for the guess-the-arm audit -- deterministic stratified
                            sample (first rep-1 cell per arm per substrate order, 4 per arm),
                            arms NOT included (aggregate.py joins them back to score)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skill-bench" / "scripts" / "lib"))
import bench_io  # noqa: E402
from blind import write_blinded  # noqa: E402


def main():
    records = [json.loads(p.read_text(encoding="utf-8"))
               for p in sorted((HERE / "outputs").glob("*.json"))]
    records = [r for r in records if not r["summary"]["error"]]
    graded = HERE / "graded"
    arm_map = write_blinded(records, graded, lambda r: r["cell"],
                            lambda r: {"substrate": r["substrate"], "response": r["response"]})
    for m, r in zip(arm_map, records):
        m["substrate"], m["rep"] = r["substrate"], r["rep"]
    bench_io.dump_records(arm_map, str(graded / "arm_map.tsv"), fmt="tsv")

    seeds = json.loads((HERE / "seeds.json").read_text(encoding="utf-8"))
    sites = json.loads((HERE / "substrates" / "sites.json").read_text(encoding="utf-8"))["seeds"]
    keys = HERE / "graded" / "keys"
    keys.mkdir(exist_ok=True)
    subs = set(r["substrate"] for r in records)
    for sub in subs:
        entries = [{"class": s["class"], "site": s["site"],
                    "found_iff": seeds["classes"][s["class"]]["found_iff"],
                    "routing_key": seeds["classes"][s["class"]]["routing_key"]}
                   for s in sites if s["substrate"] == sub]
        expected = len(seeds["assignment"].get(sub, []))
        if len(entries) != expected:
            raise SystemExit(f"{sub}: {len(entries)} sites vs {expected} assigned seeds")
        (keys / f"{sub}.json").write_text(json.dumps(entries, indent=1), encoding="utf-8")

    by_arm = {"A": [], "C": []}
    for m, r in zip(arm_map, records):
        if r["rep"] == 1:
            by_arm[r["arm"]].append(m["bid"])
    audit = sorted(by_arm["A"])[:4] + sorted(by_arm["C"])[:4]
    (graded / "audit_bids.json").write_text(json.dumps(sorted(audit)), encoding="utf-8")
    print(f"blinded {len(records)} cells; keys (with routing_key) for {sorted(subs)}; "
          f"audit sample {len(audit)}")


if __name__ == "__main__":
    main()
