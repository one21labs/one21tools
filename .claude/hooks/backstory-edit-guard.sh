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
# Path skeleton + gate-hit telemetry, one home for every file_path hook. This repo-local hook
# sources the pdca-workflow plugin's copy from the working tree (the plugin is the shipped
# artifact and owns the skeleton; .claude/hooks are its in-repo consumers). Script-relative, so
# it also resolves under the canary runner's throwaway project dir.
. "$(dirname "${BASH_SOURCE[0]}")/../../pdca-workflow/hooks/lib/hook-lib.sh" 2>/dev/null || exit 0
input=$(cat)
export BSG_INPUT="$input"
export BSG_FP="$(hook_fp "$input")"   # forward slashes + absolute, same as every sibling hook:
                                      # the exemption match below is a path test, and a raw
                                      # Windows path does not match the docs/pdca arm.
# The python body's only stdout is a deny payload, and hook_is_deny checks for exactly that
# rather than for "some output" — a stray print or an import banner must not be re-emitted to the
# host as a decision, nor log a gate hit that never happened. That check is what lets the ADR 0080
# telemetry live out here in one shared function instead of a per-hook copy inside the body.
out=$(python3 <<'PYEOF' 2>/dev/null
import json, os, re, sys
try:
    d = json.loads(os.environ["BSG_INPUT"])
    ti = d.get("tool_input") or {}
    fp = os.environ.get("BSG_FP") or ti.get("file_path") or ""
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
        # Dated incident anecdotes inside live instructions: "a mining pass on 26-Jul found...",
        # "a run on 2026-07-12 showed...". A rule that has to cite the day it was learned is
        # telling you its history, not its content. Found in the repo's own retrospect skill by an
        # audit lane AFTER this guard shipped without covering it.
        r"\b(on|in) \d{1,2}-[A-Z][a-z]{2}\b[^.\n]{0,60}\b(found|showed|caught|revealed|hit)\b",
        r"\b(on|in) 20\d\d-\d\d-\d\d\b[^.\n]{0,60}\b(found|showed|caught|revealed|hit)\b",
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

    phrase, line, snippet = hits[0]
    reason = (f"backstory-edit-guard: this edit adds git-tellable backstory to {fp} — "
              f'line {line} of the added text says "{phrase}"'
              + (f' in: "{snippet}"' if snippet else "")
              + ". Git already records what this document used to say, so restating it here is "
                "duplication with a decay date (CLAUDE.md 'git-tellable backstory'; rules: "
                "ssot-enforcement.md). Delete the narration and state only what is true NOW. If "
                "the history is genuinely load-bearing for a reader, it belongs in the commit "
                "message or an ADR Justification, not in the prose.")
    # The marker says "this is a decision" explicitly; hook_is_deny tests for it rather than
    # guessing from the JSON's shape. One home for the byte: hook-lib.sh.
    sys.stdout.write(os.environ["HOOK_DENY_MARK"] + json.dumps(
        {"hookSpecificOutput": {"hookEventName": "PreToolUse",
         "permissionDecision": "deny", "permissionDecisionReason": reason}}))
except Exception:
    sys.exit(0)  # fail open
PYEOF
)
# No `|| out=""`: a body that printed a decision and THEN died has still decided, and the marker
# is what separates that from noise. Both PreToolUse guards read this identically, so neither can
# quietly become the lenient one.
if hook_is_deny "$out"; then
  hook_gate_hit backstory-edit-guard "$BSG_FP"
  printf '%s\n' "$(hook_deny_payload "$out")"
fi
exit 0
