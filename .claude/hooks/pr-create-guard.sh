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
#   G2: the body file must contain the Claude disclosure line, and for `gh pr create` also a
#      `Retrospective:` line (ADR 0030) -- checked BEFORE the artifact exists, not at CI.
#
# COMMAND-WORD ANCHOR (session-operator finding): `gh pr create` only counts at a command-word
# position -- start of command or right after `&&`/`;`/`|` -- so `echo 'gh pr create'`
# (single-quoted: survives the JSON extraction) is not an invocation. Double-quoted mentions
# (`grep "gh pr create" f`) never even reach the matcher: the house [^"]* extraction ends at the
# first escaped quote (retrospect-reminder.sh's documented limitation) -- a miss, never a false
# fire. Flag parsing is bounded to the create invocation's own pipeline segment (cut at the
# first `&&`/`;`/`|`), so a -R in a later chained command is never misattributed.
#
# -R/--repo AND --body-file/-F both accept `=` and space forms (`--repo=o/r`, `-R o/r`, ...).
#
# JSON SAFETY: every deny reason is sanitized (double quotes, backslashes, newlines, tabs
# stripped) before interpolation, so a hostile body-file path cannot break the deny JSON.
#
# FAIL OPEN (exit 0, no deny) on: malformed/empty stdin; no body flags at all (gh errors or
# opens its editor on its own); an unreadable/nonexistent body file (gh will error legibly);
# an env-var-prefixed invocation (`FOO=1 gh pr create` -- not at a command-word position, a
# documented miss that CI's check-pr-body backstop still catches); a QUOTED --body-file path
# (extraction ends at the quote, so no body flag is seen -- same miss class).
input=$(cat)
cmd=$(printf '%s' "$input" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -z "$cmd" ] && exit 0

deny() {
  reason=$(printf '%s' "$1" | tr -d '"\\' | tr '\n\t' '  ')
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}' "$reason"
  exit 0
}

# Anchored create invocation, matched to end of command...
inv=$(printf '%s' "$cmd" | grep -oE '(^|&&|;|\|)[[:space:]]*gh[[:space:]]+(pr|issue)[[:space:]]+create\b.*' | head -1)
[ -z "$inv" ] && exit 0
inv=$(printf '%s' "$inv" | sed -E 's/^(&&|;|\|)?[[:space:]]*//')
# ...then bounded to its own pipeline segment for flag parsing.
seg=$(printf '%s' "$inv" | sed -E 's/(&&|;|\|).*//')
kind=$(printf '%s' "$seg" | sed -nE 's/^gh[[:space:]]+(pr|issue)[[:space:]].*/\1/p')

# G3 -- external repo target on a create: deny by default, override path stated.
repo=$(printf '%s' "$seg" | grep -oE '(^|[[:space:]])(--repo|-R)(=|[[:space:]]+)[^[:space:]]+' | head -1 \
  | sed -E 's/^[[:space:]]*(--repo|-R)(=|[[:space:]]+)//')
if [ -n "$repo" ]; then
  case "$repo" in
    one21labs/*) : ;;
    *) deny "Denied by default: gh $kind create targets $repo, outside one21labs/* -- external publication requires per-item owner approval of the exact text (CLAUDE.md). Override path: the owner runs this command themselves, or adds a one-off permission allow for this exact command. Leave the draft in the internal issue instead." ;;
  esac
fi

# G1 -- body must come via --body-file/-F.
bf=$(printf '%s' "$seg" | grep -oE '(^|[[:space:]])(--body-file|-F)(=|[[:space:]]+)[^[:space:]]+' | head -1 \
  | sed -E 's/^[[:space:]]*(--body-file|-F)(=|[[:space:]]+)//')
if [ -z "$bf" ]; then
  if printf '%s' "$seg" | grep -qE '(^|[[:space:]])(--body|-b)(=|[[:space:]]|$)'; then
    deny "Denied: pass the body via --body-file <file> (quoting-safe on PS 5.1, and lets this hook verify the disclosure + Retrospective lines before anything is published). Write the body to a file first."
  fi
  exit 0   # no body flags at all: let gh open its editor / error on its own
fi

# G2 -- body content checks. Relative paths resolve against the project root (the Bash tool's
# cwd); substring matches are CRLF-safe (neither phrase spans a line ending).
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null
body=$(cat "$bf" 2>/dev/null) || exit 0
case "$body" in
  *'Disclosure: written by Claude'*) : ;;
  *) deny "Denied: body file $bf is missing the Claude authorship disclosure line (CLAUDE.md: required on every issue and PR Claude writes, at creation time). Append: *Disclosure: written by Claude (Claude Code) under the direction of the repo owner.*" ;;
esac
if [ "$kind" = "pr" ]; then
  case "$body" in
    *'Retrospective:'*) : ;;
    *) deny "Denied: PR body file $bf is missing the required Retrospective: line (ADR 0030). Run /retrospect on this branch, then add a line: Retrospective: run | unavailable | skipped-<reason>." ;;
  esac
fi
exit 0
