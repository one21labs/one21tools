#!/usr/bin/env bash
# Decision-logic test for the sibling spawn-log.sh (CI runs every hooks/test-*.sh via
# .github/workflows/gates.yml). Runnable on git-bash:
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

# All marker-present fixtures pre-create docs/pdca: it is the ADR 0071 adoption marker the hook
# requires and never creates itself.

# Cases 1-6: each panel/loop primitive fires, bare and prefixed (retrospect: ADR 0081).
for skill in advise red-team verify retrospect pdca-workflow:advise pdca-workflow:retrospect; do
  FIX=$(mktemp -d)
  mkdir -p "$FIX/docs/pdca"
  res=$(fire "$FIX" "{\"tool_name\":\"Skill\",\"tool_input\":{\"skill\":\"$skill\",\"args\":\"\"}}")
  code=${res%%|*}; out=${res#*|}
  n=$( [ -f "$FIX/$LOG_REL" ] && grep -c " skill-spawn $skill\$" "$FIX/$LOG_REL" || echo 0 )
  [ "$code" = "0" ] && [ "$n" = "1" ] && ! printf '%s' "$out" | grep -q permissionDecision
  check "$skill -> exit 0, one log line, no deny" $? "code=$code lines=$n out=[$out]"
  rm -rf "$FIX"
done

# Case 5: another skill does NOT log.
FIX=$(mktemp -d)
mkdir -p "$FIX/docs/pdca"
res=$(fire "$FIX" '{"tool_name":"Skill","tool_input":{"skill":"dataviz"}}')
code=${res%%|*}
[ "$code" = "0" ] && [ ! -f "$FIX/$LOG_REL" ]
check "other skill (dataviz) -> exit 0, no log file created" $? "code=$code"
rm -rf "$FIX"

# Case 6: a skill whose name merely CONTAINS a primitive does not log (exact-match case arms).
FIX=$(mktemp -d)
mkdir -p "$FIX/docs/pdca"
res=$(fire "$FIX" '{"tool_name":"Skill","tool_input":{"skill":"security-review-verify-extra"}}')
code=${res%%|*}
[ "$code" = "0" ] && [ ! -f "$FIX/$LOG_REL" ]
check "superstring skill name -> no log (exact match only)" $? "code=$code"
rm -rf "$FIX"

# Case 7: missing skill field -> fails open, no log.
FIX=$(mktemp -d)
mkdir -p "$FIX/docs/pdca"
res=$(fire "$FIX" '{"tool_name":"Skill","tool_input":{"args":"x"}}')
code=${res%%|*}
[ "$code" = "0" ] && [ ! -f "$FIX/$LOG_REL" ]
check "missing skill field -> fails open, exit 0, no log" $? "code=$code"
rm -rf "$FIX"

# Case 8: malformed/empty stdin -> fails open.
FIX=$(mktemp -d)
mkdir -p "$FIX/docs/pdca"
out=$(printf '' | CLAUDE_PROJECT_DIR="$FIX" bash "$HOOK"); code=$?
[ "$code" = "0" ] && [ ! -f "$FIX/$LOG_REL" ]
check "malformed/empty stdin -> fails open, exit 0, no log" $? "code=$code"
rm -rf "$FIX"

# Case 9: log line FORMAT -- ISO-8601 UTC date, literal event tag, skill name, nothing else.
FIX=$(mktemp -d)
mkdir -p "$FIX/docs/pdca"
fire "$FIX" '{"tool_name":"Skill","tool_input":{"skill":"red-team"}}' >/dev/null
grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z skill-spawn red-team$' "$FIX/$LOG_REL"
check "log line format: ISO-8601Z + skill-spawn + name" $? "content=[$(cat "$FIX/$LOG_REL" 2>/dev/null)]"
rm -rf "$FIX"

# Case 10: repeat fires APPEND (one line per fire, no truncation).
FIX=$(mktemp -d)
mkdir -p "$FIX/docs/pdca"
fire "$FIX" '{"tool_name":"Skill","tool_input":{"skill":"advise"}}' >/dev/null
fire "$FIX" '{"tool_name":"Skill","tool_input":{"skill":"verify"}}' >/dev/null
n=$(grep -c ' skill-spawn ' "$FIX/$LOG_REL")
[ "$n" = "2" ]
check "two fires -> two appended lines" $? "lines=$n"
rm -rf "$FIX"

# Case 11 (ADR 0071 firing scope): primitive fires in a project WITHOUT the docs/pdca marker ->
# exit 0, no log, and the hook must NOT create the marker dir itself.
FIX=$(mktemp -d)
res=$(fire "$FIX" '{"tool_name":"Skill","tool_input":{"skill":"advise"}}')
code=${res%%|*}
[ "$code" = "0" ] && [ ! -d "$FIX/docs/pdca" ]
check "no docs/pdca marker -> exit 0, no log, dir NOT created" $? "code=$code"
rm -rf "$FIX"

# Cases 12-13 (ADR 0086 / #276 Agent|Task surface): a plugin-owned agent spawn logs one
# agent-spawn line, via either tool name the matcher covers.
for tool in Agent Task; do
  FIX=$(mktemp -d)
  mkdir -p "$FIX/docs/pdca"
  res=$(fire "$FIX" "{\"tool_name\":\"$tool\",\"tool_input\":{\"subagent_type\":\"pdca-workflow:retrospect\",\"prompt\":\"go\"}}")
  code=${res%%|*}; out=${res#*|}
  n=$( [ -f "$FIX/$LOG_REL" ] && grep -cE '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z agent-spawn pdca-workflow:retrospect$' "$FIX/$LOG_REL" || echo 0 )
  [ "$code" = "0" ] && [ "$n" = "1" ] && ! printf '%s' "$out" | grep -q permissionDecision
  check "$tool pdca-workflow:retrospect -> exit 0, one agent-spawn line, no deny" $? "code=$code lines=$n out=[$out]"
  rm -rf "$FIX"
done

# Case 14: a non-plugin agent (general-purpose) does NOT log.
FIX=$(mktemp -d)
mkdir -p "$FIX/docs/pdca"
res=$(fire "$FIX" '{"tool_name":"Agent","tool_input":{"subagent_type":"general-purpose","prompt":"x"}}')
code=${res%%|*}
[ "$code" = "0" ] && [ ! -f "$FIX/$LOG_REL" ]
check "non-plugin agent (general-purpose) -> exit 0, no log" $? "code=$code"
rm -rf "$FIX"

# Case 15: Agent input with NO subagent_type -> fails open, no log.
FIX=$(mktemp -d)
mkdir -p "$FIX/docs/pdca"
res=$(fire "$FIX" '{"tool_name":"Agent","tool_input":{"prompt":"x"}}')
code=${res%%|*}
[ "$code" = "0" ] && [ ! -f "$FIX/$LOG_REL" ]
check "Agent without subagent_type -> fails open, no log" $? "code=$code"
rm -rf "$FIX"

# Case 16: a literal "subagent_type" phrase inside the prompt VALUE is JSON-escaped and must
# not be read as the key -- the real key wins (explicit-model-guard.sh safety argument).
FIX=$(mktemp -d)
mkdir -p "$FIX/docs/pdca"
res=$(fire "$FIX" '{"tool_name":"Agent","tool_input":{"prompt":"say \"subagent_type\":\"evil\" aloud","subagent_type":"pdca-workflow:verifier"}}')
code=${res%%|*}
n=$( [ -f "$FIX/$LOG_REL" ] && grep -c ' agent-spawn pdca-workflow:verifier$' "$FIX/$LOG_REL" || echo 0 )
[ "$code" = "0" ] && [ "$n" = "1" ] && ! grep -q evil "$FIX/$LOG_REL"
check "escaped subagent_type in prompt value -> real key logged, not the decoy" $? "code=$code lines=$n content=[$(cat "$FIX/$LOG_REL" 2>/dev/null)]"
rm -rf "$FIX"

# Case 17: Skill tool input is untouched by the Agent branch (regression guard on the
# tool_name dispatch): a Skill fire still logs skill-spawn, never agent-spawn.
FIX=$(mktemp -d)
mkdir -p "$FIX/docs/pdca"
fire "$FIX" '{"tool_name":"Skill","tool_input":{"skill":"verify"}}' >/dev/null
grep -q ' skill-spawn verify$' "$FIX/$LOG_REL" && ! grep -q ' agent-spawn ' "$FIX/$LOG_REL"
check "Skill fire logs skill-spawn only (dispatch regression)" $? "content=[$(cat "$FIX/$LOG_REL" 2>/dev/null)]"
rm -rf "$FIX"

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
