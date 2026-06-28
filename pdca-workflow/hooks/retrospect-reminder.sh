#!/usr/bin/env bash
# PostToolUse hook (matcher: Bash) for the pdca-workflow plugin.
# When a `gh pr create` command runs, inject a NON-BLOCKING reminder to run /retrospect so
# process improvements land in the still-open PR before it merges. Deterministic, zero agent
# spend (the human/Claude still runs /retrospect). /retrospect never calls `gh pr create`, so
# this can't re-enter. The Bash command arrives as tool_input.command in the stdin JSON;
# matching the command VALUE (not the whole input) avoids false positives on commands that
# merely mention the string (e.g. `echo "gh pr create"`); no jq dependency (git-bash safe).
input=$(cat)
case "$input" in
  *'"command":"gh pr create'*|*'"command": "gh pr create'*)
    printf '%s' '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"A PR was just created. Run /retrospect on this branch (git range main..HEAD) before it merges so process improvements land in the PR. Skip only if you already ran it on this branch."}}'
    ;;
esac
exit 0
