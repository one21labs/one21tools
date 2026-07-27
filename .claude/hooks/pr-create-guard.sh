#!/usr/bin/env bash
# PreToolUse hook (matcher: Bash) for THIS REPO's .claude/settings.json (ADR 0047 wave-1
# publication guard; repo-instance because one21labs/* is hard-coded). CREATE-scoped: fires only
# on `gh pr create` / `gh issue create` -- NOT edit/comment/etc. Three guards, checked in order:
#   G3 (first -- an external target is denied even with a perfect body): a create targeting a
#      repo outside one21labs/* via -R/--repo is denied by default. The deny states the
#      deliberate-override path per ADR 0047: the OWNER runs the command themselves, or adds a
#      one-off allow for the exact command. This is a PARTIAL in-repo backstop -- the hazard is
#      cross-repo, so CLAUDE.md's prose rule stays structurally load-bearing (ADR 0047 (a)).
#   G1: the body must arrive via --body-file/-F. Inline --body/-b is denied (quoting-unsafe on
#      PS 5.1, and an inline body can't be content-checked before publication).
#   G2: the body file must contain the Claude disclosure line -- checked BEFORE the
#      artifact exists, not at CI.
#
# COMMAND-WORD ANCHOR: `gh pr create` only counts at a command-word
# position -- start of command or right after `&&`/`;`/`|` -- so `echo 'gh pr create'`
# (single-quoted: survives the JSON extraction) is not an invocation. Double-quoted mentions
# (`grep "gh pr create" f`) never even reach the matcher: the house [^"]* extraction ends at the
# first escaped quote -- a miss, never a false fire. Flag parsing is bounded to the create invocation's own pipeline segment (cut at the
# first `&&`/`;`/`|`), so a -R in a later chained command is never misattributed.
#
# FLAG FORMS: the long spellings take `=` or whitespace (`--repo=o/r`, `--repo o/r`). The SHORT
# spellings additionally take the value ATTACHED, with no separator at all (`-Ro/r`, `-Fb.md`,
# `-bhello`) — that is pflag's behaviour, which is what gh uses. Requiring a separator on the short
# forms silently disarmed ALL THREE sub-guards: `gh pr create -Revil/repo ...` matched nothing, so
# the external-repo deny — this repo's only in-session backstop for CLAUDE.md's "no external
# publication without approval" — did not fire. The three canaries below all declared the DETACHED
# form, so the shipped canary suite passed green while every guard was bypassable. Each hole now
# has its own attached-form canary; a canary set that only exercises the shape the author had in
# mind is not coverage.
#
# JSON SAFETY: every deny reason is sanitized (double quotes, backslashes, newlines, tabs
# stripped) before interpolation, so a hostile body-file path cannot break the deny JSON.
#
# FAIL OPEN (exit 0, no deny) on: malformed/empty stdin; no body flags at all (gh errors or
# opens its editor on its own); an unreadable/nonexistent body file (gh will error legibly);
# an env-var-prefixed invocation (`FOO=1 gh pr create` -- not at a command-word position, a
# documented miss that CI's check-pr-body backstop still catches); a QUOTED --body-file path
# (extraction ends at the quote, so no body flag is seen -- same miss class).
#
# liveness: per-event-exempt -- a deny fires only on a violating create command, which may
# legitimately never occur in a window (ADR 0086 (b)). Canaries: one per sub-guard (G3
# external target, G1 inline body, G2 missing disclosure). Grammar: scripts/check-gate-tests.mjs.
# canary: {"event":"PreToolUse","tool":"Bash","stdin":{"tool_name":"Bash","tool_input":{"command":"gh pr create -R evil/repo --title t --body-file b.md"}},"expect":{"deny":true}}
# canary: {"event":"PreToolUse","tool":"Bash","stdin":{"tool_name":"Bash","tool_input":{"command":"gh pr create --title t --body hello"}},"expect":{"deny":true}}
# canary: {"event":"PreToolUse","tool":"Bash","files":{"b.md":"a body without the required line"},"stdin":{"tool_name":"Bash","tool_input":{"command":"gh issue create --title t --body-file b.md"}},"expect":{"deny":true}}
# canary: {"event":"PreToolUse","tool":"Bash","stdin":{"tool_name":"Bash","tool_input":{"command":"gh pr create -Revil/repo --title t -Fb.md"}},"expect":{"deny":true}}
# canary: {"event":"PreToolUse","tool":"Bash","stdin":{"tool_name":"Bash","tool_input":{"command":"gh pr create --title t -bhello"}},"expect":{"deny":true}}
# canary: {"event":"PreToolUse","tool":"Bash","files":{"b.md":"a body without the required line"},"stdin":{"tool_name":"Bash","tool_input":{"command":"gh issue create --title t -Fb.md"}},"expect":{"deny":true}}
# canary: {"event":"PreToolUse","tool":"Bash","stdin":{"tool_name":"Bash","tool_input":{"command":"gh pr create --fill --title t"}},"expect":{"deny":true}}
# canary: {"event":"PreToolUse","tool":"Bash","stdin":{"tool_name":"Bash","tool_input":{"command":"gh pr comment -R outside/repo --body-file b.md"}},"expect":{"deny":true}}
# canary: {"event":"PreToolUse","tool":"Bash","stdin":{"tool_name":"Bash","tool_input":{"command":"gh issue edit 5 --repo outside/repo --add-label x"}},"expect":{"deny":true}}
# Gate-hit telemetry has one home (lib/hook-lib.sh). Sourced script-relative, not via
# CLAUDE_PROJECT_DIR: the canary runner executes hooks from their real repo path against a
# throwaway fixture project. A missing lib exits 0 — telemetry must never block a guard.
. "$(dirname "${BASH_SOURCE[0]}")/../../pdca-workflow/hooks/lib/hook-lib.sh" 2>/dev/null || exit 0

input=$(cat)
cmd=$(printf '%s' "$input" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -z "$cmd" ] && exit 0

deny() {  # $1 = reason, $2 = sub-guard tag for telemetry context
  # Gate-hit telemetry (ADR 0080): observability only, never in the failure path — the deny below
  # prints regardless. Format, field scrub and the ADR 0071 marker check live in lib/hook-lib.sh.
  hook_gate_hit pr-create-guard "${2:-}"
  reason=$(printf '%s' "$1" | tr -d '"\\' | tr '\n\t' '  ')
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}' "$reason"
  exit 0
}

# EVERY publishing invocation in the command, not just the first. `head -1` meant a compound like
# `gh pr create -R one21labs/x -F ok.md && gh pr comment -R evil/y -F c.md` was judged on its FIRST
# segment and the external comment in the tail was never seen. Widening the verb set made that
# load-bearing, so the guard now loops over all of them. A cross-family review found it.
#
# VERBS ARE AN EXEMPT-LIST, NOT A MATCH-LIST, and that inversion is the whole point. This guard
# was widened three times -- create, then +comment|edit, then +review -- each time by adding the
# verb that had just been shown to walk past, while its own comment warned against "anchoring a
# guard to the verbs its author happened to think of". Round 9 then found `gh pr merge -b`,
# `gh pr close -c` and `gh pr reopen -c` still uncovered: all of them write to a foreign repo and
# carry a body. So the default flipped. Every `gh pr|issue <verb>` is checked EXCEPT the read-only
# ones named here, which means the next verb GitHub invents is covered on the day it ships rather
# than on the day it is caught.
segs=$(printf '%s' "$cmd" | tr ';|&' '\n\n\n' \
  | grep -E '^[[:space:]]*gh[[:space:]]+(pr|issue)[[:space:]]+[a-z-]+' \
  | grep -vE '^[[:space:]]*gh[[:space:]]+(pr|issue)[[:space:]]+(view|list|status|diff|checks|checkout|develop)\b')
[ -z "$segs" ] && exit 0

# A here-string, NOT a pipe. `... | while read` runs the loop body in a SUBSHELL, so deny's exit
# would end only that subshell -- the loop would carry on and a second segment could print a SECOND
# deny JSON to the same stdout, which the host cannot parse as one decision.
while IFS= read -r seg; do
  [ -z "$seg" ] && continue
  seg=$(printf '%s' "$seg" | sed -E 's/^[[:space:]]*//')
  kind=$(printf '%s' "$seg" | sed -nE 's/^gh[[:space:]]+(pr|issue)[[:space:]].*/\1/p')
  verb=$(printf '%s' "$seg" | sed -nE 's/^gh[[:space:]]+(pr|issue)[[:space:]]+(create|comment|edit|review)\b.*/\2/p')

  # G3 -- external repo target: deny by default, override path stated.
  repo=$(printf '%s' "$seg" | grep -oE '(^|[[:space:]])(--repo(=|[[:space:]]+)|-R(=|[[:space:]]*))[^[:space:]]+' | head -1 \
    | sed -E 's/^[[:space:]]*(--repo(=|[[:space:]]+)|-R(=|[[:space:]]*))//')
  if [ -n "$repo" ]; then
    case "$repo" in
      one21labs/*) : ;;
      *) deny "Denied by default: gh $kind $verb targets $repo, outside one21labs/* -- external publication requires per-item owner approval of the exact text (CLAUDE.md). Override path: the owner runs this command themselves, or adds a one-off permission allow for this exact command. Leave the draft in the internal issue instead." external-repo ;;
    esac
  fi

  # BODY CHECKS key on whether THIS invocation carries a body, never on the verb. Keying on
  # create|comment let `gh pr edit --body '...'` and `gh issue edit -F b.md` publish text with no
  # disclosure check at all -- a fail-open introduced by the same commit that widened the verbs.
  # A verb with no body flag (`gh pr edit --add-label chore`) publishes nothing and passes.
  bf=$(printf '%s' "$seg" | grep -oE '(^|[[:space:]])(--body-file(=|[[:space:]]+)|-F(=|[[:space:]]*))[^[:space:]]+' | head -1 \
    | sed -E 's/^[[:space:]]*(--body-file(=|[[:space:]]+)|-F(=|[[:space:]]*))//')

  # --fill IS a body source: it takes the commit message as the PR body, which cannot be
  # content-checked before publication. Denied ONLY when no --body-file accompanies it -- the first
  # version denied unconditionally, refusing `--fill --body-file b.md` even though that supplies
  # exactly the checkable file the deny message asks for.
  if [ -z "$bf" ] && printf '%s' "$seg" | grep -qE '(^|[[:space:]])--fill(-first|-verbose)?([[:space:]]|$)'; then
    deny "Denied: --fill takes the body from the commit message, so nothing can be content-checked before publication (the disclosure line especially). Write the body to a file and pass --body-file <file>." fill-body
  fi

  if [ -z "$bf" ]; then
    if printf '%s' "$seg" | grep -qE '(^|[[:space:]])(--body(=|[[:space:]]|$)|-b(=|[[:space:]]|[^[:space:]]|$))'; then
      deny "Denied: pass the body via --body-file <file> (quoting-safe on PS 5.1, and lets this hook verify the disclosure line before anything is published). Write the body to a file first." inline-body
    fi
    continue   # no body flags at all: let gh open its editor / error on its own
  fi

  # G2 -- body content checks. Relative paths resolve against the project root (the Bash tool's
  # cwd); substring matches are CRLF-safe (neither phrase spans a line ending).
  cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null
  body=$(cat "$bf" 2>/dev/null) || continue   # unreadable file: gh will error legibly
  case "$body" in
    *'Disclosure: written by Claude'*) : ;;
    *) deny "Denied: body file $bf is missing the Claude authorship disclosure line (CLAUDE.md: required on every issue and PR Claude writes, at creation time). Append: *Disclosure: written by Claude (Claude Code) under the direction of the repo owner.*" missing-disclosure ;;
  esac
done <<< "$segs"
exit 0
