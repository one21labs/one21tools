#!/usr/bin/env bash
# PreToolUse hook (matcher: Bash) for THIS REPO's .claude/settings.json: DENY running a
# repo-local gate script piped into a filter, which hides its exit code (CLAUDE.md: "Never pipe
# a gate through a filter that hides its exit code"). `||` and `&&` are allowed; a true `|` after
# the invocation is always denied -- no tee/cat carve-out, since those also swallow the exit code
# without `set -o pipefail`.
#
# SCOPE / SSoT NOTE: adr-lint.mjs is EXCLUDED from GATES below. It's the one gate script the
# pdca-workflow plugin ships, and the plugin's own gate-pipe-guard.sh (wired via its hooks.json,
# active here because pdca-workflow is enabled in .claude/settings.json) already guards it. Also
# listing it here would run the SAME decision twice on the same command -- duplicated gate logic,
# cut on sight per CLAUDE.md muda rules. This script owns only the gates that are repo-local
# tooling: scripts/*.mjs and skills/building-skills/scripts/{validate.py,run_eval.py} (that
# skill's own dev-skills plugin ships no gate-pipe guard of its own).
#
# INVOCATION ANCHOR / PIPE CHECK: identical decision logic to the plugin's gate-pipe-guard.sh --
# see that file's header for the full rationale (word-boundary interpreter+gate match; &&/||
# folded before the first-operator scan so only a bare `|` denies). Duplicated here rather than
# sourced from the plugin's copy: Claude Code hooks are invoked as single standalone files with no
# shared-lib convention in this repo, and a repo hook that reaches into a plugin's installed path
# to source shell code would be a more fragile coupling than ~15 lines of proven regex logic
# repeated once. Revisit if a third gate-pipe consumer appears.
#
# ACCEPTED LIMITATIONS: only checks the FIRST occurrence of a given gate name per command. No jq
# (git-bash safe). Fails OPEN on malformed/empty stdin.
input=$(cat)
cmd=$(printf '%s' "$input" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\(.*\)/\1/p')
[ -z "$cmd" ] && exit 0

# Repo-local gate scripts NOT shipped by any plugin (ADR 0046 "instance tooling"), plus the
# dev-skills-adjacent scripts that ship no gate-pipe guard of their own.
GATES="validate.py check-restatement.mjs check-workflow.mjs check-pr-body.mjs run_eval.py"

for gate in $GATES; do
  esc_gate=$(printf '%s' "$gate" | sed 's/\./\\./g')
  invoke_re="\\b(node|python3?)[[:space:]]+([A-Za-z0-9._/-]*/)?${esc_gate}\\b"
  match=$(printf '%s' "$cmd" | grep -oE "${invoke_re}.*")
  [ -z "$match" ] && continue

  folded=$(printf '%s' "$match" | sed -e 's/&&/@@AND@@/g' -e 's/||/@@OR@@/g')
  first_op=$(printf '%s' "$folded" | grep -oE '@@AND@@|@@OR@@|;|\|' | head -1)

  if [ "$first_op" = "|" ]; then
    reason="Denied: $gate is a gate; piping it hides its exit code (CLAUDE.md: never pipe a gate through a filter). Run it bare and read the output directly."
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}' "$reason"
    exit 0
  fi
done
exit 0
