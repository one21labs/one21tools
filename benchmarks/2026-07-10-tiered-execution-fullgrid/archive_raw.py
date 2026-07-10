#!/usr/bin/env python3
"""Post-run raw-output archiver (ADR 0023 sample_rule + ADR 0026 gzip-the-rest).

Thin driver over benchmarks/lib/bench_io.sample_and_archive_raw -- reused, not reimplemented.
Keeps 1 raw outputs/*.txt per (skill, eval_id, arm) group (sorted-rep order) as the deterministic
on-main audit sample; archives the rest into outputs/all.tar.gz. Run once, after grading, before
commit.

Note: prior 3-arm precedent (benchmarks/2026-07-09-ep-remeasure-hermetic/archive_raw.py) grouped by
(eval_id, arm) only, which is safe there because that run covered a single skill. This benchmark
spans 4 skills whose eval_id namespaces overlap (each skill has evals 1-6), so the group key here
includes skill to avoid cross-skill collisions in the kept sample.
"""
import os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "..", "lib"))
from bench_io import sample_and_archive_raw  # ADR 0026 shared lib

OUT = os.path.join(BASE, "outputs")
KEEP = 1   # loose raw .txt retained per (skill, eval_id, arm) as the sample -- ADR 0023 sample_rule


def group_of(name):
    parts = name[:-4].split(".")   # <skill>.<eval_id>.<arm>.<rep>.txt
    return tuple(parts[:3]) if len(parts) == 4 else (name,)


def main():
    if not os.path.isdir(OUT) or not any(f.endswith(".txt") for f in os.listdir(OUT)):
        print("no raw outputs to archive")
        return
    kept, archived = sample_and_archive_raw(OUT, keep_per_group=KEEP, group_fn=group_of)
    print(f"kept {kept} loose as the sample, archived {archived} -> outputs/all.tar.gz")


if __name__ == "__main__":
    main()
