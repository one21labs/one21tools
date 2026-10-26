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
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
# As grid.py (ADR 0102): $SKILL_MEASURE_ROOT, else a sibling skill-measure checkout.
HARNESS = Path(os.environ.get("SKILL_MEASURE_ROOT") or HERE.parents[2] / "skill-measure")
SKILLS = ("control-narratives",)


def strip_front(text):
    return text.split("---", 2)[2].strip() if text.startswith("---") else text.strip()


def git(*args, cwd):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True,
                          cwd=cwd).stdout.strip()


def harness_commit():
    """The skill-measure commit in use; grid.py and grade.py compare it to the frozen one."""
    if not (HARNESS / "scripts" / "lib").is_dir() or not (HARNESS / ".git").exists():
        sys.exit(f"harness checkout not found at {HARNESS}: git clone https://github.com/"
                 "one21labs/skill-measure && export SKILL_MEASURE_ROOT=$PWD/skill-measure")
    # ADR 0102: new dirs record the harness commit. "-dirty" (as `git describe --dirty`) marks a
    # checkout with uncommitted changes, whose code the bare sha cannot reproduce.
    return git("rev-parse", "HEAD", cwd=HARNESS) + (
        "-dirty" if git("status", "--porcelain", cwd=HARNESS) else "")


def main():
    harness = harness_commit()
    (HERE / "treatments").mkdir(exist_ok=True)
    (HERE / "evals").mkdir(exist_ok=True)
    costs = {"source_sha": git("rev-parse", "HEAD", cwd=REPO), "harness_sha": harness}
    for s in SKILLS:
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
