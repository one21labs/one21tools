#!/usr/bin/env python3
"""Unattended end-to-end run of the pre-registered pipeline (metadata.json), resumable.

prescreen -> grade prescreen -> select -> pilot -> derive per-cell estimates -> cost-gated grid
-> grade grid -> aggregate. Every stage is idempotent (finished cells and grades are skipped), so
re-running after a crash or a container restart picks up where it stopped. Paid calls go through
usage_guard (ADR 0099): at 80% of a usage window the run waits for the reset on its own. Each
stage ends with a commit + push so the record survives the container.
"""
import glob
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BRANCH = "claude/backlog-310-317-322"
PASSES = 3  # re-run a stage while it still has ERROR cells, at most this many times
TRAILER = ("\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
           "Claude-Session: https://claude.ai/code/session_01CLLGaHs8zG2FcYFmAECwQC")


def sh(*cmd, check=True):
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=HERE, check=check)


def commit(msg):
    subprocess.run(["git", "add", "-A", str(HERE)], cwd=REPO, check=True)
    subprocess.run(["git", "add", "docs/pdca"], cwd=REPO, check=False)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=REPO).returncode == 0:
        return
    subprocess.run(["git", "commit", "-q", "-m", msg + TRAILER], cwd=REPO, check=True)
    for _ in range(4):
        if subprocess.run(["git", "push", "-q", "origin", BRANCH], cwd=REPO).returncode == 0:
            return


def cells(d):
    return [json.loads(Path(p).read_text()) for p in glob.glob(str(HERE / d / "*.json"))]


def errors(d):
    return sum(1 for c in cells(d) if c["summary"]["error"])


def run_until_clean(flag, d, label):
    for i in range(PASSES):
        sh("python3", "-u", "grid.py", *([flag] if flag else []), "--workers", "4", check=False)
        commit(f"{label}: cells after pass {i + 1}")
        if (HERE / d).exists() and errors(d) == 0:
            return
    print(f"{label}: {errors(d)} ERROR cells remain after {PASSES} passes — they are excluded "
          "from grading (#191), never scored 0", flush=True)


def judge_cost(tag):
    p = HERE / "graded" / f"judge-cost-claude-opus-5-5-{tag}.json"
    return json.loads(p.read_text()) if p.exists() else {"billed_usd": 0.0, "calls": 0}


def main():
    meta_p = HERE / "metadata.json"
    meta = json.loads(meta_p.read_text())
    for lock in HERE.glob("*/.grid.lock"):  # this orchestrator is the only runner; a lock is stale
        lock.unlink()

    run_until_clean("--prescreen", "prescreen-outputs", "Prescreen")
    sh("python3", "-u", "grade.py", "--dirs", "prescreen-outputs")
    sh("python3", "aggregate.py", "--select")
    sel = json.loads((HERE / "selection.json").read_text())
    meta["prescreen"]["result"] = {"g_per_skill": sel["g_per_skill"], "dropped": sel["dropped"],
                                   "floors": sel["floors"], "see": "selection.json"}
    meta_p.write_text(json.dumps(meta, indent=1) + "\n")
    commit("Prescreen graded; per-model surviving evals recorded (selection.json)")

    run_until_clean("--pilot", "pilot-outputs", "Pilot")
    gen = {"opus": [], "sonnet": []}
    for d in ("prescreen-outputs", "pilot-outputs"):
        for c in cells(d):
            if not c["summary"]["error"]:
                gen["opus" if "opus" in c["model"] else "sonnet"].append(c["summary"]["cell_cost_usd"])
    jc = judge_cost("prescreen-outputs")
    judge_per = jc["billed_usd"] / jc["calls"] if jc["calls"] else 0.0
    per = {m: round(sum(v) / len(v) + judge_per, 4) for m, v in gen.items()}
    spent = sum(c["summary"]["cell_cost_usd"] or 0 for d in ("prescreen-outputs", "pilot-outputs")
                for c in cells(d)) + jc["billed_usd"]
    meta["pilot"]["result"] = {"generation_mean_usd": {m: round(sum(v) / len(v), 4) for m, v in gen.items()},
                               "judge_per_cell_usd": round(judge_per, 4)}
    meta["cost"]["per_cell_estimate_usd"] = per
    meta["cost"]["spent_before_grid_usd"] = round(spent, 2)
    meta_p.write_text(json.dumps(meta, indent=1) + "\n")
    commit(f"Pilot done; per-cell estimate (generation + judge) {per}, spent ${spent:.2f}")

    run_until_clean(None, "outputs", "Grid")
    if not (HERE / "outputs").exists():
        sys.exit("grid refused by the cost gate (see log) — stopping for the owner, nothing graded")
    sh("python3", "-u", "grade.py", "--dirs", "outputs")
    sh("python3", "aggregate.py")
    commit("Grid graded and aggregated (results-<judge>.json)")


if __name__ == "__main__":
    sys.exit(main())
