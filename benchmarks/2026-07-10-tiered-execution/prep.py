#!/usr/bin/env python3
"""Prep the tiered-execution benchmark inputs (issue #41) from the live eval sets.

Candidate pool = the implementation-shaped evals: prompts whose deliverable is a concrete
artifact (module/file/skill/frontmatter/CLAUDE.md contents), not advice or review — the tiered
plan->implement->validate loop only applies where there is an artifact to implement. Review/
analysis-shaped evals (code-standards.2, engineering-principles.1-5, optimizing-context.3,
building-skills.4) are excluded.

Writes prompts/<key>.txt (eval prompt verbatim), meta.json (key -> {skill, eval_id, prompt,
expectations} — the SSoT for the harness and blind grader), candidates.txt (one key per line,
pre-screen input). tasks.txt (the 8 keys the pre-screen selects) is written by the pre-screen
analysis, not here.
"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.abspath(os.path.join(BASE, "..", "..", "skills"))
IMPL = {
    "code-standards": [1, 3, 4, 5, 6],
    "building-skills": [1, 2, 3, 5, 6],
    "optimizing-context": [1, 2, 4, 5, 6],
    "engineering-principles": [6],
}
os.makedirs(os.path.join(BASE, "prompts"), exist_ok=True)

meta, keys = {}, []
for s, ids in IMPL.items():
    with open(os.path.join(SKILLS_DIR, s, "evals", "evals.json"), encoding="utf-8") as fh:
        ev = {e["id"]: e for e in json.load(fh)["evals"]}
    for i in ids:
        e = ev[i]
        key = f"{s}.{i}"
        with open(os.path.join(BASE, "prompts", key + ".txt"), "w", encoding="utf-8", newline="") as fh:
            fh.write(e["prompt"])
        meta[key] = {"skill": s, "eval_id": str(i), "prompt": e["prompt"],
                     "expectations": e["expectations"]}
        keys.append(key)

with open(os.path.join(BASE, "meta.json"), "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=1)
with open(os.path.join(BASE, "candidates.txt"), "w", encoding="utf-8", newline="") as fh:
    fh.write("\n".join(keys) + "\n")
print(f"prepped {len(keys)} candidate tasks: {keys}")
