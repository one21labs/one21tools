#!/usr/bin/env bash
# PostToolUse hook (matcher: Edit|Write) for THIS REPO's .claude/settings.json: run the matching
# deterministic gate on the file that was just edited, for the gates the pdca-workflow PLUGIN
# does NOT already cover. Detect-at-creation rung of the latency ladder. On gate failure: exit 2
# with the gate output on stderr (fed back to Claude in-session). No jq (git-bash safe). Fails
# OPEN on malformed stdin -- a broken hook must never block edits.
#
# SCOPE / SSoT NOTE: ADR corpus + CLAUDE.md + agents + manifest-drift linting (adr-lint.mjs) is
# handled by the pdca-workflow plugin's own adr-lint-post-edit.sh, which fires automatically
# because this repo has pdca-workflow enabled (.claude/settings.json enabledPlugins). Routing
# those same paths through a second, repo-local adr-lint invocation here would be duplicated gate
# logic (two hooks racing to lint the same corpus on the same edit) -- cut on sight per CLAUDE.md
# muda rules. This script only owns the gates that are repo-local tooling, not shipped in any
# plugin (skills/building-skills/scripts/validate.py and scripts/*.mjs live in scripts/ or a
# sibling plugin, per ADR 0046's "instance tooling" distinction).
#
# check-restatement SCOPING (required fix): check-restatement.mjs takes no --file argument -- it
# always full-tree-scans for cross-file restatement (ADR 0046). Running a full-corpus scan on
# EVERY .md edit is disproportionate to a single-file edit. Two options were weighed: (a) scope
# the TRIGGER to the file classes the tool has actually caught violations in so far (README.md,
# docs/**, benchmarks/**, per ADR 0046 and the #141/#88 fix history), or (b) add a --file mode to
# check-restatement.mjs so it only compares the edited file against the corpus. (b) is a repo
# script change and is out of scope for a hook-only patch, plus it complicates the pure detect()
# signature that adr-lint.test.mjs-style testing relies on; a PROPOSAL patch for it is included
# separately (repo-hooks/check-restatement-file-mode.patch) for the PR agent to evaluate, NOT
# applied here. (a) needs no script change and is the cheaper sound option: it doesn't reduce the
# cost of any individual run, but it cuts how OFTEN a full-tree run fires -- editing a SKILL.md or
# an ADR (already linted elsewhere) no longer triggers it. Chosen: (a).
input=$(cat)
fp=$(printf '%s' "$input" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -z "$fp" ] && exit 0
# Normalize JSON-escaped Windows backslashes to forward slashes for case matching.
fp=$(printf '%s' "$fp" | sed 's/\\\\/\//g; s/\\/\//g')
root="${CLAUDE_PROJECT_DIR:-.}"
cd "$root" || exit 0   # gates assume repo-root cwd; never run them elsewhere.

run_gate() {
  out=$("$@" 2>&1) || { printf '%s\n' "GATE FAILED (fix now, before continuing): $out" >&2; exit 2; }
}

case "$fp" in
  */skills/*)
    skilldir=$(printf '%s' "$fp" | sed -n 's/.*\(skills\/[^/]*\)\/.*/\1/p')
    [ -n "$skilldir" ] && [ -d "$root/$skilldir" ] && run_gate python "$root/skills/building-skills/scripts/validate.py" "$root/$skilldir" ;;
esac
case "$fp" in
  */benchmarks/*.workflow.js) run_gate node "$root/scripts/check-workflow.mjs" ;;
esac
case "$fp" in
  */README.md|*/docs/*.md|*/benchmarks/*.md) run_gate node "$root/scripts/check-restatement.mjs" ;;
esac
exit 0
