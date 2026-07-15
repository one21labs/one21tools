#!/usr/bin/env bash
# Decision-logic test for the sibling adr-lint-post-edit.sh (CI runs every hooks/test-*.sh via
# .github/workflows/gates.yml). Runnable on git-bash:
# `bash test-adr-lint-post-edit.sh`. Builds a synthetic consumer-project fixture under mktemp -d
# (never touches the real repo) and points CLAUDE_PLUGIN_ROOT at this repo's real
# pdca-workflow/ so the gate script under test is the genuine adr-lint.mjs, not a stub.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/adr-lint-post-edit.sh"
# The real pdca-workflow/ (fixed, known path in this environment) supplies the genuine
# adr-lint.mjs under test; CLAUDE_PROJECT_DIR below always points at a synthetic mktemp fixture,
# never at the real repo, so this test cannot mutate or depend on real repo state.
REAL_PLUGIN_ROOT="C:/Users/ajmcc/projects/one21tools/pdca-workflow"
[ -f "$REAL_PLUGIN_ROOT/scripts/adr-lint.mjs" ] || { echo "SKIP: real pdca-workflow/scripts/adr-lint.mjs not found at $REAL_PLUGIN_ROOT"; exit 0; }

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
  # $1 = CLAUDE_PROJECT_DIR, $2 = file_path (already forward-slashed or backslash-escaped for JSON), $3 = plugin_root
  proj="$1"; fp="$2"; proot="$3"
  json=$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$fp")
  printf '%s' "$json" | CLAUDE_PROJECT_DIR="$proj" CLAUDE_PLUGIN_ROOT="$proot" bash "$HOOK"
  echo $?
}

# --- Fixture A: consumer WITH a valid (lite) ADR corpus ---
FIX_OK=$(mktemp -d)
mkdir -p "$FIX_OK/docs/decisions" "$FIX_OK/.claude/agents"
cat > "$FIX_OK/docs/decisions/0001-good.md" <<'EOF'
---
id: "0001"
title: "Test fixture ADR"
status: accepted
summary: "A minimal valid lite ADR used only by the hook test fixture."
tier: lite
---
# 0001: Test fixture ADR

Decision: use a lite-tier ADR for hook-test fixtures. Enforced by this fixture file existing.
EOF
cat > "$FIX_OK/CLAUDE.md" <<'EOF'
# Fixture project
Trivially small, well under any char budget.
EOF

# --- Fixture B: consumer with an INVALID ADR (missing frontmatter) ---
FIX_BAD=$(mktemp -d)
mkdir -p "$FIX_BAD/docs/decisions"
printf '# 0001: no frontmatter at all\n\nThis ADR is missing its YAML frontmatter block.\n' > "$FIX_BAD/docs/decisions/0001-bad.md"

# --- Fixture C: consumer with NO docs/decisions dir at all (degrade gracefully) ---
FIX_NONE=$(mktemp -d)
mkdir -p "$FIX_NONE/.claude/agents"
printf '# CLAUDE.md\nno ADR corpus in this consumer project\n' > "$FIX_NONE/CLAUDE.md"

trap 'rm -rf "$FIX_OK" "$FIX_BAD" "$FIX_NONE"' EXIT

code=$(run "$FIX_OK" "$FIX_OK/docs/decisions/0001-good.md" "$REAL_PLUGIN_ROOT")
assert_exit "valid ADR edit -> gate passes -> exit 0" 0 "$code"

code=$(run "$FIX_BAD" "$FIX_BAD/docs/decisions/0001-bad.md" "$REAL_PLUGIN_ROOT")
assert_exit "invalid ADR edit -> gate fails -> exit 2" 2 "$code"

code=$(run "$FIX_NONE" "$FIX_NONE/CLAUDE.md" "$REAL_PLUGIN_ROOT")
assert_exit "no docs/decisions dir -> degrade gracefully -> exit 0" 0 "$code"

code=$(run "$FIX_OK" "$FIX_OK/CLAUDE.md" "$REAL_PLUGIN_ROOT")
assert_exit "CLAUDE.md edit, valid corpus -> gate runs, passes -> exit 0" 0 "$code"

code=$(run "$FIX_OK" "$FIX_OK/.claude/agents/some-agent.md" "$REAL_PLUGIN_ROOT")
assert_exit "agents/*.md edit, valid corpus -> gate runs, passes -> exit 0" 0 "$code"

code=$(run "$FIX_OK" "$FIX_OK/.claude-plugin/marketplace.json" "$REAL_PLUGIN_ROOT")
assert_exit "marketplace.json edit, valid corpus -> gate runs, passes -> exit 0" 0 "$code"

code=$(run "$FIX_OK" "$FIX_OK/README.md" "$REAL_PLUGIN_ROOT")
assert_exit "out-of-scope file (README.md) -> exit 0, gate not invoked" 0 "$code"

# Windows-escaped path (doubled backslash, as it arrives JSON-escaped from a real Windows hook payload).
win_fp=$(printf '%s' "$FIX_OK/docs/decisions/0001-good.md" | sed 's/\//\\\\/g')
json=$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$win_fp")
code=$(printf '%s' "$json" | CLAUDE_PROJECT_DIR="$FIX_OK" CLAUDE_PLUGIN_ROOT="$REAL_PLUGIN_ROOT" bash "$HOOK"; echo $?)
assert_exit "Windows-escaped backslash path -> normalized, gate runs, passes -> exit 0" 0 "$code" "fp=[$win_fp]"

# Missing file_path entirely.
json='{"tool_name":"Write","tool_input":{}}'
code=$(printf '%s' "$json" | CLAUDE_PROJECT_DIR="$FIX_OK" CLAUDE_PLUGIN_ROOT="$REAL_PLUGIN_ROOT" bash "$HOOK"; echo $?)
assert_exit "missing file_path -> fails open -> exit 0" 0 "$code"

# Out-of-repo path (absolute path with no relation to CLAUDE_PROJECT_DIR's tree; still matches
# the docs/decisions pattern textually, so this also proves the hook is pattern-driven on the
# STRING, not filesystem-verified -- an accepted characteristic, not a bug, since the gate itself
# then does the real filesystem read and would fail closed on a genuinely missing file).
json='{"tool_name":"Write","tool_input":{"file_path":"/some/unrelated/out-of-repo/docs/decisions/9999-x.md"}}'
code=$(printf '%s' "$json" | CLAUDE_PROJECT_DIR="$FIX_NONE" CLAUDE_PLUGIN_ROOT="$REAL_PLUGIN_ROOT" bash "$HOOK"; echo $?)
assert_exit "out-of-repo path, project has no docs/decisions -> degrade gracefully -> exit 0" 0 "$code"

# Malformed/empty stdin.
code=$(printf '' | CLAUDE_PROJECT_DIR="$FIX_OK" CLAUDE_PLUGIN_ROOT="$REAL_PLUGIN_ROOT" bash "$HOOK"; echo $?)
assert_exit "malformed/empty stdin -> fails open -> exit 0" 0 "$code"

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
