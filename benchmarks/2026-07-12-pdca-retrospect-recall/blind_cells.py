#!/usr/bin/env python3
"""Operator-side blinding for the I1 grid (pre-registration: README.md).

Reads outputs/*.json cell records -> writes, via the lib layer (ADR 0052 decision 4):
  graded/items/<bid>.json   {bid, substrate, response} — NO arm
  graded/arm_map.tsv        the aggregator's join (ADR 0026 flat-record format)
  graded/keys/<sub>.json    the grading key: that substrate's seeds with class, site and
                            found-iff predicate (from seeds.json + substrates/sites.json);
                            clean substrates get an empty seed list
  graded/audit_bids.json    8 bids for the guess-the-arm audit — deterministic stratified
                            sample (first rep-1 cell per arm per substrate order, 4 per arm),
                            arms NOT included (aggregate.py joins them back to score)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
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
                    "found_iff": seeds["classes"][s["class"]]["found_iff"]}
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
    print(f"blinded {len(records)} cells; keys for {sorted(subs)}; audit sample {len(audit)}")


if __name__ == "__main__":
    main()
