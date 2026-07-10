#!/usr/bin/env python3
"""Driver for the description-ablation trigger benchmark.

Wraps the upstream skill-creator run_eval.py (patched per
benchmarks/2026-07-07-toolkit-grid/trigger-kit/runner-patches.diff):
converts a trigger-kit query file to the runner's eval-set schema,
invokes the runner with a description variant from descriptions.json,
and appends one record per query x rep to results.jsonl.

Environment (paths differ per machine, so they are parameters):
  RUNNER        path to the patched run_eval.py
  RUNNER_PKG    dir containing the runner's scripts/ package (PYTHONPATH)
  PROJECT_ROOT  clean dir with .claude/ where nested `claude -p` runs

Usage:
  run_ablation.py --skill code-standards --variant control [--reps N]
                  [--query-index 0,3] [--rep-base 0] [--workers 4]
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
KIT = REPO / "benchmarks/2026-07-07-toolkit-grid/trigger-kit"


def convert_kit_queries(skill: str) -> list[dict]:
    """Trigger-kit schema (should_fire/should_not_fire lists) ->
    runner schema (flat list of {"query", "should_trigger"})."""
    kit = json.loads((KIT / f"{skill}-queries.json").read_text())
    return [{"query": q, "should_trigger": True} for q in kit["should_fire"]] + [
        {"query": q, "should_trigger": False} for q in kit["should_not_fire"]
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--variant", required=True, help="key in descriptions.json")
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--rep-base", type=int, default=0, help="rep numbering offset for escalations")
    ap.add_argument("--query-index", default=None, help="comma-sep indices into the converted set")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--model", default="sonnet")
    args = ap.parse_args()

    runner = Path(os.environ["RUNNER"])
    runner_pkg = os.environ["RUNNER_PKG"]
    project_root = os.environ["PROJECT_ROOT"]

    descriptions = json.loads((HERE / "descriptions.json").read_text())
    description = descriptions[args.skill][args.variant].strip()

    eval_set = convert_kit_queries(args.skill)
    if args.query_index:
        idx = [int(i) for i in args.query_index.split(",")]
        eval_set = [eval_set[i] for i in idx]

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(eval_set, f)
        eval_path = f.name

    env = dict(os.environ, PYTHONPATH=runner_pkg)
    proc = subprocess.run(
        [sys.executable, str(runner),
         "--eval-set", eval_path,
         "--skill-path", str(REPO / "skills" / args.skill),
         "--description", description,
         "--num-workers", str(args.workers),
         "--runs-per-query", str(args.reps),
         "--timeout", str(args.timeout),
         "--model", args.model,
         "--verbose"],
        cwd=project_root, env=env, capture_output=True, text=True,
    )
    os.unlink(eval_path)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        sys.exit(proc.returncode)

    output = json.loads(proc.stdout)
    with open(HERE / "results.jsonl", "a") as out:
        for r in output["results"]:
            # runner aggregates reps; emit one record per rep (reps are exchangeable)
            fired_reps = [True] * r["triggers"] + [False] * (r["runs"] - r["triggers"])
            for i, fired in enumerate(fired_reps):
                out.write(json.dumps({
                    "skill": args.skill,
                    "variant": args.variant,
                    "query": r["query"],
                    "should_trigger": r["should_trigger"],
                    "fired": fired,
                    "rep": args.rep_base + i,
                }) + "\n")

    fire_ok = sum(r["triggers"] for r in output["results"] if r["should_trigger"])
    fire_n = sum(r["runs"] for r in output["results"] if r["should_trigger"])
    fp = sum(r["triggers"] for r in output["results"] if not r["should_trigger"])
    fp_n = sum(r["runs"] for r in output["results"] if not r["should_trigger"])
    print(f"{args.skill}/{args.variant}: TP {fire_ok}/{fire_n}, FP {fp}/{fp_n}")


if __name__ == "__main__":
    main()
