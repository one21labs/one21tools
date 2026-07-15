#!/usr/bin/env python3
"""Build scenario B1's reconstruction bundle (scenarios.json: backtests[0]; stdlib only).

Snapshot = this repo cloned at parent commit f6b9b38 (pre-decision state for issue #41's
tiered-execution call), future refs/reflog stripped so `git log` ends at the reconstruction
point, .claude filtered from ALL history (machinery never existed — see the hermeticity
comment below), docs/decisions kept (pre-decision at the parent), and the outcome-free issue
text (scenario-b1/ISSUE-41.md, committed input record) placed untracked at the snapshot root.

Output: scenario-b1/snapshot/ (gitignored — regenerable; this script is the home).
"""
import os
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
B1 = HERE / "scenario-b1"
SNAP = B1 / "snapshot"
COMMIT = "f6b9b38"


def sh(*args, cwd):
    return subprocess.run(args, cwd=str(cwd), check=True, capture_output=True, text=True)


def main():
    if SNAP.exists():
        shutil.rmtree(SNAP)
    sh("git", "clone", "-q", "--no-hardlinks", f"file://{REPO}", str(SNAP), cwd=HERE)
    sh("git", "checkout", "-q", COMMIT, cwd=SNAP)
    sh("git", "branch", "-f", "main", COMMIT, cwd=SNAP)
    sh("git", "checkout", "-q", "main", cwd=SNAP)
    sh("git", "remote", "remove", "origin", cwd=SNAP)
    # strip every other ref + reflog so history ends at the reconstruction point
    refs = sh("git", "for-each-ref", "--format=%(refname)", cwd=SNAP).stdout.split()
    for ref in refs:
        if ref != "refs/heads/main":
            sh("git", "update-ref", "-d", ref, cwd=SNAP)
    sh("git", "reflog", "expire", "--expire=now", "--all", cwd=SNAP)
    sh("git", "gc", "-q", "--prune=now", "--aggressive", cwd=SNAP)

    tiered = list(SNAP.glob("benchmarks/2026-07-10-tiered-execution*"))
    assert not tiered, f"outcome dirs present at {COMMIT}?! {tiered}"

    # Hermeticity, third design (2026-07-12, after fresh-eyes audits 1-2; zero counted cells
    # at each change): the machinery must never have EXISTED in the snapshot — a removal
    # commit exposes the treatment via `git show HEAD` and its fake message made cells smell
    # tampering (two refused to decide). Export the panel agents for arm-C-only injection
    # (grid_i2.py), then FILTER .claude/ and the one future-leak metadata file out of the
    # entire history. docs/decisions STAYS: at the parent commit it is pre-decision by
    # construction (outcome-free — audit-verified), and its absence while CLAUDE.md
    # references it was the loudest tamper tell. The memo lands UNTRACKED (a handed memo,
    # not a suspicious commit). Arms A/B: knowledge-symmetric, machinery-less.
    agents_src = SNAP / ".claude" / "agents"
    panel = B1 / "panel-agents"
    if panel.exists():
        shutil.rmtree(panel)
    if agents_src.exists():
        shutil.copytree(agents_src, panel)
    fb_env = {**os.environ, "FILTER_BRANCH_SQUELCH_WARNING": "1"}
    subprocess.run(["git", "filter-branch", "-f", "--index-filter",
                    "git rm -rq --cached --ignore-unmatch .claude "
                    "benchmarks/2026-07-09-claude-md-sections/metadata.json",
                    "--", "--all"],
                   cwd=str(SNAP), check=True, capture_output=True, text=True, env=fb_env)
    subprocess.run(["git", "update-ref", "-d", "refs/original/refs/heads/main"],
                   cwd=str(SNAP), capture_output=True)
    subprocess.run(["git", "clean", "-qfdx"], cwd=str(SNAP), check=True, capture_output=True)
    sh("git", "reset", "-q", "--hard", "HEAD", cwd=SNAP)
    sh("git", "reflog", "expire", "--expire=now", "--all", cwd=SNAP)
    sh("git", "gc", "-q", "--prune=now", "--aggressive", cwd=SNAP)

    shutil.copy(B1 / "ISSUE-41.md", SNAP / "ISSUE-41.md")  # untracked by design

    # assertions: .claude never existed in history; decisions present; memo untracked
    hist = subprocess.run(["git", "log", "--all", "--oneline", "--", ".claude"],
                          cwd=str(SNAP), capture_output=True, text=True).stdout.strip()
    assert not hist, f".claude still in history: {hist[:200]}"
    assert (SNAP / "docs" / "decisions").exists(), "docs/decisions missing (must stay)"
    status = sh("git", "status", "--porcelain", cwd=SNAP).stdout.strip()
    assert status == "?? ISSUE-41.md", f"unexpected status: {status[:200]}"
    head = sh("git", "rev-parse", "--short", "HEAD", cwd=SNAP).stdout.strip()
    n = sh("git", "rev-list", "--count", "HEAD", cwd=SNAP).stdout.strip()
    print(f"B1 snapshot at {head} ({n} commits), .claude filtered from history, "
          f"decisions kept, ISSUE-41.md untracked")


if __name__ == "__main__":
    main()
