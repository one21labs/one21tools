#!/usr/bin/env python3
"""Post-run raw-output archiver: keep a small readable sample, gzip the full set.

Tars+gzips EVERY raw outputs/<section>.<id>.<arm>.<rep>.txt into outputs/all.tar.gz (the complete
audit archive), then deletes the loose .txt EXCEPT ~KEEP per (section, arm) retained as the committed
readable sample. Run after the grid + grading, before commit. Idempotent-ish: re-running rebuilds the
archive from whatever loose .txt remain, so run it exactly once post-grid.
"""
import os, glob, tarfile

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "outputs")
ARCHIVE = os.path.join(OUT, "all.tar.gz")
KEEP = 2   # loose raw .txt retained per (section, arm) as the sample


def main():
    txts = sorted(f for f in glob.glob(os.path.join(OUT, "*.txt")))
    if not txts:
        print("no raw outputs to archive")
        return
    with tarfile.open(ARCHIVE, "w:gz") as tar:
        for f in txts:
            tar.add(f, arcname=os.path.basename(f))
    # choose the sample: first KEEP per (section, arm)
    seen, sample = {}, set()
    for f in txts:
        parts = os.path.basename(f)[:-4].split(".")
        if len(parts) != 4:
            continue
        section, _task_id, arm, _rep = parts
        k = (section, arm)
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
