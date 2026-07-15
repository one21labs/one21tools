#!/usr/bin/env python3
"""Shared output-blinding layer (ADR 0052 decision 4): one lib home imported by new harnesses
instead of a 10th dated-dir copy (the 9 existing copies are frozen snapshots, ADR 0041).

Two jobs, both arm-blinding (ADR 0019 item 5):
  - assign_bids/write_blinded: deterministic blind ids, per-item payload files WITHOUT the arm
    field, plus the arm map the aggregator joins back on (flat records -> ADR 0026 formats are
    the caller's job via bench_io).
  - NEUTRAL_SCHEMA_PROMPT / NEUTRAL_DECISION_PROMPT: the schema-normalization instructions the
    grading workflow runs as its FIRST stage, because output FORMAT is itself an arm tell
    (a retrospect agent's routed-fragments shape, an ADR-formatted decision) — issue #172's
    pre-registrations; blinding validated per-benchmark by a guess-the-arm audit.
"""
import hashlib
import json
from pathlib import Path


def assign_bids(records, key_fn):
    """[(bid, record)] with bid = sha256(key_fn(record))[:12] — deterministic, arm not
    inferable from the bid. key_fn must be unique per record — a duplicate key would
    silently overwrite its item file, so duplicates and hash collisions both raise."""
    out = []
    seen = {}
    for r in records:
        key = key_fn(r)
        bid = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
        if bid in seen:
            raise ValueError(f"duplicate key or bid collision: {key!r} vs {seen[bid]!r}")
        seen[bid] = key
        out.append((bid, r))
    return out


def write_blinded(records, graded_dir, key_fn, payload_fn, arm_key="arm"):
    """Write graded_dir/items/<bid>.json = payload_fn(record) (MUST NOT contain the arm; a
    payload carrying arm_key raises) and return the arm-map records
    [{bid, arm, **whatever key fields the caller adds later}] for bench_io.dump_records."""
    items = Path(graded_dir) / "items"
    items.mkdir(parents=True, exist_ok=True)
    arm_map = []
    for bid, r in assign_bids(records, key_fn):
        payload = {"bid": bid, **payload_fn(r)}
        if arm_key in payload:
            raise ValueError(f"payload for {bid} leaks {arm_key!r}")
        (items / f"{bid}.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")
        arm_map.append({"bid": bid, arm_key: r[arm_key]})
    return arm_map


NEUTRAL_SCHEMA_PROMPT = (
    "Extract every DISTINCT problem/defect finding asserted in the review text below into a "
    "JSON array, one object per finding: {\"claim\": <one-sentence restatement in neutral "
    "wording>, \"evidence\": <the cite exactly as given: commit sha, file:line, file, or "
    "\"none\">}. Preserve every finding (do not judge merit); merge exact duplicates; strip "
    "all formatting, headers, role language, and improvement/fix proposals. Output ONLY the "
    "JSON array."
)

NEUTRAL_DECISION_PROMPT = (
    "Extract the decision artifact below into ONE JSON object with exactly these keys: "
    "{\"decision\": <one sentence>, \"options\": [<each option considered, one line each, "
    "marking rejected ones as \"REJECTED: <option> — <reason>\">], \"criterion\": <the stated "
    "acceptance/reopen criterion, or \"none\">, \"risks\": [<named risks>], \"assumptions\": "
    "[<named assumptions>]}. Neutral wording; strip all formatting, section headers, and any "
    "role/process language (panels, advisors, ADR ids). Output ONLY the JSON object."
)
