#!/usr/bin/env bash
# Decision-logic test for pr-create-guard.sh. Runnable on git-bash:
# `bash test-pr-create-guard.sh`. Builds body fixtures under mktemp -d (never the real repo).
# Every deny output is also fed to node JSON.parse -- a deny reason that breaks the JSON is a
# test failure regardless of the decision being right.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/pr-create-guard.sh"
pass=0; fail=0

FIX=$(mktemp -d)
trap 'rm -rf "$FIX"' EXIT
GOOD="$FIX/good-body.md"; BAD="$FIX/bad-body.md"; CRLF="$FIX/crlf-body.md"
printf 'Purpose: x\nRetrospective: run\n\n*Disclosure: written by Claude (Claude Code) under the direction of the repo owner.*\n' > "$GOOD"
printf 'Purpose: x\n' > "$BAD"
printf 'Purpose: x\r\nRetrospective: run\r\n\r\n*Disclosure: written by Claude (Claude Code) under the direction of the repo owner.*\r\n' > "$CRLF"

# $1 = name, $2 = the command value EXACTLY as it appears inside the stdin JSON string
#      (i.e. already JSON-encoded: literal \" for a double quote), $3 = deny|allow,
# $4 = optional substring the deny reason must contain.
run_case() {
  name="$1"; jsoncmd="$2"; expect="$3"; want="${4:-}"
  out=$(printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$jsoncmd" \
        | CLAUDE_PROJECT_DIR="$FIX" bash "$HOOK"); code=$?
  if printf '%s' "$out" | grep -q '"permissionDecision":"deny"'; then got=deny; else got=allow; fi
  ok=0
  [ "$code" = "0" ] || ok=1
  [ "$got" = "$expect" ] || ok=1
  if [ -n "$out" ]; then
    printf '%s' "$out" | node -e 'let d="";process.stdin.on("data",c=>d+=c).on("end",()=>{JSON.parse(d)})' 2>/dev/null || ok=1
  fi
  if [ -n "$want" ] && ! printf '%s' "$out" | grep -qi "$want"; then ok=1; fi
  if [ "$ok" = "0" ]; then pass=$((pass+1)); printf 'PASS: %s\n' "$name"
  else fail=$((fail+1)); printf 'FAIL: %s (expected %s, got %s, exit=%s) out=[%s]\n' "$name" "$expect" "$got" "$code" "$out"; fi
}

# --- The prototype's original nine ---
run_case "deny G1: inline --body"                        "gh pr create --title x --body inline-text"                     deny  "body-file"
run_case "allow: pr create with compliant body file"     "gh pr create --title x --body-file $GOOD"                      allow
run_case "deny G2: body file missing disclosure"         "gh pr create --title x --body-file $BAD"                       deny  "disclosure"
run_case "deny G3: external repo, -R space form"         "gh pr create -R other/repo --title x --body-file $GOOD"        deny  "one21labs"
run_case "allow: internal repo -R one21labs/x"           "gh pr create -R one21labs/x --title x --body-file $GOOD"       allow
run_case "allow: non-gh command"                         "git commit -m msg"                                             allow
run_case "allow: gh but not a create subcommand"         "gh pr checks 123"                                              allow

# --- Hardening additions ---
# Command-word anchoring traps. Double-quoted mention: the JSON carries escaped quotes, so the
# [^\"]* extraction ends before the phrase. Single-quoted mention: survives extraction, but 'gh'
# sits after a quote, not at a command-word position.
run_case "allow: double-quoted mention (grep)"           "grep \\\"gh pr create\\\" file | head"                          allow
run_case "allow: single-quoted mention (echo)"           "echo 'gh pr create'"                                           allow
run_case "deny: anchored after && still fires (G1)"      "cd /some/dir && gh pr create --title x --body inline"          deny  "body-file"

# --repo equals form, external.
run_case "deny G3: external repo, --repo= equals form"   "gh issue create --repo=ext/repo --title x --body-file $GOOD"   deny  "one21labs"

# External READs and non-create writes are out of scope (create-scoped per amended ADR 0047).
run_case "allow: gh pr list -R external (read)"          "gh pr list -R other/repo"                                      allow
run_case "allow: gh pr view -R external (read)"          "gh pr view 7 --repo other/repo"                                allow
run_case "allow: gh pr edit -R external (create-scoped)" "gh pr edit 7 -R other/repo --body-file $GOOD"                  allow

# CRLF body file still matches both lines.
run_case "allow: CRLF body file, disclosure found"       "gh pr create --title x --body-file $CRLF"                      allow

# Flag-form coverage: -F short form and --body-file= equals form.
run_case "deny: -F short form parsed (missing disclosure)" "gh pr create --title x -F $BAD"                              deny  "disclosure"
run_case "deny: --body-file= equals form parsed"         "gh pr create --title x --body-file=$BAD"                       deny  "disclosure"

# Fail-open paths.
run_case "allow: unreadable body file (gh will error)"   "gh pr create --title x --body-file /nonexistent/nope.md"       allow
run_case "allow: bare create, no body flags (editor path)" "gh pr create"                                                allow

# Segment bounding: a -R in a LATER chained command is not misattributed to the create.
run_case "allow: -R external in a later && segment"      "gh pr create --body-file $GOOD && gh pr view 1 -R other/repo"  allow

# Malformed/empty stdin fails open.
out=$(printf '' | CLAUDE_PROJECT_DIR="$FIX" bash "$HOOK"); code=$?
if [ "$code" = "0" ] && [ -z "$out" ]; then pass=$((pass+1)); printf 'PASS: allow: malformed/empty stdin fails open\n'
else fail=$((fail+1)); printf 'FAIL: allow: malformed/empty stdin fails open (exit=%s out=[%s])\n' "$code" "$out"; fi

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
