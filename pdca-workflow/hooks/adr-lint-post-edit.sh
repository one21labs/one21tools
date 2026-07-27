#!/usr/bin/env bash
# PostToolUse hook (matcher: Edit|Write) for the pdca-workflow plugin: run adr-lint.mjs on the
# corpus it owns whenever an edit touches one of its inputs -- the ADR corpus itself
# (docs/decisions/*.md), the root CLAUDE.md, an agent prompt (pdca-workflow/agents/*.md or
# .claude/agents/*.md), or a manifest (plugin.json / marketplace.json, which adr-lint cross-checks
# for drift). Detect-at-creation rung of the latency ladder, same shape as the repo's
# repo-local post-edit hooks. On gate failure: exit 2 with the gate's stderr (fed back to Claude
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
#
# liveness: per-event-exempt -- the observable fire (exit 2 + stderr) is contingent on a
# FAILING lint run, which may legitimately never occur in a window (ADR 0086 (b)). Canaries:
# one per routing case arm, each against a fixture corpus the lint must fail on. Declaration
# grammar: inert since 2026-07-27 (#311) — the runner that executed these was deleted.
# canary: {"event":"PostToolUse","tool":"Edit","env":{"CLAUDE_PLUGIN_ROOT":"__REPO__/pdca-workflow"},"files":{"docs/decisions/0001-bad.md":"not an adr at all"},"stdin":{"tool_name":"Edit","tool_input":{"file_path":"__FIXTURE__/docs/decisions/0001-bad.md"}},"expect":{"exit":2}}
# canary: {"event":"PostToolUse","tool":"Edit","env":{"CLAUDE_PLUGIN_ROOT":"__REPO__/pdca-workflow"},"files":{"docs/decisions/0001-bad.md":"not an adr at all"},"stdin":{"tool_name":"Edit","tool_input":{"file_path":"__FIXTURE__/CLAUDE.md"}},"expect":{"exit":2}}
# canary: {"event":"PostToolUse","tool":"Edit","env":{"CLAUDE_PLUGIN_ROOT":"__REPO__/pdca-workflow"},"files":{"docs/decisions/0001-bad.md":"not an adr at all"},"stdin":{"tool_name":"Edit","tool_input":{"file_path":"__FIXTURE__/pdca-workflow/agents/pm.md"}},"expect":{"exit":2}}
# canary: {"event":"PostToolUse","tool":"Edit","env":{"CLAUDE_PLUGIN_ROOT":"__REPO__/pdca-workflow"},"files":{"docs/decisions/0001-bad.md":"not an adr at all"},"stdin":{"tool_name":"Edit","tool_input":{"file_path":"__FIXTURE__/.claude-plugin/plugin.json"}},"expect":{"exit":2}}
# Path skeleton + gate-hit telemetry, one home for every file_path hook (lib/hook-lib.sh).
# Sourced script-relative so it resolves from the installed plugin cache and under the canary
# runner's throwaway project dir alike.
. "$(dirname "${BASH_SOURCE[0]}")/lib/hook-lib.sh" 2>/dev/null || exit 0
input=$(cat)
fp=$(hook_fp "$input")   # forward slashes, absolute — the case arms below need both
[ -z "$fp" ] && exit 0

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
  hook_gate_hit adr-lint "$fp"
  printf '%s\n' "GATE FAILED (fix now, before continuing): $out" >&2
  exit 2
}
exit 0
