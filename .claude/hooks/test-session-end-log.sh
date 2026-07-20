#!/usr/bin/env bash
# Decision-logic test for session-end-log.sh (CI runs every .claude/hooks/test-*.sh via
# .github/workflows/gates.yml). Runnable: `bash test-session-end-log.sh`. mktemp fixtures only —
# never the real repo.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/session-end-log.sh"
pass=0; fail=0
check() {
  if [ "$2" = "0" ]; then pass=$((pass+1)); printf 'PASS: %s\n' "$1"
  else fail=$((fail+1)); printf 'FAIL: %s %s\n' "$1" "${3:-}"; fi
}
LOG_REL="docs/pdca/session-log.txt"

# 1. Marker present -> exactly one line, ISO-8601Z + session-end + reason, exit 0.
FIX=$(mktemp -d)
mkdir -p "$FIX/docs/pdca"
printf '{"hook_event_name":"SessionEnd","reason":"clear"}' | CLAUDE_PROJECT_DIR="$FIX" bash "$HOOK"
code=$?
grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z session-end clear$' "$FIX/$LOG_REL" \
  && [ "$(grep -c ' session-end ' "$FIX/$LOG_REL")" = "1" ] && [ "$code" = "0" ]
check "marker present -> one formatted line, exit 0" $? "content=[$(cat "$FIX/$LOG_REL" 2>/dev/null)] code=$code"
rm -rf "$FIX"

# 2. No docs/pdca marker -> exit 0, nothing written, dir NOT created (ADR 0071).
FIX=$(mktemp -d)
printf '{"reason":"exit"}' | CLAUDE_PROJECT_DIR="$FIX" bash "$HOOK"
code=$?
[ "$code" = "0" ] && [ ! -d "$FIX/docs/pdca" ]
check "no marker -> exit 0, no log, dir not created" $? "code=$code"
rm -rf "$FIX"

# 3. Missing reason field / malformed stdin -> still logs a boundary with reason=unknown, exit 0.
FIX=$(mktemp -d)
mkdir -p "$FIX/docs/pdca"
printf 'not json' | CLAUDE_PROJECT_DIR="$FIX" bash "$HOOK"
code=$?
grep -qE ' session-end unknown$' "$FIX/$LOG_REL" && [ "$code" = "0" ]
check "malformed stdin -> boundary logged with reason=unknown, exit 0" $? "content=[$(cat "$FIX/$LOG_REL" 2>/dev/null)]"
rm -rf "$FIX"

# 4. Unwritable log (session-log.txt as a DIRECTORY) -> exit 0, no stderr leak (ADR 0080 pattern).
FIX=$(mktemp -d)
mkdir -p "$FIX/docs/pdca/session-log.txt"
err=$(printf '{"reason":"clear"}' | CLAUDE_PROJECT_DIR="$FIX" bash "$HOOK" 2>&1); code=$?
[ "$code" = "0" ] && [ -z "$err" ]
check "unwritable log -> exit 0, silent" $? "code=$code err=[$err]"
rm -rf "$FIX"

# 5. Two ends -> two appended lines (append-only, no truncation).
FIX=$(mktemp -d)
mkdir -p "$FIX/docs/pdca"
printf '{"reason":"clear"}' | CLAUDE_PROJECT_DIR="$FIX" bash "$HOOK"
printf '{"reason":"logout"}' | CLAUDE_PROJECT_DIR="$FIX" bash "$HOOK"
[ "$(grep -c ' session-end ' "$FIX/$LOG_REL")" = "2" ]
check "two ends -> two appended lines" $?
rm -rf "$FIX"

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
