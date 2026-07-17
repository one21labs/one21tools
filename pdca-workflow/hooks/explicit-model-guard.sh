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
input=$(cat)
[ -d "${CLAUDE_PROJECT_DIR:-.}/docs/pdca" ] || exit 0
scope=$(printf '%s' "$input" | sed -n 's/.*\("tool_input".*\)/\1/p')
[ -z "$scope" ] && exit 0

has_model=$(printf '%s' "$scope" | grep -c '"model"[[:space:]]*:')
subagent_type=$(printf '%s' "$scope" | sed -n 's/.*"subagent_type"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')

if [ "$has_model" -eq 0 ] && { [ -z "$subagent_type" ] || [ "$subagent_type" = "general-purpose" ]; }; then
  reason='Denied: no explicit model, and subagent_type is absent or general-purpose -- this call would silently inherit the parent session model (ADR 0040). Re-issue the call with model set explicitly to haiku, sonnet, or opus, matched to the task: haiku for mechanical/deterministic execution, sonnet for judgment-execution, opus for planning. To target a defined frontmatter agent instead, set subagent_type to its name.'
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}' "$reason"
fi
exit 0
