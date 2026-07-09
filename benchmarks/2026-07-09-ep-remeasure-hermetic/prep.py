#!/usr/bin/env python3
"""Prep the ADR 0027 EP re-measure inputs (issue #52).

Three arms, engineering-principles only. Treatment = SKILL.md BODY (frontmatter stripped) + the
3 touched reference files, filename-headered (ADR 0027 decisions 1-2):
  treatments/with-old.txt  <- the checkout's files (main lineage)
  treatments/with-new.txt  <- `git show <EP_NEW_REF>:...` (default 675033c, engineering-principles-improve)
Also writes prompts/<key>.txt, cells.tsv, meta.json (same shapes as 2026-07-08-skills-hermetic),
and treatments/costs.json (both ADR 0019 cost bounds, measured not asserted).
"""
import json, os, re, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(BASE, "..", ".."))
SKILL = "engineering-principles"
NEW_REF = os.environ.get("EP_NEW_REF", "675033c")
REFS = ["ssot-enforcement.md", "design-review.md", "root-cause-analysis.md"]

os.makedirs(os.path.join(BASE, "treatments"), exist_ok=True)
os.makedirs(os.path.join(BASE, "prompts"), exist_ok=True)


def strip_frontmatter(text):
    return re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S).strip()


def old_file(rel):
    with open(os.path.join(REPO, "skills", SKILL, rel), encoding="utf-8") as fh:
        return fh.read()


def new_file(rel):
    return subprocess.run(
        ["git", "-C", REPO, "show", f"{NEW_REF}:skills/{SKILL}/{rel}"],
        capture_output=True, text=True, encoding="utf-8", check=True).stdout


def treatment(read):
    body = strip_frontmatter(read("SKILL.md"))
    parts = [body]
    for r in REFS:
        parts.append(f"=== references/{r} ===\n\n" + read(f"references/{r}").strip())
    return body, "\n\n".join(parts)


old_body, old_full = treatment(old_file)
new_body, new_full = treatment(new_file)
for arm, text in (("with-old", old_full), ("with-new", new_full)):
    with open(os.path.join(BASE, "treatments", arm + ".txt"), "w", encoding="utf-8", newline="") as fh:
        fh.write(text)

with open(os.path.join(REPO, "skills", SKILL, "evals", "evals.json"), encoding="utf-8") as fh:
    ev = json.load(fh)
meta, cells = {}, []
for e in ev["evals"]:
    key = f"{SKILL}.{e['id']}"
    with open(os.path.join(BASE, "prompts", key + ".txt"), "w", encoding="utf-8", newline="") as fh:
        fh.write(e["prompt"])
    meta[key] = {"skill": SKILL, "eval_id": str(e["id"]), "prompt": e["prompt"],
                 "expectations": e["expectations"]}
    cells.append(key)

with open(os.path.join(BASE, "meta.json"), "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=1)
with open(os.path.join(BASE, "cells.tsv"), "w", encoding="utf-8", newline="") as fh:
    for key in cells:
        fh.write(f"{key}\t{SKILL}\n")

costs = {"new_ref": NEW_REF, "refs": REFS,
         "body_chars": {"with-old": len(old_body), "with-new": len(new_body)},
         "full_chars": {"with-old": len(old_full), "with-new": len(new_full)}}
with open(os.path.join(BASE, "treatments", "costs.json"), "w", encoding="utf-8") as fh:
    json.dump(costs, fh, indent=1)

print(f"prepped {len(meta)} evals; treatments (chars): "
      f"body {len(old_body)}->{len(new_body)} ({len(new_body)-len(old_body):+d}), "
      f"full {len(old_full)}->{len(new_full)} ({len(new_full)-len(old_full):+d})")
