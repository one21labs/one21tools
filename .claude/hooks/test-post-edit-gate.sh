#!/usr/bin/env bash
# Decision-logic test for post-edit-gate.sh. Runnable on git-bash:
# `bash test-post-edit-gate.sh`. Uses the REAL repo as CLAUDE_PROJECT_DIR so the routing
# exercises the genuine scripts and a genuine skill/benchmark fixture, not stubs. The gate
# scripts under test only read files, but the hook itself WRITES gate-hit telemetry (ADR 0080)
# whenever a routed gate genuinely fails mid-suite -- so the real repo's log is snapshotted
# before the real-repo cases and restored on exit (#256; the pre-0080 "writes nothing" premise
# no longer holds). The repo root is derived from this script's own location (two dirs up), so
# the suite runs everywhere the repo is checked out, CI included; SKIPs (exit 0) only if that
# derivation doesn't land in a repo checkout.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/post-edit-gate.sh"
REPO="$(cd "$HERE/../.." && pwd)"
[ -f "$REPO/scripts/check-restatement.mjs" ] || { echo "SKIP: repo root not found at $REPO"; exit 0; }

# Snapshot the real telemetry log around the whole suite (restore even on mid-run kill).
GHLOG="$REPO/docs/pdca/gate-hits.txt"
GHSNAP=""; FIX=""
[ -f "$GHLOG" ] && { GHSNAP=$(mktemp); cp "$GHLOG" "$GHSNAP"; }
cleanup() {
  if [ -n "$GHSNAP" ]; then cp "$GHSNAP" "$GHLOG"; rm -f "$GHSNAP"
  elif [ -f "$GHLOG" ]; then rm -f "$GHLOG"; fi
  [ -n "$FIX" ] && rm -rf "$FIX"
}
trap cleanup EXIT

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

# --- Plugin-scoped skills (#256): the derivation must preserve the plugin prefix so the dir
# guard resolves; the old bare `skills/<name>` capture silently skipped these. ---
# A real, currently-passing plugin skill routes and passes.
code=$(run "$REPO/pdca-workflow/skills/retrospect/SKILL.md")
assert_exit "pdca-workflow/skills/* edit -> prefix preserved, validate.py passes -> exit 0" 0 "$code"

# Nonexistent plugin-scoped skill dir -> the dir guard still skips.
code=$(run "$REPO/pdca-workflow/skills/nonexistent-skill-xyz/SKILL.md")
assert_exit "pdca-workflow/skills/<nonexistent> -> dir guard skips gate -> exit 0" 0 "$code"

# --- Gate-hit telemetry (ADR 0080): failure path, exercised in a mktemp fixture whose routed
# gate script does not exist (node fails -> run_gate's failure branch), never the real repo. ---
FIX=$(mktemp -d)
json=$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$FIX/README.md")
code=$(printf '%s' "$json" | CLAUDE_PROJECT_DIR="$FIX" bash "$HOOK" 2>/dev/null; echo $?)
assert_exit "fixture README edit, gate script missing -> failure path -> exit 2" 2 "$code"
if [ ! -e "$FIX/docs/pdca/gate-hits.txt" ]; then pass=$((pass+1)); printf 'PASS: %s\n' "no docs/pdca marker: failure logged nothing"
else fail=$((fail+1)); printf 'FAIL: %s\n' "no docs/pdca marker: failure logged nothing"; fi
mkdir -p "$FIX/docs/pdca"
code=$(printf '%s' "$json" | CLAUDE_PROJECT_DIR="$FIX" bash "$HOOK" 2>/dev/null; echo $?)
assert_exit "fixture failure with marker present -> still exit 2" 2 "$code"
if [ "$(grep -c 'gate-hit check-restatement.mjs' "$FIX/docs/pdca/gate-hits.txt" 2>/dev/null)" = "1" ]; then
  pass=$((pass+1)); printf 'PASS: %s\n' "failure appended exactly one gate-hit line naming the gate"
else fail=$((fail+1)); printf 'FAIL: %s log=[%s]\n' "failure appended exactly one gate-hit line naming the gate" "$(cat "$FIX/docs/pdca/gate-hits.txt" 2>/dev/null)"; fi

# A FAILING plugin-scoped skill, real validate.py copied into the fixture: exit 2 proves the
# gate actually RAN for a prefixed path. Under the stripped-prefix bug this silently skipped
# and exited 0 -- indistinguishable from a pass in the real-repo case above, so only a failing
# skill can pin the regression.
mkdir -p "$FIX/skills/building-skills/scripts" "$FIX/pdca-workflow/skills/badskill"
cp "$REPO/skills/building-skills/scripts/validate.py" "$FIX/skills/building-skills/scripts/"
printf 'no frontmatter at all\n' > "$FIX/pdca-workflow/skills/badskill/SKILL.md"
json=$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$FIX/pdca-workflow/skills/badskill/SKILL.md")
code=$(printf '%s' "$json" | CLAUDE_PROJECT_DIR="$FIX" bash "$HOOK" 2>/dev/null; echo $?)
assert_exit "fixture failing plugin skill -> validate.py runs via preserved prefix -> exit 2" 2 "$code"

# Same failing skill with CLAUDE_PROJECT_DIR UNSET and cwd = fixture root: root falls back to
# "." so the root-prefix strip misses the absolute fp; the $PWD fallback must rescue the
# derivation or the gate silently skips (muda-review finding on this PR).
code=$(cd "$FIX" && printf '%s' "$json" | env -u CLAUDE_PROJECT_DIR bash "$HOOK" 2>/dev/null; echo $?)
assert_exit "unset CLAUDE_PROJECT_DIR, cwd=root -> \$PWD fallback still routes -> exit 2" 2 "$code"

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
