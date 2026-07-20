#!/usr/bin/env bash
# SessionEnd hook for THIS REPO's .claude/settings.json (ADR 0081): append one line —
# `<ISO-8601 UTC> session-end <reason>` — to docs/pdca/session-log.txt so every session
# BOUNDARY is a recorded, countable event. This is the exposure denominator of ADR 0081 (d)'s
# closeout metric, and it converts a SKIPPED session-close retrospect from an invisible
# non-event into a mechanical miss (a session-end with no prior `skill-spawn` retrospect line
# in the same window) — the red-team BREAK-1 fix: a hook cannot spawn the retrospect, but it
# can make the skip observable.
#
# Same observability contract as the plugin's spawn-log.sh (whose header owns the log-location
# doctrine): pure observability, ALWAYS exits 0, never blocks; docs/pdca marker-guarded (ADR
# 0071) and never mkdir (ADR 0050); single-line `>>` append (atomicity per that header);
# stderr-silenced brace group so even a redirection-open failure leaks nothing (ADR 0080
# pattern). A missing/malformed reason logs `unknown` — one harmless line beats a lost
# boundary; the line format's consumers read fields, never positions (ADR 0077).
input=$(cat)
reason=$(printf '%s' "$input" | sed -n 's/.*"reason"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
root="${CLAUDE_PROJECT_DIR:-.}"
[ -d "$root/docs/pdca" ] || exit 0
{ printf '%s session-end %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${reason:-unknown}" >> "$root/docs/pdca/session-log.txt"; } 2>/dev/null
exit 0
