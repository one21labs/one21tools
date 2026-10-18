#!/usr/bin/env python3
"""Freeze the instrument for the control-narratives revision 1 re-measure (ADR 0095 decisions 2-4).

Writes, for each measured skill:
  treatments/<skill>.txt   live SKILL.md body, frontmatter stripped — the content anchor a later
                           claim byte-compares against (ADR 0095 decision 2)
  evals/<skill>.json       the eval battery as measured (frozen copy of skills/<skill>/evals)
and treatments/costs.json (body codepoints + the source SHA). Re-running on a changed tree
refuses to overwrite: a frozen dir that silently re-derives is no longer frozen.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SKILLS = ("control-narratives",)


def strip_front(text):
    return text.split("---", 2)[2].strip() if text.startswith("---") else text.strip()


def main():
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                         check=True, cwd=REPO).stdout.strip()
    (HERE / "treatments").mkdir(exist_ok=True)
    (HERE / "evals").mkdir(exist_ok=True)
    costs = {"source_sha": sha, "body_chars": {}}
    for s in SKILLS:
        body = strip_front((REPO / "skills" / s / "SKILL.md").read_text(encoding="utf-8"))
        evals = (REPO / "skills" / s / "evals" / "evals.json").read_text(encoding="utf-8")
        for path, content in ((HERE / "treatments" / f"{s}.txt", body),
                              (HERE / "evals" / f"{s}.json", evals)):
            if path.exists() and path.read_text(encoding="utf-8") != content:
                sys.exit(f"{path.relative_to(REPO)} exists and differs from the live tree — "
                         "frozen instrument; start a new benchmark dir instead")
            path.write_text(content, encoding="utf-8")
        costs["body_chars"][s] = len(body)
    out = HERE / "treatments" / "costs.json"
    if not out.exists():  # the SHA records the FIRST freeze; a re-run after commit keeps it
        out.write_text(json.dumps(costs, indent=1) + "\n", encoding="utf-8")
    print(out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
