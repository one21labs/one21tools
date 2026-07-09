#!/usr/bin/env python3
"""Prep the issue #55 3-skill re-measure inputs (ADR 0027 arm pattern, generalized).

Three arms per skill, three skills (code-standards, building-skills, optimizing-context).
Treatment = SKILL.md BODY (frontmatter stripped) + the skill's TOUCHED reference files,
filename-headered, symmetric across the with-arms:
  treatments/<skill>.with-old.txt  <- the checkout's files (main lineage)
  treatments/<skill>.with-new.txt  <- `git show <NEW_REF>:...` (default 76a67bf, skills-improve-55)
The touched-file set per skill is DERIVED from the draft's diff and asserted against the
hand-listed REFS (issue #63's lesson: a treatment blind to where the edits live is a rigged null).
Writes prompts/<key>.txt, cells.tsv, meta.json, treatments/costs.json (measured, both ADR 0019
bounds per skill).
"""
import json, os, re, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(BASE, "..", ".."))
NEW_REF = os.environ.get("SKILLS_NEW_REF", "76a67bf")
SKILLS = {
    "code-standards": [],
    "building-skills": [],
    "optimizing-context": ["claude-md.md", "mechanism-selection.md"],
}

os.makedirs(os.path.join(BASE, "treatments"), exist_ok=True)
os.makedirs(os.path.join(BASE, "prompts"), exist_ok=True)


def git(*args):
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


# Poka-yoke, PROVISIONAL (issue #63 is an open /decide item; this run is its empirical trial):
# the treatment's file set must equal what the draft actually touched.
for skill, refs in SKILLS.items():
    touched = set(git("diff", "--name-only", f"HEAD...{NEW_REF}", "--",
                      f"skills/{skill}/").split())
    expected = {f"skills/{skill}/SKILL.md"} | {f"skills/{skill}/references/{r}" for r in refs}
    assert touched == expected, (
        f"{skill}: treatment file set {sorted(expected)} != draft's touched set {sorted(touched)} "
        f"- fix SKILLS or the draft before running (issue #63)")


def strip_frontmatter(text):
    return re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S).strip()


def old_file(skill, rel):
    with open(os.path.join(REPO, "skills", skill, rel), encoding="utf-8") as fh:
        return fh.read()


def new_file(skill, rel):
    return git("show", f"{NEW_REF}:skills/{skill}/{rel}")


def treatment(skill, read):
    body = strip_frontmatter(read(skill, "SKILL.md"))
    parts = [body]
    for r in SKILLS[skill]:
        parts.append(f"=== references/{r} ===\n\n" + read(skill, f"references/{r}").strip())
    return body, "\n\n".join(parts)


meta, cells, costs = {}, [], {"new_ref": NEW_REF, "skills": {}}
for skill, refs in SKILLS.items():
    old_body, old_full = treatment(skill, old_file)
    new_body, new_full = treatment(skill, new_file)
    for arm, text in ((f"{skill}.with-old", old_full), (f"{skill}.with-new", new_full)):
        with open(os.path.join(BASE, "treatments", arm + ".txt"), "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
    costs["skills"][skill] = {"refs": refs,
                              "body_chars": {"with-old": len(old_body), "with-new": len(new_body)},
                              "full_chars": {"with-old": len(old_full), "with-new": len(new_full)}}
    with open(os.path.join(REPO, "skills", skill, "evals", "evals.json"), encoding="utf-8") as fh:
        ev = json.load(fh)
    for e in ev["evals"]:
        key = f"{skill}.{e['id']}"
        with open(os.path.join(BASE, "prompts", key + ".txt"), "w", encoding="utf-8", newline="") as fh:
            fh.write(e["prompt"])
        meta[key] = {"skill": skill, "eval_id": str(e["id"]), "prompt": e["prompt"],
                     "expectations": e["expectations"]}
        cells.append((key, skill))

with open(os.path.join(BASE, "meta.json"), "w", encoding="utf-8", newline="") as fh:
    json.dump(meta, fh, indent=1)
with open(os.path.join(BASE, "cells.tsv"), "w", encoding="utf-8", newline="") as fh:
    for key, s in cells:
        fh.write(f"{key}\t{s}\n")
with open(os.path.join(BASE, "treatments", "costs.json"), "w", encoding="utf-8", newline="") as fh:
    json.dump(costs, fh, indent=1)

print(f"prepped {len(meta)} evals across {len(SKILLS)} skills (touched-set assertions passed)")
for skill, c in costs["skills"].items():
    b, f = c["body_chars"], c["full_chars"]
    print(f"  {skill}: body {b['with-old']}->{b['with-new']} ({b['with-new']-b['with-old']:+d}), "
          f"full {f['with-old']}->{f['with-new']} ({f['with-new']-f['with-old']:+d})")
