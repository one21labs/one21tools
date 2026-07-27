#!/usr/bin/env bash
# PreToolUse hook (matcher: Bash) for THIS REPO's .claude/settings.json: refuse a git command that
# DISCARDS uncommitted work, when there is uncommitted work to discard.
#
# THE SCAR, 2026-07-27. Mid-session the agent ran `git reset --hard HEAD~1` to undo a throwaway
# probe commit. About 60 lines of unstaged work were sitting in the tree -- a hook restructure
# closing four fail-opens a cross-family review had just found. `--hard` is the ONE reset variant
# that discards the working tree; `--soft` and plain `reset` both undo the commit and keep
# everything. The destructive form was reached for because it guarantees a known state, without
# first running `git status` to see what else was there.
#
# THE SECOND SCAR, same day. The guard written in response did its parsing in bash: `sed` to pull
# the command out of the JSON, one regex to classify it. A cross-family review found 27 ways past
# that in one pass, and an internal lane then destroyed a real file in a fixture to prove three of
# them. `sh -c 'git reset --hard'` walked past the anchor; `echo "note" && git reset --hard` broke
# the sed extraction on the quote and was allowed; `cd /other && git reset --hard` was graded
# against the wrong tree entirely. So THE DECIDING MOVED OUT OF BASH -- lib/destructive_git.py
# owns parsing and the decision, takes injected git state, and is unit-tested against every one
# of those inputs. This file is now I/O: read stdin, hand it over, print what comes back.
#
# THE PREDICATE IS MECHANICAL, never semantic: "is the worktree this command will actually touch
# dirty" is a fact git answers, not a judgement about whether this reset is the risky kind. Every
# guard in this repo keyed on the agent classifying its own situation has been evaded; the ones
# keyed on a countable fact have not.
#
# A CLEAN TREE IS NOT BLOCKED, and neither is a `stash drop` with an empty stash, nor a
# `clean --dry-run`. A guard that cries wolf is a guard people route around, and a routed-around
# guard protects nothing.
#
# liveness: per-event-exempt -- a deny fires only on a destructive command against a dirty tree,
# which may legitimately never occur in a window (ADR 0086 (b)). Grammar: scripts/check-gate-tests.mjs.
# canary: {"event":"PreToolUse","tool":"Bash","git":"dirty","stdin":{"tool_name":"Bash","tool_input":{"command":"git reset --hard HEAD~1"}},"expect":{"deny":true}}
# canary: {"event":"PreToolUse","tool":"Bash","git":"dirty","stdin":{"tool_name":"Bash","tool_input":{"command":"sh -c 'git reset --hard'"}},"expect":{"deny":true}}
# Path skeleton and gate-hit telemetry: lib/hook-lib.sh owns both. A missing lib exits 0.
. "$(dirname "${BASH_SOURCE[0]}")/../../pdca-workflow/hooks/lib/hook-lib.sh" 2>/dev/null || exit 0

DECIDER="$(dirname "${BASH_SOURCE[0]}")/lib/destructive_git.py"
input=$(cat)

# Absent machinery fails OPEN, like every sibling guard: a missing interpreter must not become a
# blanket block on git. Malformed INPUT is the opposite case and fails closed -- the decider
# scans the raw text rather than reading an unparseable payload as "nothing to see".
[ -f "$DECIDER" ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
command -v git >/dev/null 2>&1 || exit 0

# Cheap pre-filter so the common command never pays for a python start.
printf '%s' "$input" | grep -q 'git' || exit 0

verdict=$(printf '%s' "$input" | python3 "$DECIDER" "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null)
[ -z "$verdict" ] && exit 0

hook_gate_hit destructive-git-guard "$(printf '%s' "$input" | tr -d '\n' | cut -c1-60)"
printf '%s' "$verdict"
exit 0
