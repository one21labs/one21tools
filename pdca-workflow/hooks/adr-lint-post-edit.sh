#!/usr/bin/env bash
# PostToolUse hook (matcher: Edit|Write) for the pdca-workflow plugin: run adr-lint.mjs on the
# corpus it owns whenever an edit touches one of its inputs -- the ADR corpus itself
# (docs/decisions/*.md), the root CLAUDE.md, an agent prompt (pdca-workflow/agents/*.md or
# .claude/agents/*.md), or a manifest (plugin.json / marketplace.json, which adr-lint cross-checks
# for drift). Detect-at-creation rung of the latency ladder, same shape as the repo's
# post-edit-gate.sh. On gate failure: exit 2 with the gate's stderr (fed back to Claude
# in-session). No jq (git-bash safe). Fails OPEN (exit 0) on malformed/empty stdin, a missing
# file_path, or an unenterable project dir -- a broken hook must never block edits.
#
# GRACEFUL DEGRADATION (required for a generic plugin hook): adr-lint.mjs itself hard-exits(2)
# only when its PRIMARY argument dir (docs/decisions) is missing -- every other input it reads
# (CLAUDE.md, the agent dirs, the manifests) is already ENOENT-tolerant inside the script. A
# consumer project that doesn't use this repo's ADR workflow has no docs/decisions dir at all, so
# running the gate there would hard-fail on every matching edit for a reason the consumer can't
# fix. This hook checks for docs/decisions BEFORE invoking adr-lint.mjs and exits 0 fast if it's
# absent -- the plugin is then a no-op for that consumer, not a blocker.
#
# ACCEPTED LIMITATION: adr-lint.mjs's oversizeDocs() check is hardcoded to the repo-root-relative
# path "CLAUDE.md" (char-budget.mjs DOC_BUDGETS), so a nested CLAUDE.md match here (any depth, via
# `*/CLAUDE.md`) re-runs the SAME root-CLAUDE.md check rather than checking the nested file --
# harmless over-trigger (wastes one run), not a false negative on the file that was actually
# edited (there is no per-file budget for a nested CLAUDE.md to miss).
input=$(cat)
fp=$(printf '%s' "$input" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -z "$fp" ] && exit 0
# Normalize JSON-escaped Windows backslashes to forward slashes for case matching.
fp=$(printf '%s' "$fp" | sed 's/\\\\/\//g; s/\\/\//g')

root="${CLAUDE_PROJECT_DIR:-.}"
cd "$root" || exit 0   # adr-lint.mjs's checks resolve relative to CWD; never run it elsewhere.

case "$fp" in
  */docs/decisions/*.md|*/CLAUDE.md|*/agents/*.md|*plugin.json|*marketplace.json) : ;;
  *) exit 0 ;;
esac

# FIRING SCOPE (ADR 0071): only a project that adopted the PDCA practice (docs/pdca/ marker,
# scaffolded by /pdca-init) gets this gate -- a generic docs/decisions ADR corpus that never
# opted in must not be linted with this plugin's house rules (ADR 0050).
[ -d "$root/docs/pdca" ] || exit 0
# Degrade gracefully: a consumer with no ADR corpus has nothing for this hook to gate.
[ -d "$root/docs/decisions" ] || exit 0

out=$(node "${CLAUDE_PLUGIN_ROOT}/scripts/adr-lint.mjs" "$root/docs/decisions" 2>&1) || {
  printf '%s\n' "GATE FAILED (fix now, before continuing): $out" >&2
  exit 2
}
exit 0
