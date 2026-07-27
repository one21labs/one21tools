#!/usr/bin/env bash
# Tests for destructive-git-guard.sh (CI: gates.yml runs .claude/hooks/test-*.sh).
#
# THE DECISION LOGIC IS TESTED IN PYTHON, next to the code that owns it: lib/destructive_git_test.py
# drives every parsing and predicate case against injected git state, which is the only way to test
# "did it ask the RIGHT worktree" -- a shell fixture can only ever be one tree. This file runs that
# suite and then checks the things only an end-to-end run can check: that the shim wires stdin,
# CLAUDE_PROJECT_DIR, and real git together, and that it fails open rather than closed when the
# machinery around it is missing.
#
# The previous version of this file asserted `git stash drop` on a dirty worktree should DENY.
# That was the product's bug written down as a requirement -- dropping a stash entry cannot touch
# the worktree -- so fixing the product correctly would have turned CI red. A cross-family review
# caught it. Encoding a defect as an expectation is the most expensive kind of test to have.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/destructive-git-guard.sh"
pass=0; fail=0

record() {  # $1 = label, $2 = ok|not
  if [ "$2" = ok ]; then pass=$((pass+1)); printf 'PASS: %s\n' "$1"
  else fail=$((fail+1)); printf 'FAIL: %s\n' "$1"; fi
}

# --- The decision logic, in its own home. ----------------------------------------------------
printf -- '--- lib/destructive_git_test.py ---\n'
if python3 "$HERE/lib/destructive_git_test.py"; then record "decision-logic suite" ok
else record "decision-logic suite" not; fi
printf -- '--- end-to-end shim ---\n'

fixture() {  # $1 = dirty|clean -> echoes a repo path
  d=$(mktemp -d)
  git -C "$d" init -q .
  git -C "$d" -c user.email=t@t -c user.name=t commit -q --allow-empty -m base
  [ "$1" = "dirty" ] && printf 'uncommitted work\n' > "$d/wip.txt"
  printf '%s' "$d"
}

run() {  # $1 = repo, $2 = command -> echoes deny|allow
  out=$(printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$2" \
    | CLAUDE_PROJECT_DIR="$1" bash "$HOOK" 2>/dev/null)
  # Whitespace-tolerant: the decider emits via json.dumps, whose default separators put a space
  # after the colon. Matching the compact form silently read every deny as an allow.
  if printf '%s' "$out" | grep -q '"permissionDecision"[[:space:]]*:[[:space:]]*"deny"'; then printf 'deny'
  else printf 'allow'; fi
}

check() {  # $1 = label, $2 = repo, $3 = command, $4 = expected
  got=$(run "$2" "$3")
  if [ "$got" = "$4" ]; then record "$1" ok
  else printf 'FAIL: %s (expected %s, got %s)\n' "$1" "$4" "$got"; fail=$((fail+1)); fi
}

DIRTY=$(fixture dirty)
CLEAN=$(fixture clean)

# The shim really reaches real git through a real dirty tree.
check "reset --hard on a dirty tree" "$DIRTY" "git reset --hard HEAD~1" deny
check "reset --hard on a clean tree" "$CLEAN" "git reset --hard HEAD~1" allow
check "reset --soft is the prescribed alternative and must never be blocked" "$DIRTY" "git reset --soft HEAD~1" allow
# The bypass that a cross-family review demonstrated against the bash-regex version, end to end.
check "sh -c re-exec reaches the decider" "$DIRTY" "sh -c 'git reset --hard'" deny

# The deny is built from the tree the shim actually read, not from a canned string.
out=$(printf '{"tool_name":"Bash","tool_input":{"command":"git reset --hard HEAD~1"}}' \
  | CLAUDE_PROJECT_DIR="$DIRTY" bash "$HOOK" 2>/dev/null)
printf '%s' "$out" | grep -q 'wip.txt' && record "the deny names the file it read from the tree" ok \
  || record "the deny names the file it read from the tree" not
printf '%s' "$out" | grep -q 'reset --soft' && record "the deny prescribes the safe alternative" ok \
  || record "the deny prescribes the safe alternative" not
python3 -c 'import json,sys; json.loads(sys.stdin.read())' <<< "$out" >/dev/null 2>&1 \
  && record "the emitted response is valid JSON even with a filename in it" ok \
  || record "the emitted response is valid JSON even with a filename in it" not

# --- Fails OPEN on absent machinery, like every sibling guard. An unreadable environment must
# not become a blanket block on git. (Absent INPUT is the opposite case and is covered in the
# python suite, where malformed JSON must NOT read as "nothing destructive here".) ------------
check "nonexistent project dir cannot be statted, so it allows" "/no/such/dir-xyz" "git reset --hard HEAD~1" allow
out=$(printf '{"tool_name":"Bash","tool_input":{"command":"git reset --hard"}}' \
  | CLAUDE_PROJECT_DIR="$DIRTY" PATH="/nonexistent" bash "$HOOK" 2>/dev/null)
[ -z "$out" ] && record "no python3 on PATH fails open" ok || record "no python3 on PATH fails open" not

# --- The floor: if the hook were stubbed to exit 0, every allow above would still pass. Only a
# deny can evidence the guard works, so assert at least one fired. ----------------------------
[ "$(run "$DIRTY" "git reset --hard HEAD~1")" = deny ] \
  && record "the hook is not a stub (a known-bad command really denies)" ok \
  || record "the hook is not a stub (a known-bad command really denies)" not

rm -rf "$DIRTY" "$CLEAN"
printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
