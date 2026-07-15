#!/usr/bin/env python3
"""Canonical blinding TEMPLATE (#170) — the operator-side recipe audited across I2/armd/poker.

COPY into a dated benchmark dir and adapt the `ADAPT` blocks. The recipe you keep:

  outputs/*.json -> graded/items/<bid>.json {bid, scenario, response} — NO arm field; any
  cell-written decision artifacts are folded into the response text so artifact PRESENCE
  cannot tell the arm. Arm-side inputs (advisor tables, framer output) are never included.
  Also written: arm_map.tsv (the join the aggregator uses), keys.json (the grading key per
  scenario), audit_bids.json (the guess-the-arm sample validating the blinding).

#191 hardening baked in: ERROR cells are split out mechanically (classify_cells) before
blinding — infrastructure, never quality zeros — and the capture-symmetry sweep runs BEFORE
blinding; a skewed sweep aborts (fix the harness, don't grade the skew).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# ADAPT: path to skill-bench/scripts/lib (see grid.py note for the installed-plugin form)
sys.path.insert(0, str(HERE.parents[1] / "skill-bench" / "scripts" / "lib"))
import bench_io  # noqa: E402
from artifact_check import classify_cells  # noqa: E402
from blind import capture_symmetry, write_blinded  # noqa: E402


def merged_response(r):
    """Response text + every cell-created artifact. ADAPT if scenario bundles ship their own
    .md corpus: exclude those paths so pre-existing files are never swept in (#185 lesson)."""
    text = r["response"] or ""
    for rel, body in (r.get("artifacts") or {}).items():
        text += f"\n\n--- recorded decision file {rel} ---\n{body}"
    return text


def main():
    records = [json.loads(p.read_text(encoding="utf-8"))
               for p in sorted((HERE / "outputs").glob("*.json"))]
    graded = HERE / "graded"
    graded.mkdir(exist_ok=True)

    ok, errors = classify_cells(records, merged_response)   # #191 item 1
    if errors:
        (graded / "error_cells.json").write_text(json.dumps(
            [{"cell": r["cell"], "reason": why} for r, why in errors], indent=1),
            encoding="utf-8")
        print(f"{len(errors)} ERROR cell(s) excluded (infrastructure, resumable) "
              f"-> graded/error_cells.json", file=sys.stderr)

    sweep = capture_symmetry(ok, merged_response)           # #191 item 2
    print("capture symmetry:", json.dumps(sweep))
    if sweep["skewed"]:
        sys.exit("arm-skewed capture — fix the harness before grading, this is not signal")

    arm_map = write_blinded(ok, graded, lambda r: r["cell"],
                            lambda r: {"scenario": r["scenario"],
                                       "response": merged_response(r)})
    for m, r in zip(arm_map, ok):
        m["scenario"], m["rep"] = r["scenario"], r["rep"]
    bench_io.dump_records(arm_map, str(graded / "arm_map.tsv"), fmt="tsv")

    # ADAPT: keys.json — the per-scenario grading key (expectations / traps / outcome keys)
    # in the shape your grade workflow's rubric reads (ADR 0025/0026 layout).
    keys = {}
    (graded / "keys.json").write_text(json.dumps(keys, indent=1), encoding="utf-8")

    # Guess-the-arm audit sample: rep-1 cells, up to 3 per arm, deterministic.
    by_arm = {}
    for m, r in zip(arm_map, ok):
        if r["rep"] == 1:
            by_arm.setdefault(r["arm"], []).append(m["bid"])
    audit = sorted(sum((sorted(v)[:3] for v in by_arm.values()), []))
    (graded / "audit_bids.json").write_text(json.dumps(audit), encoding="utf-8")
    print(f"blinded {len(ok)} cells -> {graded}; audit sample {len(audit)}")


if __name__ == "__main__":
    main()
