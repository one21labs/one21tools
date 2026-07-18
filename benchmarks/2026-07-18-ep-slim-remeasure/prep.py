#!/usr/bin/env python3
"""Prep the 3-arm ep-slim re-measure inputs (issue #248).

Arms: without / with-full / with-slim, engineering-principles only. Treatment construction is
IDENTICAL across arms (07-09/ep-partition pattern): stripped SKILL.md body, then the 3 touched
reference files, each block prefixed "=== references/<name> ===".
  with-full : source files pinned at FULL_COMMIT (pre-slim main) via `git show` — the currently
              shipped skill, byte-stable regardless of working-tree state.
  with-slim : WORKING-TREE source files verbatim — the slim draft as it would ship.

ADR 0024 2d guard (anti-rigged-null): the touched-file set is derived from
`git diff --name-only FULL_COMMIT -- skills/engineering-principles` and every touched file must
be either IN the treatment set or in the PRE-REGISTERED exclusion list
(references/ENGINEERING_PRINCIPLES.md — the deep-theory demotion target, never part of the
07-09/ep-partition treatment construction; evals/ is harness input, not treatment). Fails loudly
otherwise. Also asserts the two treatments actually differ.

Writes treatments/*.txt, prompts/<key>.txt, cells.tsv, meta.json, treatments/costs.json.
"""
import json, os, re, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(BASE, "..", ".."))
SKILL = "engineering-principles"
REFS = ["ssot-enforcement.md", "design-review.md", "root-cause-analysis.md"]
FULL_COMMIT = "bc6957d7ca3fb4c469b975df2962665b1e2ff584"
TREATMENT_SET = {f"skills/{SKILL}/SKILL.md"} | {f"skills/{SKILL}/references/{r}" for r in REFS}
EXCLUDED = {f"skills/{SKILL}/references/ENGINEERING_PRINCIPLES.md"}

os.makedirs(os.path.join(BASE, "treatments"), exist_ok=True)
os.makedirs(os.path.join(BASE, "prompts"), exist_ok=True)


def strip_frontmatter(text):
    return re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S).strip()


def worktree_file(rel):
    with open(os.path.join(REPO, "skills", SKILL, rel), encoding="utf-8") as fh:
        return fh.read()


def pinned_file(rel):
    return subprocess.run(
        ["git", "-C", REPO, "show", f"{FULL_COMMIT}:skills/{SKILL}/{rel}"],
        capture_output=True, text=True, check=True).stdout


def treatment(body, ref_reader):
    parts = [body] if body.strip() else []
    for r in REFS:
        content = ref_reader(r).strip()
        if content:
            parts.append(f"=== references/{r} ===\n\n" + content)
    return "\n\n".join(parts)


# ADR 0024 2d: assert the draft's touched files are covered by the treatment (or pre-excluded).
touched = subprocess.run(
    ["git", "-C", REPO, "diff", "--name-only", FULL_COMMIT, "--", f"skills/{SKILL}"],
    capture_output=True, text=True, check=True).stdout.split()
uncovered = [t for t in touched if t not in TREATMENT_SET and t not in EXCLUDED
             and not t.startswith(f"skills/{SKILL}/evals/")]
if uncovered:
    raise SystemExit(f"prep.py: draft touches files the treatment is blind to (rigged null): {uncovered}")
in_treatment = [t for t in touched if t in TREATMENT_SET]
if not in_treatment:
    raise SystemExit("prep.py: draft touches NO treatment file -- nothing to measure")
print(f"touched-file guard OK: {len(in_treatment)} treatment files changed, "
      f"excluded (pre-registered, never ships): {sorted(set(touched) & EXCLUDED)}")

full_text = treatment(strip_frontmatter(pinned_file("SKILL.md")),
                      lambda r: pinned_file(f"references/{r}"))
slim_text = treatment(strip_frontmatter(worktree_file("SKILL.md")),
                      lambda r: worktree_file(f"references/{r}"))
if full_text == slim_text:
    raise SystemExit("prep.py: with-full and with-slim treatments are identical -- nothing to measure")

ARM_TEXT = {"with-full": full_text, "with-slim": slim_text}
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

costs = {"refs": REFS, "full_commit": FULL_COMMIT,
         "full_chars": {arm: len(ARM_TEXT[arm]) for arm in ARM_TEXT},
         "chars_delta_slim_minus_full": len(slim_text) - len(full_text)}
with open(os.path.join(BASE, "treatments", "costs.json"), "w", encoding="utf-8", newline="") as fh:
    json.dump(costs, fh, indent=1)

print(f"prepped {len(meta)} evals; with-full={len(full_text)} chars, with-slim={len(slim_text)} chars, "
      f"delta={costs['chars_delta_slim_minus_full']:+d}")
