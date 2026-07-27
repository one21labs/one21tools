#!/usr/bin/env bash
# Decision-logic tests for destructive-git-guard.sh (CI: gates.yml runs .claude/hooks/test-*.sh).
#
# The load-bearing property is a PAIR, and both halves matter equally: it must deny when the tree
# holds work that would be lost, and it must NOT deny when it does not. A guard that denies a clean
# `git reset --hard` is a guard people learn to route around, and a routed-around guard protects
# nothing.
set -u
HOOK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/destructive-git-guard.sh"
pass=0; fail=0

fixture() {  # $1 = dirty|clean -> echoes a repo path
  d=$(mktemp -d)
  git -C "$d" init -q .
  git -C "$d" -c user.email=t@t -c user.name=t commit -q --allow-empty -m base
  [ "$1" = "dirty" ] && printf 'uncommitted work\n' > "$d/wip.txt"
  printf '%s' "$d"
}

check() {  # $1 = label, $2 = repo, $3 = command, $4 = deny|allow
  out=$(printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$3" \
    | CLAUDE_PROJECT_DIR="$2" bash "$HOOK" 2>/dev/null)
  got=allow; printf '%s' "$out" | grep -q '"permissionDecision":"deny"' && got=deny
  if [ "$got" = "$4" ]; then pass=$((pass+1)); printf 'PASS: %s\n' "$1"
  else fail=$((fail+1)); printf 'FAIL: %s (expected %s, got %s)\n' "$1" "$4" "$got"; fi
}

DIRTY=$(fixture dirty)
CLEAN=$(fixture clean)

# --- Denies: the tree holds work these would silently take. ---
check "reset --hard on a dirty tree" "$DIRTY" "git reset --hard HEAD~1" deny
check "clean -fd on a dirty tree (untracked files are exactly what it deletes)" "$DIRTY" "git clean -fd" deny
check "checkout -f on a dirty tree" "$DIRTY" "git checkout -f" deny
check "stash drop on a dirty tree" "$DIRTY" "git stash drop" deny
check "reset --merge on a dirty tree" "$DIRTY" "git reset --merge HEAD~1" deny
check "chained after another command still counts" "$DIRTY" "cd x && git reset --hard HEAD~1" deny

# --- Allows: the SAFE alternatives the deny message names. If these were denied the guard would
# be telling the operator to run something it also blocks, which is how a guard gets disabled. ---
check "reset --soft keeps everything, must be allowed" "$DIRTY" "git reset --soft HEAD~1" allow
check "plain reset keeps the worktree, must be allowed" "$DIRTY" "git reset HEAD~1" allow
check "status is never destructive" "$DIRTY" "git status" allow
check "commit is the opposite of destructive" "$DIRTY" "git commit -m x" allow
check "stash push SAVES work" "$DIRTY" "git stash push -m wip" allow

# --- Allows on a CLEAN tree: nothing uncommitted means nothing to lose. The commits themselves
# remain in the reflog, so this is not the loss the guard is about. ---
check "reset --hard on a clean tree" "$CLEAN" "git reset --hard HEAD~1" allow
check "clean -fd on a clean tree" "$CLEAN" "git clean -fd" allow

# --- Not an invocation: the word appearing inside a quoted argument must not fire. ---
check "a mention inside a grep pattern is not an invocation" "$DIRTY" "grep -r 'git reset --hard' docs" allow

# --- The deny must PRESCRIBE, not just refuse (house standard): it names the safe alternative. ---
out=$(printf '{"tool_name":"Bash","tool_input":{"command":"git reset --hard HEAD~1"}}' \
  | CLAUDE_PROJECT_DIR="$DIRTY" bash "$HOOK" 2>/dev/null)
if printf '%s' "$out" | grep -q 'reset --soft'; then pass=$((pass+1)); printf 'PASS: %s\n' "the deny names the non-destructive alternative"
else fail=$((fail+1)); printf 'FAIL: %s\n' "the deny names the non-destructive alternative"; fi
if printf '%s' "$out" | grep -q 'wip.txt'; then pass=$((pass+1)); printf 'PASS: %s\n' "the deny names what would actually be lost"
else fail=$((fail+1)); printf 'FAIL: %s\n' "the deny names what would actually be lost"; fi

# --- Fails OPEN on absent machinery, like every sibling guard: an unreadable project dir must not
# become a blanket block on git. ---
check "nonexistent project dir -> cannot know -> allow" "/no/such/dir-xyz" "git reset --hard HEAD~1" allow

rm -rf "$DIRTY" "$CLEAN"
printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
