#!/usr/bin/env python3
"""Prep the hermetic CLAUDE.md-section ablation inputs from tasks.json + treatments/.

tasks.json {section: [{id, prompt, pass_criterion}]} is the task SSoT; treatments/<section>.txt (the
section text, incl. its `##` header) is the "with" treatment. This writes prompts/<section>.<id>.txt
(the task prompt verbatim), meta.json (key -> {section, task_id, prompt, expectations:[pass_criterion]}),
and cells.tsv (key<TAB>section) — the SSoT the harness and the blind grader both read. ALL writes use
newline='' (a prior CRLF cells.tsv corrupted a run). key = "<section>.<id>"; neither may contain a dot
(blind.py splits the output filename on '.').
"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE, "tasks.json"), encoding="utf-8") as fh:
    tasks = json.load(fh)
os.makedirs(os.path.join(BASE, "prompts"), exist_ok=True)

meta, cells = {}, []
for section, items in tasks.items():
    if "." in section:
        raise SystemExit(f"section name has a dot (breaks filename split): {section!r}")
    tpath = os.path.join(BASE, "treatments", section + ".txt")
    if not os.path.exists(tpath):
        raise SystemExit(f"missing treatment for section {section!r}: {tpath}")
    for t in items:
        tid = t["id"]
        if "." in tid:
            raise SystemExit(f"task id has a dot (breaks filename split): {tid!r}")
        key = f"{section}.{tid}"
        with open(os.path.join(BASE, "prompts", key + ".txt"), "w", encoding="utf-8", newline="") as fh:
            fh.write(t["prompt"])
        meta[key] = {"section": section, "task_id": tid, "prompt": t["prompt"],
                     "expectations": [t["pass_criterion"]]}
        cells.append((key, section))

with open(os.path.join(BASE, "meta.json"), "w", encoding="utf-8", newline="") as fh:
    json.dump(meta, fh, ensure_ascii=False, separators=(",", ":"))   # gitignored, machine-read -> minified
with open(os.path.join(BASE, "cells.tsv"), "w", encoding="utf-8", newline="") as fh:
    for key, section in cells:
        fh.write(f"{key}\t{section}\n")

print(f"prepped {len(meta)} tasks across {len(tasks)} sections")
for section, items in tasks.items():
    with open(os.path.join(BASE, "treatments", section + ".txt"), encoding="utf-8") as fh:
        tc = len(fh.read())
    print(f"  {section}: {len(items)} tasks, treatment {tc} chars")
