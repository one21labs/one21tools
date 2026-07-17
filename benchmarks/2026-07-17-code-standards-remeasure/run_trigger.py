#!/usr/bin/env python3
"""L1 trigger-ablation harness for #214 (matched protocol; one variant per invocation).

Derives the query set from the committed trigger-kit (ADR 0041: derive, don't duplicate) and
invokes skill-bench's vendored runner with the mandated protocol: --num-workers 1 (concurrent
workers collapse rates toward 1/N), sonnet pinned, 3 runs/query, timeout 240 (a timeout is a
null measurement, never a False). Output: trigger-results/<variant>.json (append-only).
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RUNNER = REPO / "skill-bench" / "scripts" / "run_eval.py"
KIT = REPO / "benchmarks" / "2026-07-07-toolkit-grid" / "trigger-kit" / "code-standards-queries.json"
MODEL, RUNS, TIMEOUT = "sonnet", 3, 240


def eval_set():
    kit = json.loads(KIT.read_text(encoding="utf-8"))
    return ([{"query": q, "should_trigger": True} for q in kit["should_fire"]] +
            [{"query": q, "should_trigger": False} for q in kit["should_not_fire"]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True, help="key in descriptions.json")
    a = ap.parse_args()
    desc = json.loads((HERE / "descriptions.json").read_text(encoding="utf-8"))[a.variant].strip()
    out = HERE / "trigger-results"
    out.mkdir(exist_ok=True)
    outfile = out / f"{a.variant}.json"
    if outfile.exists():
        sys.exit(f"{outfile} exists — append-only record; remove deliberately to re-run")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(eval_set(), f)
        ep = f.name
    try:
        r = subprocess.run(
            [sys.executable, str(RUNNER), "--eval-set", ep,
             "--skill-path", str(REPO / "skills" / "code-standards"), "--description", desc,
             "--num-workers", "1", "--runs-per-query", str(RUNS), "--timeout", str(TIMEOUT),
             "--model", MODEL, "--verbose"],
            capture_output=True, text=True)
    finally:
        os.unlink(ep)
    sys.stderr.write((r.stderr or "")[-4000:])
    if r.returncode != 0:
        sys.exit(f"runner exit {r.returncode}")
    outfile.write_text(r.stdout, encoding="utf-8")
    print(a.variant, json.loads(r.stdout)["summary"])


if __name__ == "__main__":
    main()
