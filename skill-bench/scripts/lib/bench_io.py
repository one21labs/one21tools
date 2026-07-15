#!/usr/bin/env python3
"""Reusable benchmark-artifact IO (ADR 0026): format convention + sampled raw retention.

ARCHITECTURE ROLE: the one home for benchmark-record serialization (dump_records/load_records)
and for bounding raw-output byte cost (sample_and_archive_raw — archive, never discard).
Format-choice rationale and size measurements live in ADR 0026; per-function contracts live in
the docstrings below.

DESIGN CONSTRAINTS: stdlib only.
"""
import csv
import json
import os
import tarfile

# CSV default per ADR 0026 (owner preference; CSV == TSV in size for delimiter-free scalar records).
RAW_FORMATS = ("csv", "tsv", "jsonl")
_DELIMS = {"csv": ",", "tsv": "\t"}


def _flatten_value(key, value):
    """Yield (column, scalar) pairs for one record field, expanding nested list/dict values so a
    delimited writer never has to quote a composite value (ADR 0026). A 2-element list/tuple is
    treated as a confidence interval and named `<key>_lo`/`<key>_hi`; other lengths get
    `<key>_0`, `<key>_1`, ...; dict values get `<key>_<subkey>` per item. Scalars pass through
    unchanged.
    """
    if isinstance(value, (list, tuple)):
        if len(value) == 2:
            yield f"{key}_lo", value[0]
            yield f"{key}_hi", value[1]
        else:
            for i, v in enumerate(value):
                yield f"{key}_{i}", v
    elif isinstance(value, dict):
        for subkey, v in value.items():
            yield f"{key}_{subkey}", v
    else:
        yield key, value


def _flatten_record(record):
    """Flatten one record's nested values into a flat dict (see _flatten_value)."""
    flat = {}
    for key, value in record.items():
        for col, val in _flatten_value(key, value):
            flat[col] = val
    return flat


def dump_records(records, path, fmt="csv"):
    """Write `records` (list of dict, same keys) to `path` as csv/tsv/jsonl. csv/tsv flatten
    nested list/dict values into columns first (ADR 0026), so a field never needs quoting. Returns
    path.
    """
    if fmt in _DELIMS:
        flat_records = [_flatten_record(r) for r in records]
        fieldnames = list(flat_records[0].keys()) if flat_records else []
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter=_DELIMS[fmt])
            writer.writeheader()
            writer.writerows(flat_records)
    elif fmt == "jsonl":
        with open(path, "w", newline="", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record, separators=(",", ":")) + "\n")
    else:
        raise ValueError(f"unknown fmt {fmt!r}, expected one of {RAW_FORMATS}")
    return path


def load_records(path, fmt="csv"):
    """Read records back from a file `dump_records` wrote. Returns list of dict. For csv/tsv this
    returns the flattened columns as written (e.g. `ci_lo`/`ci_hi`), not the original nesting.
    """
    if fmt in _DELIMS:
        with open(path, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh, delimiter=_DELIMS[fmt]))
    elif fmt == "jsonl":
        with open(path, encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]
    else:
        raise ValueError(f"unknown fmt {fmt!r}, expected one of {RAW_FORMATS}")


def sample_and_archive_raw(outputs_dir, keep_per_group, group_fn, archive_path=None):
    """Keep `keep_per_group` raw files per group in `outputs_dir` untouched (the deterministic
    audit sample, ADR 0023) and gzip-archive the rest into one `archive_path` (default
    outputs_dir/all.tar.gz), then remove the archived originals — bounding the byte cost of raw
    output (ADR 0026) without silently discarding anything.

    `group_fn(filename) -> group key` (e.g. everything before the replicate index) groups the raw
    files; within a group, files are kept in sorted-filename order — a deterministic sample, never
    a random draw (ADR 0023 rejected seeded-random for the reopen-conditions it breaks).

    Returns (kept, archived) file counts.
    """
    archive_path = archive_path or os.path.join(outputs_dir, "all.tar.gz")
    names = sorted(
        f for f in os.listdir(outputs_dir)
        if os.path.isfile(os.path.join(outputs_dir, f)) and f != os.path.basename(archive_path)
    )

    groups = {}
    for name in names:
        groups.setdefault(group_fn(name), []).append(name)

    kept, archived = [], []
    for key in sorted(groups):
        group_names = groups[key]
        kept.extend(group_names[:keep_per_group])
        archived.extend(group_names[keep_per_group:])

    with tarfile.open(archive_path, "w:gz") as tar:
        for name in archived:
            tar.add(os.path.join(outputs_dir, name), arcname=name)
    for name in archived:
        os.remove(os.path.join(outputs_dir, name))

    return len(kept), len(archived)
