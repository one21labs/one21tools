#!/usr/bin/env bash
# Decision-logic test for repo-hooks/three-dot-warn.sh. Runnable on git-bash:
# `bash test-three-dot-warn.sh`. Uses a mktemp CLAUDE_PROJECT_DIR fixture -- never the real
# repo -- and asserts on the additionalContext output, the appended log line, and exit codes.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/three-dot-warn.sh"
pass=0; fail=0
LOG_REL="docs/pdca/session-log.txt"

check() {
  name="$1"; ok="$2"; extra="${3:-}"
  if [ "$ok" = "0" ]; then pass=$((pass+1)); printf 'PASS: %s\n' "$name"
  else fail=$((fail+1)); printf 'FAIL: %s %s\n' "$name" "$extra"; fi
}

# $1 = name, $2 = command, $3 = "warn" or "silent"
run_case() {
  name="$1"; cmd="$2"; expect="$3"
  FIX=$(mktemp -d)
  json=$(printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$cmd")
  out=$(printf '%s' "$json" | CLAUDE_PROJECT_DIR="$FIX" bash "$HOOK"); code=$?
  if printf '%s' "$out" | grep -q '"additionalContext"'; then got=warn; else got=silent; fi
  logged=$( [ -f "$FIX/$LOG_REL" ] && grep -c ' two-dot-main ' "$FIX/$LOG_REL" || echo 0 )
  want_logged=0; [ "$expect" = "warn" ] && want_logged=1
  # A warn must never be a deny, and exit is always 0.
  [ "$code" = "0" ] && [ "$got" = "$expect" ] && [ "$logged" = "$want_logged" ] \
    && ! printf '%s' "$out" | grep -q permissionDecision
  check "$name" $? "(expected $expect/logged=$want_logged, got $got/logged=$logged, exit=$code) cmd=[$cmd]"
  rm -rf "$FIX"
}

# Two-dot-against-main variants: fire.
run_case "warn: git log main..feature"               'git log main..feature'                          warn
run_case "warn: git diff origin/main..HEAD"          'git diff origin/main..HEAD'                     warn
run_case "warn: git rev-list --count main..HEAD"     'git rev-list --count main..HEAD'                warn
run_case "warn: chained cd && git log main..x"       'cd /some/dir && git log --oneline main..x'      warn

# The fix itself: three-dot never fires.
run_case "silent: git log origin/main...branch"      'git log origin/main...branch'                   silent
run_case "silent: git diff main...HEAD"              'git diff main...HEAD'                           silent

# Ranges not involving main: never fire.
run_case "silent: git log a..b (non-main)"           'git log a..b'                                   silent
run_case "silent: git diff feature..other"           'git diff feature..other'                        silent
run_case "silent: notmain..x (boundary guard)"       'git log notmain..x'                             silent
run_case "silent: upstream/main..x (accepted limitation, doc'd)" 'git log upstream/main..x'           silent

# git without a range subcommand: never fires.
run_case "silent: git checkout main"                 'git checkout main'                              silent
run_case "silent: non-git command mentioning range"  'cat notes-main..txt'                            silent

# Quoted mention: the [^"]* extraction ends at the first escaped quote, so the phrase inside
# quotes is never seen (documented accepted limitation -- a miss, never a false fire).
run_case "silent: echo \\\"main..x\\\" quoted mention" 'echo \"main..x\"'                             silent

# Malformed/empty stdin fails open.
FIX=$(mktemp -d)
out=$(printf '' | CLAUDE_PROJECT_DIR="$FIX" bash "$HOOK"); code=$?
[ "$code" = "0" ] && [ -z "$out" ] && [ ! -f "$FIX/$LOG_REL" ]
check "silent: malformed/empty stdin fails open" $? "code=$code out=[$out]"
rm -rf "$FIX"

# Log line format on a fire: ISO-8601Z + two-dot-main + the matched range token.
FIX=$(mktemp -d)
printf '%s' '{"tool_name":"Bash","tool_input":{"command":"git log origin/main..HEAD"}}' \
  | CLAUDE_PROJECT_DIR="$FIX" bash "$HOOK" >/dev/null
grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z two-dot-main .*origin/main\.\.' "$FIX/$LOG_REL"
check "log line format: ISO-8601Z + two-dot-main + range token" $? "content=[$(cat "$FIX/$LOG_REL" 2>/dev/null)]"
rm -rf "$FIX"

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
