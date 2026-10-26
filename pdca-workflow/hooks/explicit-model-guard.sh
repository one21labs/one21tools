#!/usr/bin/env bash
# PreToolUse hook (matcher: Agent|Task) for the pdca-workflow plugin (ADR 0040).
# DEFAULTS TO SONNET an Agent/Task call that has no explicit `model` AND targets an unmodeled
# surface (`subagent_type` absent or "general-purpose") -- the case that would silently inherit
# the PARENT SESSION model (owner, 26-Oct-2026: "Sonnet must be default for all users of this
# plugin"). It rewrites the call with model "sonnet" (updatedInput) instead of denying it, so no
# round-trip is wasted; a call that names haiku or opus keeps it. If node cannot rebuild the
# input, it falls back to the old deny. A named frontmatter-modeled agent or a fork
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
# liveness: per-event-exempt -- a default fires only on an unmodeled general-purpose/absent-type
# call, which may legitimately never occur in a window (ADR 0086 (b)). Canaries: the two
# defaulted input shapes, one per tool name the matcher covers. Declaration grammar home: the
# grammar is inert since 2026-07-27 (#311) — its runner was deleted.
# canary: {"event":"PreToolUse","tool":"Agent","stdin":{"tool_name":"Agent","tool_input":{"prompt":"do the thing"}},"expect":{"model":"sonnet"}}
# canary: {"event":"PreToolUse","tool":"Task","stdin":{"tool_name":"Task","tool_input":{"subagent_type":"general-purpose","prompt":"do the thing"}},"expect":{"model":"sonnet"}}
input=$(cat)
[ -d "${CLAUDE_PROJECT_DIR:-.}/docs/pdca" ] || exit 0
scope=$(printf '%s' "$input" | sed -n 's/.*\("tool_input".*\)/\1/p')
[ -z "$scope" ] && exit 0

has_model=$(printf '%s' "$scope" | grep -c '"model"[[:space:]]*:')
subagent_type=$(printf '%s' "$scope" | sed -n 's/.*"subagent_type"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')

if [ "$has_model" -eq 0 ] && { [ -z "$subagent_type" ] || [ "$subagent_type" = "general-purpose" ]; }; then
  # Gate-hit telemetry (ADR 0080): observability only, never in the failure path — the output
  # below prints regardless; docs/pdca existence already established above (ADR 0071 marker),
  # never mkdir. Read by the retrospect agent, when present.
  { printf '%s gate-hit explicit-model-guard %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${subagent_type:-unset}" >> "${CLAUDE_PROJECT_DIR:-.}/docs/pdca/gate-hits.txt"; } 2>/dev/null
  updated=$(printf '%s' "$input" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const t=JSON.parse(s).tool_input;t.model="sonnet";process.stdout.write(JSON.stringify(t))})' 2>/dev/null)
  if [ -n "$updated" ]; then
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","permissionDecisionReason":"%s","updatedInput":%s}}' 'No explicit model on a general-purpose call: defaulted to sonnet (pdca-workflow). Set model to haiku or opus to choose another tier.' "$updated"
    exit 0
  fi
  reason='Denied: no explicit model, and subagent_type is absent or general-purpose -- this call would silently inherit the parent session model (ADR 0040). Re-issue the call with model set explicitly: sonnet by default, haiku for mechanical/deterministic execution, opus only for planning. To target a defined frontmatter agent instead, set subagent_type to its name.'
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}' "$reason"
fi
exit 0
