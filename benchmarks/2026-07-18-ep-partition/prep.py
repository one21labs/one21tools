#!/usr/bin/env python3
"""Prep the 4-arm ep-partition inputs (issue #244).

Arms: without / with-full / with-operational / with-conceptual, engineering-principles only.
Treatment construction is IDENTICAL across arms (07-09's treatment() pattern): stripped SKILL.md
body, then the 3 touched reference files, each block prefixed "=== references/<name> ===". with-full
reads the working-tree source files verbatim; with-operational / with-conceptual read
partition/{operational,conceptual}/*.md (partition.py's output -- run that first) instead of the
source files, same join. A file whose variant is empty is omitted from the join entirely (spec
line 56) -- none of the 4 files happens to have an empty variant on the current skill content, but
the omission path is implemented and exercised by the empty-body branch below regardless.

Writes treatments/*.txt, prompts/<key>.txt, cells.tsv, meta.json (same shapes as
2026-07-09-ep-remeasure-hermetic), and treatments/costs.json (body_chars/full_chars per arm).
"""
import json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(BASE, "..", ".."))
SKILL = "engineering-principles"
REFS = ["ssot-enforcement.md", "design-review.md", "root-cause-analysis.md"]
PART = os.path.join(BASE, "partition")

os.makedirs(os.path.join(BASE, "treatments"), exist_ok=True)
os.makedirs(os.path.join(BASE, "prompts"), exist_ok=True)


def strip_frontmatter(text):
    return re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S).strip()


def source_file(rel):
    with open(os.path.join(REPO, "skills", SKILL, rel), encoding="utf-8") as fh:
        return fh.read()


def variant_file(variant_dir, name):
    path = os.path.join(variant_dir, name)
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def full_treatment(body, ref_reader):
    """body: SKILL.md content for this arm (already stripped/variant-selected).
    ref_reader(ref_name) -> that ref's content for this arm.
    Same construction as 07-09: body first (unheadered), then each non-empty ref headered,
    joined with blank lines. A ref whose content is empty for this arm is omitted (spec line 56)."""
    parts = [body] if body.strip() else []
    for r in REFS:
        content = ref_reader(r).strip()
        if not content:
            continue
        parts.append(f"=== references/{r} ===\n\n" + content)
    return "\n\n".join(parts)


# with-full: working-tree source files, verbatim (07-09 construction).
full_body = strip_frontmatter(source_file("SKILL.md"))
full_text = full_treatment(full_body, lambda r: source_file(f"references/{r}"))

# with-operational / with-conceptual: partition.py's output, same construction.
if not os.path.isdir(os.path.join(PART, "operational")):
    raise SystemExit("prep.py: partition/operational/ missing -- run partition.py first")

op_body = variant_file(os.path.join(PART, "operational"), "SKILL.md")
op_text = full_treatment(op_body, lambda r: variant_file(os.path.join(PART, "operational"), r))

co_body = variant_file(os.path.join(PART, "conceptual"), "SKILL.md")
co_text = full_treatment(co_body, lambda r: variant_file(os.path.join(PART, "conceptual"), r))

ARM_TEXT = {"with-full": full_text, "with-operational": op_text, "with-conceptual": co_text}
ARM_BODY = {"with-full": full_body, "with-operational": op_body, "with-conceptual": co_body}
for arm, text in ARM_TEXT.items():
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

with open(os.path.join(BASE, "meta.json"), "w", encoding="utf-8", newline="") as fh:
    json.dump(meta, fh, indent=1)
with open(os.path.join(BASE, "cells.tsv"), "w", encoding="utf-8", newline="") as fh:
    for key in cells:
        fh.write(f"{key}\t{SKILL}\n")

costs = {"refs": REFS,
         "body_chars": {arm: len(ARM_BODY[arm]) for arm in ARM_TEXT},
         "full_chars": {arm: len(ARM_TEXT[arm]) for arm in ARM_TEXT}}
with open(os.path.join(BASE, "treatments", "costs.json"), "w", encoding="utf-8", newline="") as fh:
    json.dump(costs, fh, indent=1)

print(f"prepped {len(meta)} evals; treatments (chars): " +
      ", ".join(f"{arm} body={costs['body_chars'][arm]} full={costs['full_chars'][arm]}"
                for arm in ("with-full", "with-operational", "with-conceptual")))
