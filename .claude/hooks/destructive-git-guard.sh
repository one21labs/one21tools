#!/usr/bin/env bash
# PreToolUse hook (matcher: Bash) for THIS REPO's .claude/settings.json: refuse a git command that
# DISCARDS uncommitted work, when there is uncommitted work to discard.
#
# THE SCAR, 2026-07-27. Mid-session the agent ran `git reset --hard HEAD~1` to undo a throwaway
# probe commit. About 60 lines of unstaged work were sitting in the tree -- a hook restructure
# closing four fail-opens a cross-family review had just found. `--hard` is the ONE reset variant
# that discards the working tree; `--soft` and plain `reset` both undo the commit and keep
# everything. The destructive form was reached for because it guarantees a known state, without
# first running `git status` to see what else was there. The work had to be redone from the review
# output. Had it not been noticed, the commit would have shipped claiming fixes it no longer
# contained -- CLAUDE.md's "before deleting or overwriting, look at the target", lost to habit.
#
# THE PREDICATE IS MECHANICAL, never semantic: "is the tree dirty" is a fact `git status` answers,
# not a judgement about whether this particular reset is the risky kind. Every guard in this repo
# that keyed on the agent classifying its own situation has been evaded by the agent classifying
# it differently; the ones that keyed on a countable fact never have.
#
# A CLEAN TREE IS NOT BLOCKED. `git reset --hard` with nothing uncommitted destroys nothing
# recoverable (the commits stay in the reflog), and blocking it would deny a legitimate everyday
# move -- a guard that cries wolf teaches people to route around it.
#
# COMMANDS COVERED: reset --hard, checkout/restore that overwrite files, clean -f/-fd, and
# stash drop/clear. All of them can silently take uncommitted work.
#
# liveness: per-event-exempt -- a deny fires only on a destructive command against a dirty tree,
# which may legitimately never occur in a window (ADR 0086 (b)). Grammar: scripts/check-gate-tests.mjs.
# canary: {"event":"PreToolUse","tool":"Bash","git":"dirty","stdin":{"tool_name":"Bash","tool_input":{"command":"git reset --hard HEAD~1"}},"expect":{"deny":true}}
# canary: {"event":"PreToolUse","tool":"Bash","git":"dirty","stdin":{"tool_name":"Bash","tool_input":{"command":"git clean -fd"}},"expect":{"deny":true}}
# Path skeleton and gate-hit telemetry: lib/hook-lib.sh owns both. A missing lib exits 0.
. "$(dirname "${BASH_SOURCE[0]}")/../../pdca-workflow/hooks/lib/hook-lib.sh" 2>/dev/null || exit 0

input=$(cat)
cmd=$(printf '%s' "$input" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -z "$cmd" ] && exit 0

# Does the command discard uncommitted work? Anchored at a command-word position so a mention
# inside a quoted string or a grep pattern is not an invocation.
printf '%s' "$cmd" | grep -qE '(^|&&|;|\|)[[:space:]]*git[[:space:]]+(reset[[:space:]]+(--hard|--merge)|clean[[:space:]]+(-[a-zA-Z]*f|--force)|checkout[[:space:]]+(--\.|-f|--force)|restore[[:space:]]+.*--worktree|stash[[:space:]]+(drop|clear))' || exit 0

root="${CLAUDE_PROJECT_DIR:-.}"
cd "$root" 2>/dev/null || exit 0
command -v git >/dev/null 2>&1 || exit 0            # no git: cannot know, must not block

# The tree's actual state, not a guess. `--porcelain` lists staged AND unstaged AND untracked.
# Untracked counts: `git clean -fd` deletes exactly those, and a new file nobody has added yet is
# the most common thing to lose.
dirty=$(git status --porcelain 2>/dev/null | head -40)
[ -z "$dirty" ] && exit 0                            # clean tree: nothing to lose, allow

count=$(printf '%s\n' "$dirty" | grep -c .)
sample=$(printf '%s\n' "$dirty" | head -5 | tr '\n' ' ' | tr -d '"\\')
hook_gate_hit destructive-git-guard "$(printf '%s' "$cmd" | cut -c1-40)"
reason="Denied: this discards uncommitted work and the tree is NOT clean -- ${count} path(s) would be lost, e.g. ${sample}. If the goal is to undo a COMMIT, use 'git reset --soft HEAD~1' (keeps everything staged) or 'git reset HEAD~1' (keeps the working tree); both undo the commit without touching your files. If you genuinely mean to discard, commit or stash first so it is recoverable, then re-run. Scar: 60 lines of a security-hook fix were lost this way on 2026-07-27, and the commit that followed would have claimed fixes it no longer contained."
reason=$(printf '%s' "$reason" | tr -d '"\\' | tr '\n\t' '  ')
printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}' "$reason"
exit 0
