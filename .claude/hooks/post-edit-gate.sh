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
# check-restatement SCOPING: check-restatement.mjs takes no --file argument -- every run is a
# full-tree scan for cross-file restatement (ADR 0046). Scoping the TRIGGER to the file classes
# with a violation history (README.md, docs/**, benchmarks/**, per ADR 0046) keeps a full-tree
# run from firing on every .md edit. A per-file mode would need a check-restatement.mjs change
# and would complicate the pure detect() signature its tests rely on.
input=$(cat)
fp=$(printf '%s' "$input" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -z "$fp" ] && exit 0
# Normalize JSON-escaped Windows backslashes to forward slashes for case matching.
fp=$(printf '%s' "$fp" | sed 's/\\\\/\//g; s/\\/\//g')
root="${CLAUDE_PROJECT_DIR:-.}"
cd "$root" || exit 0   # gates assume repo-root cwd; never run them elsewhere.
PY=$(command -v python3 || command -v python)  # Linux/CI ship python3 only; git-bash ships python.

run_gate() {  # $1 = gate name for telemetry; rest = the gate command
  gname="$1"; shift
  out=$("$@" 2>&1) || {
    # Gate-hit telemetry (ADR 0080): observability only, never in the failure path — appended
    # after the failure is decided, error-suppressed; marker-guarded, never mkdir (ADR 0071).
    # Line format home: scorecard.mjs parseGateHits.
    { [ -d "$root/docs/pdca" ] && printf '%s gate-hit %s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$gname" "$fp" >> "$root/docs/pdca/gate-hits.txt"; } 2>/dev/null
    printf '%s\n' "GATE FAILED (fix now, before continuing): $out" >&2; exit 2
  }
}

case "$fp" in
  */skills/*)
    # Derive the skill dir RELATIVE to $root, preserving any plugin prefix (#256): a bare
    # `skills/<name>` capture strips `pdca-workflow/`-style prefixes, so the dir guard below
    # silently skipped every plugin-scoped skill. Normalize root's backslashes the same way as
    # fp's, or the prefix strip fails on Windows and reintroduces the same silent skip.
    rootn=$(printf '%s' "$root" | sed 's/\\\\/\//g; s/\\/\//g')
    relfp=${fp#"$rootn"/}
    skilldir=$(printf '%s' "$relfp" | sed -n 's/^\(.*skills\/[^/]*\)\/.*/\1/p')
    [ -n "$skilldir" ] && [ -d "$root/$skilldir" ] && run_gate validate.py "$PY" "$root/skills/building-skills/scripts/validate.py" "$root/$skilldir" ;;
esac
case "$fp" in
  */benchmarks/*.workflow.js) run_gate check-workflow.mjs node "$root/scripts/check-workflow.mjs" ;;
esac
case "$fp" in
  */README.md|*/docs/*.md|*/benchmarks/*.md) run_gate check-restatement.mjs node "$root/scripts/check-restatement.mjs" ;;
esac
exit 0
