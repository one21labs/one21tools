#!/usr/bin/env python3
"""Post-run raw-output archiver (ADR 0026): gzip the full set, keep a readable sample.

Tars+gzips every raw outputs/<skill>.<eval_id>.<arm>.<rep>.txt into outputs/all.tar.gz (the
complete audit archive), then deletes the loose .txt EXCEPT KEEP per (eval_id, arm) retained as
the committed readable sample. Run exactly once, after the grid + grading, before commit.
"""
import os, glob, tarfile

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "outputs")
ARCHIVE = os.path.join(OUT, "all.tar.gz")
KEEP = 1   # loose raw .txt retained per (eval_id, arm) as the sample


def main():
    txts = sorted(f for f in glob.glob(os.path.join(OUT, "*.txt")))
    if not txts:
        print("no raw outputs to archive")
        return
    with tarfile.open(ARCHIVE, "w:gz") as tar:
        for f in txts:
            tar.add(f, arcname=os.path.basename(f))
    seen, sample = {}, set()
    for f in txts:
        parts = os.path.basename(f)[:-4].split(".")
        if len(parts) != 4:
            continue
        _skill, eval_id, arm, _rep = parts
        k = (eval_id, arm)
        if seen.get(k, 0) < KEEP:
            sample.add(f)
            seen[k] = seen.get(k, 0) + 1
    removed = 0
    for f in txts:
        if f not in sample:
            os.remove(f)
            removed += 1
    print(f"archived {len(txts)} raw outputs -> {os.path.relpath(ARCHIVE, BASE)}; "
          f"kept {len(sample)} loose as sample, removed {removed}")


if __name__ == "__main__":
    main()
