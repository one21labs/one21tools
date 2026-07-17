#!/usr/bin/env bash
# PostToolUse hook (matcher: Bash) for THIS REPO's .claude/settings.json (ADR 0047 as amended,
# predicate revised diff-only by ADR 0072): when `git diff` runs a TWO-dot range against main
# (`main..X` / `origin/main..X`), inject a NON-BLOCKING additionalContext warning -- for DIFF,
# two-dot is tip-to-tip and shows a branch merely behind main as reverting main's content; PR
# previews need three-dot (origin/main...branch), per CLAUDE.md Shipping rules. NEVER denies.
# Also appends one counted line to the shared session log (docs/pdca/session-log.txt -- location
# owned and documented by the plugin's spawn-log.sh header; same single-line `>>` append, atomic
# enough per that header) so the promotion-to-deny window is measurable from git: if the count
# stays zero the warn rung suffices; if it grows, promote.
#
# FIRE CONDITIONS: the command must (a) invoke `git diff` -- and ONLY diff: the trap is
# diff-specific. `git log A..B` / `git rev-list A..B` two-dot is the CORRECT
# commits-ahead-of-A query (three-dot there is symmetric difference, pulling in main-only
# commits -- the opposite of what a PR commit listing wants), so warning on log/rev-list taught
# the wrong habit and polluted the promotion count (ADR 0072) -- and (b) contain `main..` or
# `origin/main..` NOT followed by a third dot, with a token boundary before `main` (so
# `notmain..x` never fires). Three-dot `main...X` cannot match: the literal `main..` is at one
# fixed offset and the next char there is `.`, rejected by the final [^.] class.
#
# ACCEPTED LIMITATIONS, per spec scope: (1) main on the RIGHT (`X..main`) is not matched -- ADR
# 0047's named trap is the main-on-left preview form. (2) `upstream/main..X` (a non-origin
# remote) is not matched: the boundary class excludes `/` before a bare `main`, which is what
# keeps arbitrary `<anything>/main` refs out; origin/ is special-cased as the one named remote.
# (3) A command merely QUOTING the range (`echo "main..x"`) does not fire: the house [^"]* sed
# extraction ends at the first escaped quote (\" contains "), same accepted behavior as
# retrospect-reminder.sh -- a genuine quoted ARGUMENT (`git log "main..x"`) is therefore also a
# miss, never a false fire. Fails OPEN (exit 0, no output) on malformed/empty stdin.
input=$(cat)
cmd=$(printf '%s' "$input" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -z "$cmd" ] && exit 0

printf '%s' "$cmd" | grep -qE '\bgit\b.*\bdiff\b' || exit 0
range=$(printf '%s' "$cmd" | grep -oE '(^|[^[:alnum:]_/.-])(origin/)?main\.\.([^.]|$)' | head -1)
[ -z "$range" ] && exit 0

root="${CLAUDE_PROJECT_DIR:-.}"
mkdir -p "$root/docs/pdca" 2>/dev/null && \
  printf '%s two-dot-main %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(printf '%s' "$range" | tr -d ' \t')" >> "$root/docs/pdca/session-log.txt" 2>/dev/null

printf '%s' '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"two-dot against main shows tip-to-tip, use three-dot (origin/main...branch) for PR previews -- CLAUDE.md"}}'
exit 0
