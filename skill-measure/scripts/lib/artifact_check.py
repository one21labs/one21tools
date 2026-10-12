#!/usr/bin/env python3
"""Graded-artifact validation + ERROR-cell rule (#191 item 1). Stdlib only, pure.

Capture failures graded as quality zeros corrupt the verdict (#185's failure mode).
The rule this module mechanizes: a cell whose graded
artifact fails a mechanical non-emptiness/shape check is an ERROR cell (infrastructure,
recorded and resumable), never a quality 0. Run it BEFORE blinding; an ERROR cell never
reaches a grader.
"""


def check_artifact(text, min_chars=40, require=()):
    """Mechanical shape check on the artifact a grader will see.

    Returns (ok, reason). `min_chars` guards non-emptiness after stripping; `require` is an
    optional tuple of substrings the artifact must contain (e.g. a pre-registered section
    marker). Semantic quality is the GRADER's job — never test it here.
    """
    stripped = (text or "").strip()
    if len(stripped) < min_chars:
        return False, f"artifact under {min_chars} chars ({len(stripped)})"
    for marker in require:
        if marker not in stripped:
            return False, f"artifact missing required marker {marker!r}"
    return True, ""


def classify_cells(records, artifact_fn, min_chars=40, require=()):
    """Split records into gradable cells and ERROR cells.

    `artifact_fn(record)` extracts the graded-artifact text. A record whose harness already
    marked an execution error is an ERROR cell regardless of its text. Returns
    (ok_records, error_records) where each error record is (record, reason).
    """
    ok, errors = [], []
    for r in records:
        harness_error = (r.get("summary") or {}).get("error")
        if harness_error:
            errors.append((r, f"harness error: {harness_error}"))
            continue
        passed, reason = check_artifact(artifact_fn(r), min_chars=min_chars, require=require)
        (ok.append(r) if passed else errors.append((r, reason)))
    return ok, errors
