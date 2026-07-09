#!/usr/bin/env python3
"""Prep the hermetic skill benefit-benchmark inputs from the live eval sets.

For each skill: writes treatments/<skill>.txt (SKILL.md BODY, frontmatter stripped — the "with"
treatment), prompts/<skill>.<id>.txt (the eval prompt verbatim, newlines/code blocks preserved),
cells.tsv (key<TAB>skill, one row per eval), and meta.json (key -> {skill, eval_id, prompt,
expectations}) — the SSoT the harness and the blind grader both read.
"""
import json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.abspath(os.path.join(BASE, "..", "..", "skills"))
SKILLS = ["code-standards", "engineering-principles", "building-skills", "optimizing-context"]
os.makedirs(os.path.join(BASE, "treatments"), exist_ok=True)
os.makedirs(os.path.join(BASE, "prompts"), exist_ok=True)

meta = {}
cells = []
for s in SKILLS:
    sk = open(os.path.join(SKILLS_DIR, s, "SKILL.md"), encoding="utf-8").read()
    body = re.sub(r"^---\n.*?\n---\n", "", sk, count=1, flags=re.S).strip()  # strip YAML frontmatter
    open(os.path.join(BASE, "treatments", s + ".txt"), "w", encoding="utf-8", newline="").write(body)
    ev = json.load(open(os.path.join(SKILLS_DIR, s, "evals", "evals.json"), encoding="utf-8"))
    for e in ev["evals"]:
        key = f"{s}.{e['id']}"
        open(os.path.join(BASE, "prompts", key + ".txt"), "w", encoding="utf-8", newline="").write(e["prompt"])
        meta[key] = {"skill": s, "eval_id": str(e["id"]), "prompt": e["prompt"],
                     "expectations": e["expectations"]}
        cells.append((key, s))

json.dump(meta, open(os.path.join(BASE, "meta.json"), "w", encoding="utf-8"), indent=1)
with open(os.path.join(BASE, "cells.tsv"), "w", encoding="utf-8", newline="") as fh:
    for key, s in cells:
        fh.write(f"{key}\t{s}\n")

print(f"prepped {len(meta)} evals across {len(SKILLS)} skills")
for s in SKILLS:
    n = sum(1 for k in meta if meta[k]["skill"] == s)
    tc = len(open(os.path.join(BASE, "treatments", s + ".txt"), encoding="utf-8").read())
    print(f"  {s}: {n} evals, treatment {tc} chars")
