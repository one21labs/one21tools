#!/usr/bin/env python3
"""Shared output-blinding layer (ADR 0052): one lib home imported by new harnesses
instead of a 10th dated-dir copy (the 9 existing copies are frozen snapshots, ADR 0041).

Three jobs (the first two are arm-blinding, ADR 0019 item 5):
  - assign_bids/write_blinded: secret-salted blind ids, per-item payload files carrying only
    whitelisted fields, plus the arm map the aggregator joins back on (flat records -> ADR 0026
    formats are the caller's job via bench_io).
  - NEUTRAL_SCHEMA_PROMPT / NEUTRAL_DECISION_PROMPT: the schema-normalization instructions the
    grading workflow runs as its FIRST stage, because output FORMAT is itself an arm tell
    (a retrospect agent's routed-fragments shape, an ADR-formatted decision) — issue #172's
    pre-registrations; blinding validated per-benchmark by a guess-the-arm audit.
  - capture_symmetry: pre-blinding per-arm exclusion-skew sweep (#191 item 2); contract in its
    docstring.
"""
import hashlib
import json
import random
import secrets
from pathlib import Path


def assign_bids(records, key_fn, salt=None):
    """[(bid, record)] with bid = sha256(salt + key_fn(record))[:12]. The salt is a fresh random
    secret unless given (tests; a re-run reusing its persisted salt): an unsalted hash of a public key (cell names carry the arm) is
    recomputable offline, which un-blinds every item. The caller must not write the salt where
    the grader can read it. key_fn must be unique per record — a duplicate key would silently
    overwrite its item file, so duplicates and hash collisions both raise."""
    salt = secrets.token_hex(16) if salt is None else salt
    out = []
    seen = {}
    for r in records:
        key = key_fn(r)
        bid = hashlib.sha256((salt + key).encode("utf-8")).hexdigest()[:12]
        if bid in seen:
            raise ValueError(f"duplicate key or bid collision: {key!r} vs {seen[bid]!r}")
        seen[bid] = key
        out.append((bid, r))
    return out


def write_blinded(records, graded_dir, key_fn, payload_fn, arm_key="arm",
                  allowed=("scenario", "response"), salt=None):
    """Write graded_dir/items/<bid>.json = {bid, **payload_fn(record)} and return the arm-map
    records [{bid, arm}] (in input order) for bench_io.dump_records — written by the caller
    OUTSIDE graded_dir, since the map is the un-blinding key. Payload keys are WHITELISTED
    (`allowed`): a blacklist of the arm key's one name let `condition`, `cell`, or a renamed arm
    through. Items are written in shuffled order so file mtimes do not recover the arm order.
    `salt` as in assign_bids: a re-run that must keep its bids (so existing grades still join)
    passes the salt it persisted, outside graded_dir, on the first run."""
    items = Path(graded_dir) / "items"
    items.mkdir(parents=True, exist_ok=True)
    bids = assign_bids(records, key_fn, salt)
    payloads = []
    for bid, r in bids:
        payload = payload_fn(r)
        extra = set(payload) - set(allowed)
        if extra:
            raise ValueError(f"payload for {bid} carries non-whitelisted keys {sorted(extra)}")
        payloads.append((bid, {"bid": bid, **payload}))
    random.SystemRandom().shuffle(payloads)
    for bid, payload in payloads:
        (items / f"{bid}.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return [{"bid": bid, arm_key: r[arm_key]} for bid, r in bids]


def capture_symmetry(records, response_fn, arm_key="arm", empty_chars=40, skew_threshold=0.1,
                     excluded_fn=None):
    """Per-arm EXCLUSION sweep run BEFORE blinding, over ALL records (#191 item 2): arm symmetry
    (ADR 0023) covers prompts; this extends it to what survives to grading. A record counts as
    excluded when excluded_fn(record) is truthy (pass the caller's whole exclusion rule: harness
    ERROR, failed artifact check, ...) or its response is under empty_chars. Returns
    {"arms": {arm: {n, excluded_n, excluded_rate, median_len}}, "skewed": bool} — skewed when
    some arm's exclusion rate exceeds the minimum arm's by more than skew_threshold. Run it on
    the records BEFORE excluding them, or it can never fire. A skewed sweep is an infrastructure
    defect to fix before grading (in #185 arm P had 3/24 empty captures vs 0/48 elsewhere),
    never signal."""
    by_arm = {}
    for r in records:
        n = len((response_fn(r) or "").strip())
        by_arm.setdefault(r[arm_key], []).append(
            (n, bool(excluded_fn and excluded_fn(r)) or n < empty_chars))
    arms = {}
    for arm, cells in sorted(by_arm.items()):
        lens = sorted(n for n, _ in cells)
        excluded_n = sum(1 for _, x in cells if x)
        arms[arm] = {"n": len(cells), "excluded_n": excluded_n,
                     "excluded_rate": round(excluded_n / len(cells), 3),
                     "median_len": lens[len(lens) // 2]}
    rates = [a["excluded_rate"] for a in arms.values()]
    skewed = bool(rates) and (max(rates) - min(rates)) > skew_threshold
    return {"arms": arms, "skewed": skewed}


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
