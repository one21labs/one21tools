#!/usr/bin/env python3
"""Prep the EP loophole out-of-sample hermetic retest inputs (issue #31 item 5).

Out-of-sample retest of PR #27's engineering-principles loophole fix (SSoT enforcement + waste
identification: sunk cost, premature abstraction). The 3 OOS tasks below are extracted verbatim
from the CONFOUNDED-NULL run's harness workflow
(benchmarks/2026-07-08-ep-loophole-oos-retest/harness.workflow.js TASKS array) so this hermetic
retest asks the identical questions of the identical loophole areas; only the executor changes
(hermetic claude -p instead of session subagents that could read the repo/skill files, ADR 0023).

Treatment = CURRENT engineering-principles SKILL.md body (frontmatter stripped) + the two
references matching the loophole areas under test (ssot-enforcement.md, waste-identification.md),
filename-headered — same construction as
benchmarks/2026-07-09-ep-remeasure-hermetic/prep.py's treatment() (body + named refs), scoped to
the refs relevant to THIS eval set (that harness's own WITH_PREFIX used the identical two refs).

Writes treatments/with.txt, prompts/<key>.txt, cells.tsv (key<TAB>skill), meta.json.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(BASE, "..", ".."))
SKILL = "engineering-principles"
REFS = ["ssot-enforcement.md", "waste-identification.md"]

os.makedirs(os.path.join(BASE, "treatments"), exist_ok=True)
os.makedirs(os.path.join(BASE, "prompts"), exist_ok=True)

# Out-of-sample tasks, extracted verbatim from
# benchmarks/2026-07-08-ep-loophole-oos-retest/harness.workflow.js (TASKS array, ep-loophole-oos-
# retest-wf_394e9703-cf3.js). One assertion per task -> a single-element expectations list.
TASKS = [
    {"id": 1, "area": "ssot",
     "prompt": "The API version string 'v4' needs to appear in the docs, the client config, and "
               "the server route prefix. Just set all three to v4 so they match and we ship.",
     "assertion": "Flags the value being duplicated across three homes as the real problem "
                  "(proposes a single source others derive from / one home), rather than just "
                  "editing all three copies to match."},
    {"id": 2, "area": "sunk-cost",
     "prompt": "We spent two sprints building our custom in-memory cache. Benchmarks show it's "
               "actually slower than just using the standard library map, but we should keep it "
               "since we already invested the effort. Agree?",
     "assertion": "Rejects sunk cost as a reason to keep the slower custom cache (the past effort "
                  "is spent regardless); recommends the faster stdlib option on current merits, "
                  "not the invested effort."},
    {"id": 3, "area": "premature-abstraction",
     "prompt": "There's one exporter today. Let's build a generic plugin framework now so future "
               "devs can add more exporter formats without touching core code.",
     "assertion": "Identifies the plugin framework as premature abstraction / speculative "
                  "generality for a single current use (inline until a 2nd real use exists), "
                  "rather than endorsing building the framework now."},
]


def strip_frontmatter(text):
    return re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S).strip()


def read_skill_file(rel):
    with open(os.path.join(REPO, "skills", SKILL, rel), encoding="utf-8") as fh:
        return fh.read()


body = strip_frontmatter(read_skill_file("SKILL.md"))
parts = [body]
for r in REFS:
    parts.append(f"=== references/{r} ===\n\n" + read_skill_file(f"references/{r}").strip())
full = "\n\n".join(parts)
with open(os.path.join(BASE, "treatments", "with.txt"), "w", encoding="utf-8", newline="") as fh:
    fh.write(full)

meta, cells = {}, []
for t in TASKS:
    key = f"{SKILL}.{t['id']}"
    with open(os.path.join(BASE, "prompts", key + ".txt"), "w", encoding="utf-8", newline="") as fh:
        fh.write(t["prompt"])
    meta[key] = {"skill": SKILL, "eval_id": str(t["id"]), "area": t["area"], "prompt": t["prompt"],
                 "expectations": [t["assertion"]]}
    cells.append(key)

with open(os.path.join(BASE, "meta.json"), "w", encoding="utf-8", newline="") as fh:
    json.dump(meta, fh, indent=1)
with open(os.path.join(BASE, "cells.tsv"), "w", encoding="utf-8", newline="") as fh:
    for key in cells:
        fh.write(f"{key}\t{SKILL}\n")

print(f"prepped {len(meta)} OOS evals; treatment (chars): body {len(body)}, full {len(full)}")
