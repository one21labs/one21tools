#!/usr/bin/env python3
"""Prep the tiered-agent-execution benchmark inputs from the live eval sets (issue #41).

Reuses skills/*/evals/evals.json verbatim -- the same 24-eval battery (4 skills x 6 evals) as
benchmarks/2026-07-08-skills-hermetic/prep.py. Unlike that benchmark, NO treatment content is
generated or injected here: arms differ by EXECUTOR CONFIGURATION only (model tier / orchestration
pattern, see harness.workflow.js), never by prompt text. All arms get the same neutral framing.

Writes:
  meta.json        key -> {skill, eval_id, prompt, expectations} -- the grading SSoT (blind.py
                    reads this for expectations; ADR 0019 blind grading).
  cells.tsv         key<TAB>skill, one row per eval (24 rows).
  evals_args.json   [{skill, eval_id, prompt}, ...] -- PROMPT ONLY, expectations stripped. This is
                    the exact value to pass as harness.workflow.js's `args.evals` so the executor
                    arms never see the grading criteria (no teaching to the test).
"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.abspath(os.path.join(BASE, "..", "..", "skills"))
SKILLS = ["code-standards", "engineering-principles", "building-skills", "optimizing-context"]

meta = {}
cells = []
for s in SKILLS:
    with open(os.path.join(SKILLS_DIR, s, "evals", "evals.json"), encoding="utf-8") as fh:
        ev = json.load(fh)
    for e in ev["evals"]:
        key = f"{s}.{e['id']}"
        meta[key] = {"skill": s, "eval_id": str(e["id"]), "prompt": e["prompt"],
                     "expectations": e["expectations"]}
        cells.append((key, s))

with open(os.path.join(BASE, "meta.json"), "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=1)
with open(os.path.join(BASE, "cells.tsv"), "w", encoding="utf-8", newline="") as fh:
    for key, s in cells:
        fh.write(f"{key}\t{s}\n")

evals_args = [{"skill": m["skill"], "eval_id": m["eval_id"], "prompt": m["prompt"]} for m in meta.values()]
with open(os.path.join(BASE, "evals_args.json"), "w", encoding="utf-8") as fh:
    json.dump(evals_args, fh, indent=1)

print(f"prepped {len(meta)} evals across {len(SKILLS)} skills "
      f"(no treatment content -- arms differ by executor config only)")
for s in SKILLS:
    n = sum(1 for k in meta if meta[k]["skill"] == s)
    print(f"  {s}: {n} evals")
print(f"evals_args.json: {len(evals_args)} prompt-only records "
      f"(pass verbatim as harness.workflow.js args.evals)")
