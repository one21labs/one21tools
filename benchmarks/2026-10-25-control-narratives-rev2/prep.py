#!/usr/bin/env python3
"""Freeze the instrument for the control-narratives revision 2 re-measure (#328).

Writes, for the measured skill:
  treatments/<skill>.txt   live SKILL.md body, frontmatter stripped — the content anchor a later
                           claim byte-compares against (ADR 0095 decision 2)
  evals/<skill>.json       the eval battery as measured (frozen copy of skills/<skill>/evals,
                           blind-authored and struck by the owner as domain reader)
and treatments/costs.json (the source and harness SHAs). Re-running on a
changed tree refuses to overwrite: a frozen dir that silently re-derives is no longer frozen.
"""
import json
import subprocess
import sys
from pathlib import Path

from _harness import HARNESS

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SKILLS = ("control-narratives",)


def strip_front(text):
    return text.split("---", 2)[2].strip() if text.startswith("---") else text.strip()


def git(*args, cwd):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True,
                          cwd=cwd).stdout.strip()


def harness_commit():
    """The skill-measure commit in use; grid.py and grade.py compare it to the frozen one."""
    if not (HARNESS / ".git").exists():
        sys.exit(f"{HARNESS} is not a git checkout, so no commit can be recorded (ADR 0102)")
    # A checkout with uncommitted changes runs code its sha cannot reproduce: refused, not recorded.
    if git("status", "--porcelain", cwd=HARNESS):
        sys.exit(f"{HARNESS} has uncommitted changes: commit or stash them, so the recorded "
                 "harness commit is the code that runs")
    return git("rev-parse", "HEAD", cwd=HARNESS)


def main():
    harness = harness_commit()
    (HERE / "treatments").mkdir(exist_ok=True)
    (HERE / "evals").mkdir(exist_ok=True)
    costs = {"source_sha": git("rev-parse", "HEAD", cwd=REPO), "harness_sha": harness}
    for s in SKILLS:
        if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", f"skills/{s}"], cwd=REPO).returncode:
            sys.exit(f"skills/{s} has uncommitted changes: commit them first, so source_sha is "
                     "the commit the frozen copy came from")
        body = strip_front((REPO / "skills" / s / "SKILL.md").read_text(encoding="utf-8"))
        evals = (REPO / "skills" / s / "evals" / "evals.json").read_text(encoding="utf-8")
        for path, content in ((HERE / "treatments" / f"{s}.txt", body),
                              (HERE / "evals" / f"{s}.json", evals)):
            if path.exists() and path.read_text(encoding="utf-8") != content:
                sys.exit(f"{path.relative_to(REPO)} exists and differs from the live tree — "
                         "frozen instrument; start a new benchmark dir instead")
            path.write_text(content, encoding="utf-8")
    out = HERE / "treatments" / "costs.json"
    if not out.exists():  # the SHA records the FIRST freeze; a re-run after commit keeps it
        out.write_text(json.dumps(costs, indent=1) + "\n", encoding="utf-8")
    print(out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
