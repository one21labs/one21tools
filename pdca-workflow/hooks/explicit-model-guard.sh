#!/usr/bin/env bash
# PreToolUse hook (matcher: Agent|Task) for the pdca-workflow plugin (ADR 0040 item 6).
# DENIES an Agent/Task call that has no explicit `model` AND targets an unmodeled surface
# (`subagent_type` absent or "general-purpose") -- the case that silently inherits the PARENT
# SESSION model instead of a per-call tier. A named frontmatter-modeled agent or a fork
# (subagent_type set to anything else) is carved out: it inherits its own tier by design.
#
# tool_input.prompt is free text that can contain the words "model"/"subagent_type", so a
# bare-word search on raw stdin is wrong. This matches the JSON KEY PATTERN `"model"[[:space:]]*:`
# instead: an unescaped `"model":` byte sequence can only come from a real JSON key -- literal
# `"model":`-looking text inside a string VALUE is escaped by the encoder to `\"model\":`, which
# lacks the contiguous bytes this pattern requires. Scoped to the substring from "tool_input"
# onward so an unrelated top-level field can't match. No jq (git-bash safe). Fails OPEN (allows)
# on malformed/empty stdin or a missing tool_input marker -- a broken hook must never block
# every agent launch.
#
# FIRING SCOPE (ADR 0071): fires only in a project that adopted the PDCA practice, marked by the
# docs/pdca/ dir (scaffolded by /pdca-init). Everywhere else this is a no-op -- a session-wide
# install must not impose tier discipline on repos that never opted in (ADR 0050). Stdin is
# drained BEFORE the marker check so the harness never sees a broken pipe.
#
# liveness: per-event-exempt -- a deny fires only on an unmodeled general-purpose/absent-type
# call, which may legitimately never occur in a window (ADR 0086 (b)). Canaries: the two
# denied input shapes, one per tool name the matcher covers. Declaration grammar home: the
# consumer repo's check-gate-tests (this repo: scripts/check-gate-tests.mjs).
# canary: {"event":"PreToolUse","tool":"Agent","stdin":{"tool_name":"Agent","tool_input":{"prompt":"do the thing"}},"expect":{"deny":true}}
# canary: {"event":"PreToolUse","tool":"Task","stdin":{"tool_name":"Task","tool_input":{"subagent_type":"general-purpose","prompt":"do the thing"}},"expect":{"deny":true}}
# Gate-hit telemetry has one home (lib/hook-lib.sh). Sourced script-relative, not via
# CLAUDE_PROJECT_DIR: the canary runner executes hooks from their real repo path against a
# throwaway fixture project. A missing lib exits 0 — telemetry never blocks a guard.
. "$(dirname "${BASH_SOURCE[0]}")/lib/hook-lib.sh" 2>/dev/null || exit 0

input=$(cat)
[ -d "${CLAUDE_PROJECT_DIR:-.}/docs/pdca" ] || exit 0
scope=$(printf '%s' "$input" | sed -n 's/.*\("tool_input".*\)/\1/p')
[ -z "$scope" ] && exit 0

# PRESENCE IS NOT A VALUE. Counting the `"model":` KEY let `"model": ""` and `"model": null`
# satisfy the guard while inheriting the parent model anyway — the same shape as a value-less
# flag coercing to NaN and skipping the check. Require a non-empty quoted string.
has_model=$(printf '%s' "$scope" | grep -c '"model"[[:space:]]*:[[:space:]]*"[^"]\{1,\}"')
subagent_type=$(printf '%s' "$scope" | sed -n 's/.*"subagent_type"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')

if [ "$has_model" -eq 0 ] && { [ -z "$subagent_type" ] || [ "$subagent_type" = "general-purpose" ]; }; then
  # Gate-hit telemetry (ADR 0080): observability only, never in the failure path — the deny below
  # prints regardless. lib/hook-lib.sh owns the line format, the field scrub and the ADR 0071
  # marker check; a copy here is the mirror 83e43ef deleted three of.
  hook_gate_hit explicit-model-guard "${subagent_type:-unset}"
  reason='Denied: no explicit model, and subagent_type is absent or general-purpose -- this call would silently inherit the parent session model (ADR 0040). Re-issue the call with model set explicitly to haiku, sonnet, or opus, matched to the task: haiku for mechanical/deterministic execution, sonnet for judgment-execution, opus for planning. To target a defined frontmatter agent instead, set subagent_type to its name.'
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}' "$reason"
fi
exit 0
