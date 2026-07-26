#!/usr/bin/env bash
# PreToolUse hook (matcher: Edit|Write): the PREVENT rung for git-tellable backstory in docs
# (CLAUDE.md "Muda — ruthlessly cut on sight"; backstory rules live in ssot-enforcement.md;
# ladder: ADR 0047). ADR 0018 already put a backstory sweep in /retrospect — the DETECT-LATE rung,
# after the prose has shipped. It has not held: the owner caught two insertions by hand on
# 26-Jul-2026 alone, in a session that had already been corrected for it. This moves the catch to
# the moment of the edit, where budget-edit-guard already lives.
#
# WHAT IT CATCHES: prose that narrates the document's OWN prior state or a change to it — "an
# earlier draft", "was renamed to X", "this used to say", "that clause is deleted". Git already
# records every one of those, so restating them in the doc is duplication with a decay date.
# It is a LEXICAL check on high-precision phrases, not a semantic one: it cannot catch backstory
# written without these markers, and it is not a substitute for the /retrospect sweep, which stays.
#
# WHERE IT DOES NOT FIRE: frozen dated benchmark dirs (append-only historical records, ADR 0041),
# docs/pdca logs, and this file. ADRs are NOT exempt — one of the two caught instances was in an
# ADR Context line, which is exactly where "harmless historical note" is most tempting.
#
# Fails OPEN on any error: a broken guard must never block edits.
#
# liveness: per-event-exempt -- a deny fires only when someone writes backstory, which may
# legitimately never happen in a window (ADR 0086 (b)).
# canary: {"event":"PreToolUse","tool":"Write","stdin":{"tool_name":"Write","tool_input":{"file_path":"__FIXTURE__/docs/decisions/0001-canary.md","content":"Shipped as MSH-baby and renamed to MSH on owner direction, 26-Jul-2026."}},"expect":{"deny":true}}
# canary: {"event":"PreToolUse","tool":"Write","stdin":{"tool_name":"Write","tool_input":{"file_path":"__FIXTURE__/README.md","content":"An earlier draft of this paragraph said otherwise; that clause is deleted."}},"expect":{"deny":true}}
input=$(cat)
export BSG_INPUT="$input"
python3 <<'PYEOF' 2>/dev/null || exit 0
import json, os, re, sys
try:
    d = json.loads(os.environ["BSG_INPUT"])
    ti = d.get("tool_input") or {}
    fp = ti.get("file_path") or ""
    if not fp.endswith(".md"):
        sys.exit(0)
    # Frozen/append-only records legitimately narrate history; live docs do not.
    if re.search(r"(^|/)(benchmarks/20\d\d-|docs/pdca/)", fp) or "backstory-edit-guard" in fp:
        sys.exit(0)
    # Only the text this edit ADDS is scanned. Editing around existing prose must not be blocked
    # by prose the edit is not introducing — a guard that fires on untouched content is a guard
    # people learn to route around.
    added = ti.get("content") if "content" in ti else ti.get("new_string") or ""
    if not added:
        sys.exit(0)

    # High-precision markers only. Each names the document's own prior state or a change to it.
    # Tuned against the two real 26-Jul instances plus the forms that recur in this repo's history.
    MARKERS = [
        r"an? (earlier|previous|prior|first) (draft|pass|version|cut)\b",
        r"\bearlier (draft|version) of this\b",
        r"\bwas renamed\b", r"\brenamed (from|to)\b",
        r"\bused to (say|be|read|live)\b",
        r"\bpreviously (said|stated|lived|called|named)\b",
        r"\bformerly (called|named|known as)\b",
        r"\b(this|which) replaced\b",
        r"\bno longer (says|reads|lives)\b",
        r"\b(clause|sentence|paragraph|line) (is|was) (deleted|removed)\b",
        r"\bwas added then removed\b",
        r"\bshipped as .{0,40}\band renamed\b",
    ]
    hits = []
    for m in MARKERS:
        found = re.search(m, added, re.I)
        if found:
            line = added[:found.start()].count("\n") + 1
            snippet = added.splitlines()[line - 1].strip()[:110] if added.splitlines() else ""
            hits.append((found.group(0), line, snippet))
    if not hits:
        sys.exit(0)

    # Gate-hit telemetry (ADR 0080): observability only, never in the failure path.
    try:
        from datetime import datetime, timezone
        pdca = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", "."), "docs", "pdca")
        if os.path.isdir(pdca):
            with open(os.path.join(pdca, "gate-hits.txt"), "a", encoding="utf-8") as lf:
                lf.write(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                         + f" gate-hit backstory-edit-guard {fp}\n")
    except Exception:
        pass

    phrase, line, snippet = hits[0]
    reason = (f"backstory-edit-guard: this edit adds git-tellable backstory to {fp} — "
              f'line {line} of the added text says "{phrase}"'
              + (f' in: "{snippet}"' if snippet else "")
              + ". Git already records what this document used to say, so restating it here is "
                "duplication with a decay date (CLAUDE.md 'git-tellable backstory'; rules: "
                "ssot-enforcement.md). Delete the narration and state only what is true NOW. If "
                "the history is genuinely load-bearing for a reader, it belongs in the commit "
                "message or an ADR Justification, not in the prose.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
          "permissionDecision": "deny", "permissionDecisionReason": reason}}))
except Exception:
    sys.exit(0)  # fail open
PYEOF
exit 0
