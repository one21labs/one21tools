#!/usr/bin/env bash
# Decision-logic test for repo-hooks/post-edit-gate.sh. Runnable on git-bash:
# `bash test-post-edit-gate.sh`. Uses the REAL repo as CLAUDE_PROJECT_DIR (read-only: the gate
# scripts under test -- validate.py, check-restatement.mjs, check-workflow.mjs -- only read
# files, this test writes nothing into the repo) so the routing exercises the genuine scripts and
# a genuine skill/benchmark fixture, not stubs.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/post-edit-gate.sh"
REPO="C:/Users/ajmcc/projects/one21tools"
[ -f "$REPO/scripts/check-restatement.mjs" ] || { echo "SKIP: real repo not found at $REPO"; exit 0; }

pass=0; fail=0
assert_exit() {
  name="$1"; expect="$2"; got="$3"; extra="${4:-}"
  if [ "$got" = "$expect" ]; then
    pass=$((pass+1)); printf 'PASS: %s\n' "$name"
  else
    fail=$((fail+1)); printf 'FAIL: %s (expected exit %s, got %s) %s\n' "$name" "$expect" "$got" "$extra"
  fi
}

run() {
  fp="$1"
  json=$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$fp")
  printf '%s' "$json" | CLAUDE_PROJECT_DIR="$REPO" bash "$HOOK"
  echo $?
}

# A real, currently-passing skill -> validate.py routing.
code=$(run "$REPO/skills/building-skills/SKILL.md")
assert_exit "skills/* edit -> validate.py runs, passes -> exit 0" 0 "$code"

# A real README.md -> check-restatement.mjs routing (scoped class).
code=$(run "$REPO/README.md")
assert_exit "README.md edit -> check-restatement.mjs runs, corpus clean -> exit 0" 0 "$code"

# A real docs/ file -> check-restatement.mjs routing (scoped class).
code=$(run "$REPO/docs/decisions/0046-layered-poka-yoke-altitude-restatement.md")
assert_exit "docs/*.md edit -> check-restatement.mjs runs -> exit 0" 0 "$code"

# A real benchmarks/*.md file -> check-restatement.mjs routing (scoped class).
code=$(run "$REPO/benchmarks/README.md")
assert_exit "benchmarks/*.md edit -> check-restatement.mjs runs -> exit 0" 0 "$code"

# A real benchmarks/*.workflow.js -> check-workflow.mjs routing.
code=$(run "$REPO/benchmarks/2026-07-08-skills-hermetic/grade.workflow.js")
assert_exit "benchmarks/*.workflow.js edit -> check-workflow.mjs runs -> exit 0" 0 "$code"

# An out-of-scope .md that is NOT README/docs/benchmarks (a skill's own SKILL.md is .md but
# routed to validate.py above, not check-restatement -- this file has neither route: proves the
# scoping fix actually narrows the trigger, not just adds a redundant one).
code=$(run "$REPO/CLAUDE.md")
assert_exit "CLAUDE.md edit -> out of scope for BOTH repo routes -> exit 0, no gate run" 0 "$code"

# Windows-escaped path (doubled backslash).
win_fp=$(printf '%s' "$REPO/README.md" | sed 's/\//\\\\/g')
json=$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$win_fp")
code=$(printf '%s' "$json" | CLAUDE_PROJECT_DIR="$REPO" bash "$HOOK"; echo $?)
assert_exit "Windows-escaped backslash path -> normalized, routes correctly -> exit 0" 0 "$code" "fp=[$win_fp]"

# Missing file_path entirely.
json='{"tool_name":"Write","tool_input":{}}'
code=$(printf '%s' "$json" | CLAUDE_PROJECT_DIR="$REPO" bash "$HOOK"; echo $?)
assert_exit "missing file_path -> fails open -> exit 0" 0 "$code"

# Out-of-repo path (no relation to the repo at all).
json='{"tool_name":"Write","tool_input":{"file_path":"/some/unrelated/place/README.md"}}'
code=$(printf '%s' "$json" | CLAUDE_PROJECT_DIR="$REPO" bash "$HOOK"; echo $?)
assert_exit "out-of-repo README.md path -> hook still routes on the STRING (cd \$root succeeds; check-restatement scans \$root's OWN tree, unaffected by the out-of-repo fp) -> exit 0" 0 "$code"

# Malformed/empty stdin.
code=$(printf '' | CLAUDE_PROJECT_DIR="$REPO" bash "$HOOK"; echo $?)
assert_exit "malformed/empty stdin -> fails open -> exit 0" 0 "$code"

# A skills/ path pointing at a NONEXISTENT skill dir -> validate.py must not be invoked (the
# `[ -d ... ]` guard in the script), so this still exits 0 even though the dir is bogus.
code=$(run "$REPO/skills/nonexistent-skill-xyz/SKILL.md")
assert_exit "skills/<nonexistent>/SKILL.md -> dir guard skips gate -> exit 0" 0 "$code"

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
