#!/usr/bin/env bash
# Shared skeleton for every file_path-matched hook — this plugin's own, and the repo-local
# .claude/hooks that dogfood it. Sourced, never executed; defines functions only.
#
# WHY THIS EXISTS: every file_path hook needs the same steps before it can route — pull
# tool_input.file_path out of the payload, collapse backslashes, make the path absolute — and
# getting any of them wrong is INVISIBLE. The hook does not error; it just stops matching and
# stops firing, and the surface it guards goes unwatched with no symptom. Hand-rolled per hook,
# the copies drift apart one fix at a time. One home means one place to be right (CLAUDE.md
# poka-yoke: delete the mirror, derive). The same logic cuts the other way and is the standing
# risk of this file: a defect here disarms four guards at once, so every change needs the canary
# suite (scripts/check-gate-tests.mjs) run, not just the unit tests.
#
# CONSUMERS SOURCE IT SCRIPT-RELATIVE, not via CLAUDE_PROJECT_DIR — the canary runner executes
# hooks from their real repo path against a throwaway fixture project dir, so a
# CLAUDE_PROJECT_DIR-relative source would break under test while looking fine in a session.
#   plugin hook:      . "$(dirname "${BASH_SOURCE[0]}")/lib/hook-lib.sh"
#   repo-local hook:  . "$(dirname "${BASH_SOURCE[0]}")/../../pdca-workflow/hooks/lib/hook-lib.sh"
# BASH_SOURCE, not $0, so the path stays right if a hook is ever sourced rather than executed.
#
# A MISSING LIB FAILS OPEN (the consumer exits 0), which would silently disarm all four guards
# — the ADR 0086 silent-coverage-gap class. What stops that being silent is check-gate-tests:
# every consumer declares canaries that EXECUTE the real hook and assert the deny/exit, so a lib
# that cannot be sourced fails CI on every hook at once rather than passing quietly.

# ASCII record separator. Two jobs, both the same idea: make a signal EXPLICIT rather than
# inferred from the shape of some output. A subprocess prefixes it to say "this is my answer,
# and it starts here" — so an interpreter that prints a startup banner, or a runtime that
# succeeds while producing nothing usable, cannot be mistaken for a decision. Exported because
# the python bodies in the PreToolUse guards read it from the environment; it has one home.
export HOOK_DENY_MARK=$'\036'

# Forward and backslash both, JSON-escaped or not, collapsed to forward slashes.
hook_norm_slashes() {
  printf '%s' "$1" | sed 's/\\\\/\//g; s/\\/\//g'
}

# Echo the edited file's path from a hook's stdin JSON: normalized to forward slashes and to an
# absolute path. Empty output means the payload named no file (the caller decides whether that
# is an exit-0 skip).
#
# It PARSES the JSON rather than pattern-matching it, and reads specifically `tool_input`
# .file_path. A lexical scan cannot do this safely: a PostToolUse payload carries a tool_response
# alongside the tool_input, `content`/`new_string` hold the entire text being written, and a
# regex has no way to tell which "file_path" is the one the tool acted on — a greedy one gates the
# echoed path instead of the edited one. Measured at 14ms, the same as the three-process sed
# pipeline it replaces, so correctness here costs nothing.
#
# EVERY INTERPRETER IS TRIED UNTIL ONE MARKS AN ANSWER. "It exited 0" is not the same claim as
# "it parsed this": python 2 returns a non-`str` for every JSON string and would hand back an
# empty path with a clean exit, and a runtime with a startup banner writes to the same stdout the
# answer arrives on. Both look like success and would stop the fallthrough, leaving a guard that
# routes nothing. So the answer must arrive behind the marker, and anything printed ahead of it
# is discarded. Nothing parses it => empty, which is fail-open: there is no tier that guesses,
# because a guessed path aims a guard at the wrong file.
#
# The payload goes in on STDIN, never the environment: a Write payload carries the entire file
# content, and a large one would blow the environment-size limit and disarm the guard on exactly
# the big edits that matter most.
#
# Absolute-ness is not cosmetic: every consumer routes on `*/dir/*` case arms, which need a
# literal `/` ahead of `dir`, so a repo-relative path falls through every arm and the gate does
# not run. `?:/*` covers a Windows drive path, which is absolute but has no leading slash.
hook_fp() {
  local raw fp="" parsed="" py root
  for py in python3 python; do
    command -v "$py" >/dev/null 2>&1 || continue
    raw=$(printf '%s' "$1" | HOOK_MARK="$HOOK_DENY_MARK" "$py" -c '
import json, os, sys
if sys.version_info[0] < 3:      # py2 JSON strings are not str; an empty answer would look fine
    sys.exit(1)
d = json.loads(sys.stdin.read())
p = (d.get("tool_input") or {}).get("file_path")
if not isinstance(p, str) or "\x00" in p:   # a NUL would truncate the path inside the shell
    p = ""
sys.stdout.write(os.environ["HOOK_MARK"] + p)
' 2>/dev/null) || continue
    case "$raw" in *"$HOOK_DENY_MARK"*) fp="${raw##*"$HOOK_DENY_MARK"}"; parsed=1; break ;; esac
  done
  if [ -z "$parsed" ] && command -v node >/dev/null 2>&1; then
    raw=$(printf '%s' "$1" | HOOK_MARK="$HOOK_DENY_MARK" node -e '
let s = "";
process.stdin.on("data", (c) => (s += c)).on("end", () => {
  const p = (JSON.parse(s).tool_input || {}).file_path;
  const ok = typeof p === "string" && p.indexOf("\u0000") === -1;
  process.stdout.write(process.env.HOOK_MARK + (ok ? p : ""));
});
' 2>/dev/null) || raw=""
    case "$raw" in *"$HOOK_DENY_MARK"*) fp="${raw##*"$HOOK_DENY_MARK"}"; parsed=1 ;; esac
  fi
  [ -n "$parsed" ] || fp=""
  fp=$(hook_norm_slashes "$fp")
  case "$fp" in
    /*|?:/*|"") ;;
    *)
      root="${CLAUDE_PROJECT_DIR:-.}"
      while [ "$root" != "${root%/}" ]; do root="${root%/}"; done   # /proj/// joins as one slash
      [ -n "$root" ] || root="/"
      fp="$(hook_norm_slashes "$root")/$fp" ;;
  esac
  printf '%s' "$fp"
}

# Did the guard's decision body actually DECIDE to deny? The PreToolUse guards run a python body
# and re-emit its stdout to the host, so this is the line between "a decision was made" and
# "something got printed". It tests for the marker the body itself writes — not for the shape of
# the JSON, which would make the predicate guess at a serializer's spacing, key order and casing,
# and would read a stray mention of the word as a decision.
hook_is_deny() {
  case "$1" in *"$HOOK_DENY_MARK"*) return 0 ;; *) return 1 ;; esac
}

# The decision payload alone: everything after the marker, so a noisy interpreter's banner is
# never forwarded to the host as part of a hook response.
hook_deny_payload() {
  printf '%s' "${1##*"$HOOK_DENY_MARK"}"
}

# Append one gate-hit telemetry line (ADR 0080). Observability only: it is called AFTER the
# failure is decided, swallows every error, and always returns 0, so it can never become the
# reason a gate did or did not fire. Line format's one home is scorecard.mjs parseGateHits, which
# parses per line and splits on whitespace — hence the scrub, so a path containing a newline or a
# tab cannot split a row or shift a field. docs/pdca is the ADR 0071 adoption marker — checked,
# never created.
# PATHS ARE LOGGED PROJECT-RELATIVE, NEVER ABSOLUTE. This log is COMMITTED (docs/pdca is a tracked
# adoption marker), so in a public repo an absolute path publishes the operator's home directory and
# local tree layout on every single gate fire — this repo shipped 76 such lines before anyone
# looked. It is also the more useful value: the same gate firing on the same file from two machines
# should read as one context, not two. Nothing consumes it as a decision (scorecard's parseGateHits
# keeps it as `context` and only displays it). Stripping HERE, at the one writer, is the only place
# that can guarantee it — a reviewer noticing an absolute path in a diff is the weakest rung, and
# that rung already failed 76 times.
hook_gate_hit() {
  local root="${CLAUDE_PROJECT_DIR:-.}" name path
  name=$(printf '%s' "$1" | tr '\n\r\t' '   ')
  path=$(printf '%s' "$2" | tr '\n\r\t' '   ')
  while [ "$root" != "${root%/}" ]; do root="${root%/}"; done   # /proj/// and /proj strip alike
  [ -n "$root" ] && [ "$root" != "." ] && path="${path#"$root"/}"
  { [ -d "$root/docs/pdca" ] && printf '%s gate-hit %s %s\n' \
      "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$name" "$path" >> "$root/docs/pdca/gate-hits.txt"; } 2>/dev/null
  return 0
}
