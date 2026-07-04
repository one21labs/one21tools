#!/usr/bin/env bash
# PostToolUse hook (matcher: Bash) for the pdca-workflow plugin.
# When a `gh pr create` command runs, inject a NON-BLOCKING reminder to run /retrospect so
# process improvements land in the still-open PR before it merges. Deterministic, zero agent
# spend (the human/Claude still runs /retrospect). /retrospect never calls `gh pr create`, so
# this can't re-enter. The Bash command arrives as tool_input.command in the stdin JSON: first
# ISOLATE the command value (the text after `"command":` up to the next raw quote), then
# substring-match it — a prefixed/chained invocation (`cd x && gh pr create`) still fires,
# while a command merely QUOTING the phrase (`echo "gh pr create"`) does not: its escaped \"
# ends the extraction before the phrase. Accepted limitation: any quote earlier in the command
# (`git commit -m "x" && gh pr create`) also ends extraction early — a miss, never a false
# fire. No jq dependency (git-bash safe).
input=$(cat)
cmd=$(printf '%s' "$input" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
case "$cmd" in
  *'gh pr create'*)
    printf '%s' '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"A PR was just created. Run /retrospect on this branch (git range main..HEAD) before it merges so process improvements land in the PR. Skip only if you already ran it on this branch."}}'
    ;;
esac
exit 0
