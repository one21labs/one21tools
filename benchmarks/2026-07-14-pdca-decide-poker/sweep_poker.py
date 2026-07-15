#!/usr/bin/env python3
"""Contamination sweep + substrate fingerprints for the poker grid (run BEFORE blinding).

Mechanical, per lib/contamination.py:
- sweep_tree over the 7 rebuilt scenario bundles (bench-tells + git history).
- sweep_records over outputs/*.json — response + artifacts + the arm-P poker payload
  (advisor/round-2 text rides in via the record's probes slot, which _record_text scans).
- Outcome tells: post-outcome repo facts that postdate every backtest parent commit
  (ADR ids 0052+, issue ids 172+) may not appear in any backtest cell; harness names and
  THIS worktree's path may not appear in any cell (escape tells).
- Fingerprints: git HEAD per bundle, recorded so a rebuild's determinism is checkable.

Writes sweep-report.json; exits 1 on any hit (quarantine per pre-registration).
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "skill-bench" / "scripts" / "lib"))
from contamination import GLOBAL_TELLS, sweep_records, sweep_tree  # noqa: E402

I2 = HERE.parent / "2026-07-12-pdca-decide-outcome"
BUNDLES = {"B1/B2": "scenario-b1/snapshot", "B3": "scenario-b3/snapshot",
           "B4": "scenario-b4/snapshot", "S1": "scenario-s1/workdir",
           "S2": "scenario-s2/workdir", "S3": "scenario-s3/workdir",
           "S4": "scenario-s4/workdir"}
# Backtest snapshots ARE historical copies of this benchmarking repo, so generic bench
# language is legitimate pre-decision context there; their tells must be experiment-specific
# terms that postdate every parent commit. Synthetic workdirs should contain NO bench language.
BACKTEST_TREE_TELLS = [r"planning.?poker", r"[Dd]elphi", r"#185\b", r"reveal spread",
                       r"poker"]
SYNTH_TREE_TELLS = [r"planted", r"pre-regist", r"guess-the-arm", r"benchmark arm",
                    r"seed manifest"] + BACKTEST_TREE_TELLS
POST_OUTCOME = [r"ADR 00(5[2-9]|6\d)", r"#17[2-9]\b", r"#18\d\b"]
RECORD_TELLS = {s: list(POST_OUTCOME) for s in ("B1", "B2", "B3", "B4")}
ESCAPE_TELLS = GLOBAL_TELLS + [r"one21tools-172close"]


def head_of(path):
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(path),
                       capture_output=True, text=True)
    return r.stdout.strip()[:12] if r.returncode == 0 else None


def main():
    report = {"bundle_heads": {}, "tree_hits": {}, "record_hits": [], "cells_swept": 0}
    for name, rel in BUNDLES.items():
        path = I2 / rel
        if not path.exists():
            sys.exit(f"bundle missing: {rel} — rebuild via build_b1.py / build_scenarios.py")
        report["bundle_heads"][name] = head_of(path)
        tells = BACKTEST_TREE_TELLS if name.startswith("B") else SYNTH_TREE_TELLS
        hits = sweep_tree(path, tells)
        if hits:
            report["tree_hits"][name] = hits[:20]

    records = []
    for p in sorted((HERE / "outputs").glob("*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        # the arm-P poker payload (advisor/round-2 text) rides in the probes slot the
        # lib's _record_text already scans; A/C cells have no poker record
        records.append({"cell": r["cell"], "scenario": r["scenario"],
                        "response": r["response"], "artifacts": r.get("artifacts"),
                        "probes": r.get("poker")})
    report["cells_swept"] = len(records)
    report["record_hits"] = [list(h) for h in
                             sweep_records(records, RECORD_TELLS, ESCAPE_TELLS)]

    (HERE / "sweep-report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    clean = not report["tree_hits"] and not report["record_hits"]
    print(json.dumps({"bundle_heads": report["bundle_heads"],
                      "tree_hits": {k: len(v) for k, v in report["tree_hits"].items()},
                      "record_hits": len(report["record_hits"]),
                      "cells_swept": report["cells_swept"], "clean": clean}, indent=1))
    sys.exit(0 if clean else 1)


if __name__ == "__main__":
    main()
