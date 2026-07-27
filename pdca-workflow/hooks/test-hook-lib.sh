#!/usr/bin/env bash
# Decision-logic test for the sibling lib/hook-lib.sh (CI runs every hooks/test-*.sh via
# .github/workflows/gates.yml). Runnable on git-bash: `bash test-hook-lib.sh`.
#
# hook_fp IS routing logic, not plumbing: every consumer hook decides whether to fire by matching
# `*/dir/*` case arms against its output, so a path shape this function gets wrong turns the whole
# guard into a silent no-op. That is the failure class ADR 0086 names, and both remaining
# consumers share this one implementation, so a defect here is two silent guards, not one.
#
# hook_is_deny is the other decision: the PreToolUse guards re-emit their python body's stdout to
# the host, and this predicate is all that stands between "a deny was decided" and "something got
# printed".
#
# hook_gate_hit's contract is the third: it is called from a failure path, so it must never be
# able to change an outcome — appends when the ADR 0071 marker dir exists, stays silent and still
# returns 0 when it does not.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # derived, never hard-coded (ADR 0069)
LIB="$HERE/lib/hook-lib.sh"
[ -f "$LIB" ] || { echo "FAIL: lib/hook-lib.sh missing at $LIB"; exit 1; }
# shellcheck disable=SC1090
. "$LIB"

pass=0; fail=0
assert_eq() {
  name="$1"; expect="$2"; got="$3"
  if [ "$got" = "$expect" ]; then
    pass=$((pass+1)); printf 'PASS: %s\n' "$name"
  else
    fail=$((fail+1)); printf 'FAIL: %s (expected "%s", got "%s")\n' "$name" "$expect" "$got"
  fi
}

json_for() { printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$1"; }

PROJ=$(mktemp -d)   # a synthetic project root; the real repo is never written to
export CLAUDE_PROJECT_DIR="$PROJ"

# --- hook_fp: the shapes a hook's case arms must be able to match ---
assert_eq "absolute posix path passes through unchanged" \
  "/repo/docs/decisions/0001-x.md" "$(hook_fp "$(json_for /repo/docs/decisions/0001-x.md)")"

assert_eq "repo-relative path is made absolute (else every */dir/* arm misses)" \
  "$PROJ/docs/decisions/0001-x.md" "$(hook_fp "$(json_for docs/decisions/0001-x.md)")"

assert_eq "bare filename at the repo root is made absolute" \
  "$PROJ/CLAUDE.md" "$(hook_fp "$(json_for CLAUDE.md)")"

# A Windows separator arrives JSON-escaped as a doubled backslash and is a REAL single backslash
# once parsed, which is what the slash normalizer then collapses.
assert_eq "JSON-escaped windows separators collapse to forward slashes" \
  "C:/repo/docs/decisions/0001-x.md" "$(hook_fp "$(json_for 'C:\\repo\\docs\\decisions\\0001-x.md')")"

assert_eq "a windows drive path is already absolute and is NOT re-rooted" \
  "C:/repo/CLAUDE.md" "$(hook_fp "$(json_for 'C:\\repo\\CLAUDE.md')")"

assert_eq "relative windows path is normalized AND made absolute" \
  "$PROJ/docs/x.md" "$(hook_fp "$(json_for 'docs\\x.md')")"

# --- hook_fp: reading the RIGHT key, which a lexical scan cannot do ---
# A PostToolUse payload echoes a tool_response beside the tool_input. A greedy regex takes the
# LAST match and gates the wrong file; a first-match regex is right only by field ordering luck.
assert_eq "tool_input wins over a tool_response that repeats the key" \
  "/repo/real.md" \
  "$(hook_fp '{"tool_name":"Edit","tool_input":{"file_path":"/repo/real.md"},"tool_response":{"file_path":"/tmp/echoed.md"}}')"

assert_eq "a file_path named only in tool_response is NOT the edited file" \
  "" "$(hook_fp '{"tool_name":"Edit","tool_response":{"file_path":"/tmp/echoed.md"}}')"

# Write/Edit payloads carry the whole text being written, which can itself contain the key.
assert_eq "a file_path string inside content does not hijack the match" \
  "/repo/real.md" \
  "$(hook_fp '{"tool_name":"Write","tool_input":{"file_path":"/repo/real.md","content":"example: \"file_path\": \"/tmp/decoy.md\""}}')"

assert_eq "pretty-printed multi-line payloads parse the same as compact ones" \
  "/repo/a.md" "$(printf '{\n  "tool_name": "Edit",\n  "tool_input": {\n    "file_path": "/repo/a.md"\n  }\n}' | { read -r -d "" j || true; hook_fp "$j"; })"

assert_eq "a path containing spaces survives intact" \
  "/repo/my docs/a b.md" "$(hook_fp "$(json_for '/repo/my docs/a b.md')")"

assert_eq "a path containing a dollar sign is not expanded" \
  '/repo/$HOME/x.md' "$(hook_fp "$(json_for '/repo/$HOME/x.md')")"

assert_eq "a JSON-escaped quote in a path is decoded, not truncated at it" \
  '/repo/wei"rd.md' "$(hook_fp '{"tool_name":"Write","tool_input":{"file_path":"/repo/wei\"rd.md"}}')"

# --- hook_fp: refusing to guess ---
assert_eq "no file_path in the payload yields empty (caller decides to skip)" \
  "" "$(hook_fp '{"tool_name":"Bash","tool_input":{"command":"ls"}}')"

assert_eq "malformed stdin yields empty rather than a guessed path" \
  "" "$(hook_fp 'not json at all')"

# `\r` parses as a carriage return and `\C` is not a valid escape at all, so this payload is not
# JSON. Empty (fail open) is the contract — a guard must never route on a reconstructed guess.
assert_eq "a raw unescaped backslash makes the payload invalid JSON: empty, not guessed" \
  "" "$(hook_fp '{"tool_name":"Write","tool_input":{"file_path":"C:\repo\CLAUDE.md"}}')"

assert_eq "a non-string file_path is not coerced" \
  "" "$(hook_fp '{"tool_name":"Write","tool_input":{"file_path":42}}')"

# --- hook_fp: the parser chain ---
# A broken-but-present interpreter is the trap: detecting it and stopping there returns an empty
# path, and an empty path is a guard that silently does not fire.
MULTI='{"tool_name":"Edit","tool_input":{"file_path":"/repo/real.md"},"tool_response":{"file_path":"/tmp/echoed.md"}}'
STUB=$(mktemp -d); printf '#!/bin/sh\nexit 127\n' > "$STUB/python3"
cp "$STUB/python3" "$STUB/python"; chmod +x "$STUB/python3" "$STUB/python"
assert_eq "a python that is on PATH but broken falls through to node, not to empty" \
  "/repo/real.md" "$(PATH="$STUB:$PATH" bash -c '. "$0"; hook_fp "$1"' "$LIB" "$MULTI")"

# The dangerous stub is not the one that crashes — it is the one that exits 0 having produced
# nothing usable, because "it worked" would stop the fallthrough and leave an empty path.
PY2=$(mktemp -d)
printf '#!/bin/sh\nexit 1\n' > "$PY2/python3"; cp "$PY2/python3" "$PY2/python"
chmod +x "$PY2/python3" "$PY2/python"
assert_eq "an interpreter that cannot answer (python 2 exits 1) falls through to node" \
  "/repo/real.md" "$(PATH="$PY2:$PATH" bash -c '. "$0"; hook_fp "$1"' "$LIB" "$MULTI")"

NOISY=$(mktemp -d)
printf '#!/bin/sh\necho "conda: activating base"\nexit 0\n' > "$NOISY/python3"
cp "$NOISY/python3" "$NOISY/python"; chmod +x "$NOISY/python3" "$NOISY/python"
assert_eq "an interpreter that exits 0 printing only a banner does not count as parsed" \
  "/repo/real.md" "$(PATH="$NOISY:$PATH" bash -c '. "$0"; hook_fp "$1"' "$LIB" "$MULTI")"
rm -rf "$PY2" "$NOISY"

assert_eq "a NUL in the path is refused outright, not truncated into a different path" \
  "" "$(hook_fp '{"tool_name":"Write","tool_input":{"file_path":"/repo/foo\u0000bar.md"}}')"

BARE=$(mktemp -d)
for b in bash sed grep tr date cat; do ln -sf "$(command -v "$b")" "$BARE/$b" 2>/dev/null; done
# bash itself must be in the fixture PATH: without it the `bash -c` below never runs and the
# assertion passes on an empty result for the wrong reason.
assert_eq "no JSON parser reachable at all: empty, so every consumer skips (fail open)" \
  "" "$(PATH="$BARE" bash -c '. "$0"; hook_fp "$1"' "$LIB" "$MULTI")"
rm -rf "$STUB" "$BARE"

# --- hook_fp: the project root it joins against ---
assert_eq "unset CLAUDE_PROJECT_DIR falls back to . rather than dropping the path" \
  "./docs/x.md" "$(CLAUDE_PROJECT_DIR= hook_fp "$(json_for docs/x.md)")"

assert_eq "a trailing slash on CLAUDE_PROJECT_DIR does not produce a doubled separator" \
  "/proj/docs/x.md" "$(CLAUDE_PROJECT_DIR=/proj/ hook_fp "$(json_for docs/x.md)")"

assert_eq "several trailing slashes collapse too, not just one" \
  "/proj/docs/x.md" "$(CLAUDE_PROJECT_DIR=/proj/// hook_fp "$(json_for docs/x.md)")"

# --- hook_is_deny: a decision, not merely output ---
# Driven by a REAL guard's stdout, not a hand-written string shaped to satisfy the predicate —
# a golden literal here would pass no matter how far the guard's actual output drifted.
REPO="$(cd "$HERE/../.." && pwd)"
GUARD="$REPO/.claude/hooks/budget-edit-guard.sh"
if [ -x "$GUARD" ]; then
  GFIX=$(mktemp -d); mkdir -p "$GFIX/docs/pdca"
  REAL=$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s/CLAUDE.md","content":"far over a ten char cap"}}' "$GFIX" \
    | CLAUDE_PROJECT_DIR="$GFIX" \
      BUDGET_GUARD_CAPS_JSON='{"doc":10,"adr":10,"lite":10,"agent":10,"skill":10,"ref":10,"refToc":10}' \
      bash "$GUARD")
  # End to end the marker is INTERNAL: the body writes it, the guard's tail consumes it, and the
  # host must receive clean JSON. Both halves are asserted, because a marker that leaked would be
  # a malformed hook response and a marker that never arrived would be a silently allowed edit.
  assert_eq "the live guard still emits a deny decision the host can act on" \
    "deny" "$(printf '%s' "$REAL" | sed -n 's/.*"permissionDecision": *"\([a-z]*\)".*/\1/p')"
  assert_eq "the internal marker never leaks into the host-facing response" \
    "0" "$(printf '%s' "$REAL" | tr -cd "$HOOK_DENY_MARK" | wc -c | tr -d ' ')"
  rm -rf "$GFIX"
else
  echo "SKIP: budget-edit-guard.sh not executable at $GUARD"; fail=$((fail+1))
fi

hook_is_deny "" && r=yes || r=no
assert_eq "empty output is not a deny" "no" "$r"
hook_is_deny "DeprecationWarning: something imported noisily" && r=yes || r=no
assert_eq "a stray banner on stdout is NOT a deny (it must not be re-emitted as a decision)" "no" "$r"
# The old substring predicate read this as a deny: the tokens are present, the decision is not.
hook_is_deny '{"hookSpecificOutput":{"permissionDecision":"allow","reason":"not a deny"}}' && r=yes || r=no
assert_eq "an allow whose text merely mentions deny is not a deny" "no" "$r"
assert_eq "a banner printed ahead of the decision is stripped, never forwarded to the host" \
  '{"ok":1}' "$(hook_deny_payload "conda: activating base${HOOK_DENY_MARK}{\"ok\":1}")"

# --- hook_gate_hit: observability that can never become a failure path ---
mkdir -p "$PROJ/docs/pdca"
hook_gate_hit test-gate "$PROJ/CLAUDE.md"
assert_eq "one append per call, naming the gate AND the PROJECT-RELATIVE path after an ISO-8601Z stamp" \
  "1" "$(grep -cE "^20[0-9]{2}-[01][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z gate-hit test-gate CLAUDE\.md\$" "$PROJ/docs/pdca/gate-hits.txt")"
# RELATIVE is the assertion, and the `$` anchor is what enforces it: this log is COMMITTED, and an
# absolute path publishes the operator's home directory on every gate fire in a public repo.
# Asserted rather than trusted, because the leak has no symptom -- the hook works either way, and
# only a reader of the committed log would ever notice.
hook_gate_hit test-gate "/somewhere/else/outside.md"
assert_eq "a path OUTSIDE the project is left absolute rather than mangled into a false relative" \
  "1" "$(grep -c ' gate-hit test-gate /somewhere/else/outside\.md$' "$PROJ/docs/pdca/gate-hits.txt")"
: > "$PROJ/docs/pdca/gate-hits.txt"   # reset: the row-count assertions below start from zero
hook_gate_hit test-gate "$PROJ/CLAUDE.md"

# gate-hits.txt is one row per line, so an embedded newline must not split a row.
hook_gate_hit test-gate "$(printf '/repo/we\nird.md')"
assert_eq "a newline inside a path cannot split one hit into two rows" \
  "2" "$(wc -l < "$PROJ/docs/pdca/gate-hits.txt")"

NOMARK=$(mktemp -d)
CLAUDE_PROJECT_DIR="$NOMARK" hook_gate_hit test-gate "$NOMARK/CLAUDE.md"
assert_eq "no docs/pdca adoption marker: nothing written, nothing created (ADR 0071)" \
  "absent" "$([ -e "$NOMARK/docs" ] && echo present || echo absent)"

CLAUDE_PROJECT_DIR="$NOMARK" hook_gate_hit test-gate "$NOMARK/CLAUDE.md"; rc=$?
assert_eq "returns 0 even when it wrote nothing — it must not alter a caller's exit path" "0" "$rc"

CLAUDE_PROJECT_DIR="/nonexistent-$$/nowhere" hook_gate_hit test-gate "x"; rc=$?
assert_eq "unwritable project root: still silent, still 0" "0" "$rc"

rm -rf "$PROJ" "$NOMARK"
printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
