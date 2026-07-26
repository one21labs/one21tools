#!/usr/bin/env bash
# Decision-logic test for backstory-edit-guard.sh (CLAUDE.md Never rule: no process-gating script
# without a test of its decision logic). The two DENY fixtures are the verbatim insertions the
# owner caught by hand on 26-Jul-2026 — a backstory guard that does not fire on the backstory that
# caused it is worthless. Runnable: bash .claude/hooks/test-backstory-edit-guard.sh
set -u
H="$(cd "$(dirname "$0")" && pwd)/backstory-edit-guard.sh"
pass=0; fail=0

run() { printf '%s' "$2" | bash "$H" 2>/dev/null; }

expect() { # name json expect_deny
  out=$(run "$1" "$2")
  got=no; case "$out" in *'"deny"'*) got=yes;; esac
  if [ "$got" = "$3" ]; then pass=$((pass+1)); else
    fail=$((fail+1)); echo "FAIL: $1 (expected deny=$3, got deny=$got)"; echo "  out: $out"; fi
}

j() { python3 -c 'import json,sys; print(json.dumps({"tool_name":sys.argv[1],"tool_input":{"file_path":sys.argv[2],("content" if sys.argv[1]=="Write" else "new_string"):sys.argv[3]}}))' "$1" "$2" "$3"; }

# --- the real instances ---
expect "real: ADR rename narration" \
  "$(j Write docs/decisions/0082-x.md 'Shipped as `MSH-baby` and renamed to `MSH` on owner direction, 26-Jul-2026 (name only).')" yes
expect "real: doc narrating its own deleted clause" \
  "$(j Write skill-bench/skills/bench/references/x.md 'An earlier draft of this paragraph added that it is not the metric-gaming variety. That clause is deleted, and its deletion is the point.')" yes

# --- other forms of the same move ---
expect "used-to-say" "$(j Edit README.md 'This section used to say the judge was grok by default.')" yes
expect "formerly-called" "$(j Write CLAUDE.md 'The command, formerly called MSH-baby, ships one package.')" yes
expect "this-replaced" "$(j Write docs/x.md 'This replaced the older three-arm design.')" yes

# --- must NOT fire: ordinary prose, instructions, and legitimate history ---
expect "plain instruction" "$(j Write README.md 'Rename the skill folder to match the name field, then run validate.py.')" no
expect "present-tense doctrine" \
  "$(j Write skill-bench/skills/bench/references/x.md 'State the finding without the mitigating clause. If the clause is load-bearing it survives on its own.')" no
expect "frozen benchmark dir is exempt" \
  "$(j Write benchmarks/2026-07-17-thirdparty/README.md 'An earlier draft of the pre-registration used four arms; this replaced it.')" no
expect "pdca log is exempt" "$(j Write docs/pdca/notes.md 'The gate was renamed to something else.')" no
expect "non-markdown ignored" "$(j Write scripts/x.py 'was renamed from foo')" no
expect "empty edit ignored" '{"tool_name":"Edit","tool_input":{"file_path":"README.md"}}' no

# --- fail-open: a broken payload must never block an edit ---
expect "garbage stdin fails open" 'not json at all' no

echo "backstory-edit-guard: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
