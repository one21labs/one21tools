#!/usr/bin/env bash
# Decision-logic test for budget-edit-guard.sh (CLAUDE.md Never rule). Runnable:
# `bash test-budget-edit-guard.sh`. Uses a mktemp fixture + BUDGET_GUARD_CAPS_JSON override —
# never the real repo files, no node needed. Asserts deny JSON on over-cap, silence otherwise.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/budget-edit-guard.sh"
export BUDGET_GUARD_CAPS_JSON='{"doc":100,"adr":100,"lite":40,"agent":60}'
pass=0; fail=0

check() {
  if [ "$2" = "0" ]; then pass=$((pass+1)); printf 'PASS: %s\n' "$1"
  else fail=$((fail+1)); printf 'FAIL: %s %s\n' "$1" "${3:-}"; fi
}

payload() {  # $1 tool, $2 file, $3.. fields already JSON-encoded pairs
  python3 - "$@" <<'PY'
import json, sys
tool, fp = sys.argv[1], sys.argv[2]
ti = {"file_path": fp}
for kv in sys.argv[3:]:
    k, v = kv.split("=", 1)
    ti[k] = v
print(json.dumps({"tool_name": tool, "tool_input": ti}))
PY
}

FIX=$(mktemp -d)
export CLAUDE_PROJECT_DIR="$FIX"
mkdir -p "$FIX/docs/decisions" "$FIX/pdca-workflow/agents"

# 1. Write over the doc cap -> deny with reason
big=$(python3 -c "print('x'*150)")
out=$(payload Write "$FIX/CLAUDE.md" "content=$big" | bash "$HOOK")
printf '%s' "$out" | grep -q '"permissionDecision": "deny"'; check "over-cap Write denied" $?
printf '%s' "$out" | grep -q 'headroom'; check "deny reason carries headroom math" $?

# 2. Under-cap Write -> silent allow
out=$(payload Write "$FIX/CLAUDE.md" "content=short enough" | bash "$HOOK")
[ -z "$out" ]; check "under-cap Write silent" $?

# 3. Edit that pushes an existing file over -> deny
python3 -c "open('$FIX/CLAUDE.md','w').write('a'*95)"
out=$(payload Edit "$FIX/CLAUDE.md" "old_string=aaaaa" "new_string=$big" | bash "$HOOK")
printf '%s' "$out" | grep -q '"permissionDecision": "deny"'; check "over-cap Edit denied" $?

# 4. Edit that SHRINKS an over-cap file -> allowed (never trap a fix)
python3 -c "open('$FIX/CLAUDE.md','w').write('b'*150)"
out=$(payload Edit "$FIX/CLAUDE.md" "old_string=bbbbbbbbbb" "new_string=b" | bash "$HOOK")
[ -z "$out" ]; check "shrinking edit allowed" $?

# 5. Lite ADR gets the lite cap
lite=$(python3 -c "print('tier: lite\n' + 'y'*80)")
out=$(payload Write "$FIX/docs/decisions/0099-x.md" "content=$lite" | bash "$HOOK")
printf '%s' "$out" | grep -q 'deny'; check "lite ADR held to lite cap" $?

# 6. Full ADR under adr cap allowed
out=$(payload Write "$FIX/docs/decisions/0099-x.md" "content=normal adr text" | bash "$HOOK")
[ -z "$out" ]; check "full ADR under cap silent" $?

# 7. Non-budgeted file -> silent, fast bail
out=$(payload Write "$FIX/notes.md" "content=$big" | bash "$HOOK")
[ -z "$out" ]; check "non-budgeted file ignored" $?

# 8. Malformed stdin -> fail open
out=$(printf 'not json' | bash "$HOOK")
[ -z "$out" ]; check "malformed stdin fails open" $?

# 9. Agent file over agent cap -> deny
big70=$(python3 -c "print('z'*70)")
out=$(payload Write "$FIX/pdca-workflow/agents/pm.md" "content=$big70" | bash "$HOOK")
printf '%s' "$out" | grep -q 'deny'; check "agent file held to agent cap" $?

# 10-13. Gate-hit telemetry (ADR 0080): marker-gated, one line per deny, none on pass
[ ! -e "$FIX/docs/pdca/gate-hits.txt" ]; check "no docs/pdca marker: denies above logged nothing" $?
mkdir -p "$FIX/docs/pdca"
python3 -c "open('$FIX/CLAUDE.md','w').write('small')"
out=$(payload Write "$FIX/CLAUDE.md" "content=$big" | bash "$HOOK")
printf '%s' "$out" | grep -q '"permissionDecision": "deny"'; check "deny unchanged with marker present" $?
[ "$(grep -c 'gate-hit budget-edit-guard' "$FIX/docs/pdca/gate-hits.txt" 2>/dev/null)" = "1" ]; check "deny appended exactly one gate-hit line" $?
out=$(payload Write "$FIX/CLAUDE.md" "content=fine" | bash "$HOOK")
[ "$(grep -c 'gate-hit' "$FIX/docs/pdca/gate-hits.txt" 2>/dev/null)" = "1" ]; check "pass appended nothing" $?

rm -rf "$FIX"
printf '%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" = "0" ]
