#!/usr/bin/env bash
# Decision-logic test for plugin-hooks/spawn-log.sh. Runnable on git-bash:
# `bash test-spawn-log.sh`. Uses a mktemp CLAUDE_PROJECT_DIR fixture -- never the real repo --
# and asserts on exit code, the ABSENCE of any deny output, and the log file's content/format.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/spawn-log.sh"
pass=0; fail=0

check() {
  name="$1"; ok="$2"; extra="${3:-}"
  if [ "$ok" = "0" ]; then pass=$((pass+1)); printf 'PASS: %s\n' "$name"
  else fail=$((fail+1)); printf 'FAIL: %s %s\n' "$name" "$extra"; fi
}

fire() {
  # $1 = project dir, $2 = raw stdin. Echoes "exitcode|stdout".
  out=$(printf '%s' "$2" | CLAUDE_PROJECT_DIR="$1" bash "$HOOK"); code=$?
  printf '%s|%s' "$code" "$out"
}

LOG_REL="docs/pdca/session-log.txt"

# Cases 1-4: each panel primitive fires, bare and prefixed.
for skill in advise red-team verify pdca-workflow:advise; do
  FIX=$(mktemp -d)
  res=$(fire "$FIX" "{\"tool_name\":\"Skill\",\"tool_input\":{\"skill\":\"$skill\",\"args\":\"\"}}")
  code=${res%%|*}; out=${res#*|}
  n=$( [ -f "$FIX/$LOG_REL" ] && grep -c " skill-spawn $skill\$" "$FIX/$LOG_REL" || echo 0 )
  [ "$code" = "0" ] && [ "$n" = "1" ] && ! printf '%s' "$out" | grep -q permissionDecision
  check "$skill -> exit 0, one log line, no deny" $? "code=$code lines=$n out=[$out]"
  rm -rf "$FIX"
done

# Case 5: another skill does NOT log.
FIX=$(mktemp -d)
res=$(fire "$FIX" '{"tool_name":"Skill","tool_input":{"skill":"dataviz"}}')
code=${res%%|*}
[ "$code" = "0" ] && [ ! -f "$FIX/$LOG_REL" ]
check "other skill (dataviz) -> exit 0, no log file created" $? "code=$code"
rm -rf "$FIX"

# Case 6: a skill whose name merely CONTAINS a primitive does not log (exact-match case arms).
FIX=$(mktemp -d)
res=$(fire "$FIX" '{"tool_name":"Skill","tool_input":{"skill":"security-review-verify-extra"}}')
code=${res%%|*}
[ "$code" = "0" ] && [ ! -f "$FIX/$LOG_REL" ]
check "superstring skill name -> no log (exact match only)" $? "code=$code"
rm -rf "$FIX"

# Case 7: missing skill field -> fails open, no log.
FIX=$(mktemp -d)
res=$(fire "$FIX" '{"tool_name":"Skill","tool_input":{"args":"x"}}')
code=${res%%|*}
[ "$code" = "0" ] && [ ! -f "$FIX/$LOG_REL" ]
check "missing skill field -> fails open, exit 0, no log" $? "code=$code"
rm -rf "$FIX"

# Case 8: malformed/empty stdin -> fails open.
FIX=$(mktemp -d)
out=$(printf '' | CLAUDE_PROJECT_DIR="$FIX" bash "$HOOK"); code=$?
[ "$code" = "0" ] && [ ! -f "$FIX/$LOG_REL" ]
check "malformed/empty stdin -> fails open, exit 0, no log" $? "code=$code"
rm -rf "$FIX"

# Case 9: log line FORMAT -- ISO-8601 UTC date, literal event tag, skill name, nothing else.
FIX=$(mktemp -d)
fire "$FIX" '{"tool_name":"Skill","tool_input":{"skill":"red-team"}}' >/dev/null
grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z skill-spawn red-team$' "$FIX/$LOG_REL"
check "log line format: ISO-8601Z + skill-spawn + name" $? "content=[$(cat "$FIX/$LOG_REL" 2>/dev/null)]"
rm -rf "$FIX"

# Case 10: repeat fires APPEND (one line per fire, no truncation), and the dir is auto-created
# fresh each session (mkdir -p covered implicitly by every case above starting dir-less).
FIX=$(mktemp -d)
fire "$FIX" '{"tool_name":"Skill","tool_input":{"skill":"advise"}}' >/dev/null
fire "$FIX" '{"tool_name":"Skill","tool_input":{"skill":"verify"}}' >/dev/null
n=$(grep -c ' skill-spawn ' "$FIX/$LOG_REL")
[ "$n" = "2" ]
check "two fires -> two appended lines" $? "lines=$n"
rm -rf "$FIX"

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
