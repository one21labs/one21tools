#!/usr/bin/env bash
# PreToolUse hook (matcher: Bash) for the pdca-workflow plugin. DENIES a Bash command that
# invokes adr-lint.mjs -- the only gate script this plugin ships -- and pipes its output through
# a filter: a pipe reports the filter's exit status, not the gate's, so gate failures pass
# silently. `||` and `&&` are allowed (they don't touch the exit code); a true `|`
# after the invocation is always denied, including into `tee`/`cat` -- those still swallow the
# exit code without `set -o pipefail`, so there is no carve-out for them.
#
# INVOCATION ANCHOR (fix for a prior false-positive/false-negative pair): a bare substring match
# on the gate's filename is wrong in both directions -- `grep adr-lint.mjs file | head` is not an
# invocation (denying it would be a false positive), and the gate name can appear at any position
# after an interpreter with an arbitrary path prefix (`node pdca-workflow/scripts/adr-lint.mjs`).
# So a "gate" only counts when it is the argument to `node`/`python`/`python3` as a whole word,
# optionally behind a path ending in `/`:
#   \b(node|python3?)[[:space:]]+([A-Za-z0-9._/-]*/)?<gate>\b
# PIPE CHECK: once an invocation is found, scan from that match to the end of the command for the
# first top-level operator. `&&` and `||` are folded to non-`|` markers first (so `||` can never
# be mistaken for a piping `|`); whatever operator is left-most among {`;`, folded-&&, folded-||,
# `|`} decides: only a bare `|` denies. This bounds the check to the gate's OWN segment -- a pipe
# in a later, `&&`/`;`-separated segment does not deny (that pipe never touches the gate's exit
# code).
#
# ACCEPTED LIMITATIONS: only checks the FIRST occurrence of the gate name per command (a second,
# later invocation of the same gate name in one chained command is not separately checked -- rare
# in practice, and the composite command still gets caught by whichever pipe follows the first
# hit's segment in the common case). No jq (git-bash safe). Fails OPEN on malformed/empty stdin.
input=$(cat)
cmd=$(printf '%s' "$input" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\(.*\)/\1/p')
[ -z "$cmd" ] && exit 0

# The only gate script pdca-workflow ships (pdca-workflow/scripts/adr-lint.mjs). Repo-specific
# gate scripts (check-restatement.mjs, validate.py, check-workflow.mjs, ...) are guarded by the
# consuming repo's OWN gate-pipe-guard.sh (see repo-hooks/), not here -- a generic plugin cannot
# know a consumer's repo-local script names.
GATES="adr-lint.mjs"

for gate in $GATES; do
  esc_gate=$(printf '%s' "$gate" | sed 's/\./\\./g')
  invoke_re="\\b(node|python3?)[[:space:]]+([A-Za-z0-9._/-]*/)?${esc_gate}\\b"
  match=$(printf '%s' "$cmd" | grep -oE "${invoke_re}.*")
  [ -z "$match" ] && continue

  # Fold && / || to non-pipe markers, then find the first remaining top-level operator.
  folded=$(printf '%s' "$match" | sed -e 's/&&/@@AND@@/g' -e 's/||/@@OR@@/g')
  first_op=$(printf '%s' "$folded" | grep -oE '@@AND@@|@@OR@@|;|\|' | head -1)

  if [ "$first_op" = "|" ]; then
    reason="Denied: $gate is a gate; piping it hides its exit code (a pipe reports the filter's exit status, not the gate's). Run it bare and read the output directly."
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}' "$reason"
    exit 0
  fi
done
exit 0
