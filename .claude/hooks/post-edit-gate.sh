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
#
# liveness: per-event-exempt -- the observable fire (exit 2 + stderr) is contingent on a
# FAILING gate run, which may legitimately never occur in a window (ADR 0086 (b)). Canaries:
# one per routing case arm, each with a fixture the gate must fail on -- reaching the arm
# without observing the gate's verdict would be vacuous. Grammar: scripts/check-gate-tests.mjs.
# canary: {"event":"PostToolUse","tool":"Edit","copy":["skills/building-skills/scripts/validate.py"],"files":{"skills/foo/SKILL.md":"just a body with no frontmatter"},"stdin":{"tool_name":"Edit","tool_input":{"file_path":"__FIXTURE__/skills/foo/SKILL.md"}},"expect":{"exit":2}}
# canary: {"event":"PostToolUse","tool":"Edit","copy":["scripts/check-workflow.mjs"],"files":{"benchmarks/x.workflow.js":"const r = await agent(\"do the thing\", {label: \"x\"});"},"stdin":{"tool_name":"Edit","tool_input":{"file_path":"__FIXTURE__/benchmarks/x.workflow.js"}},"expect":{"exit":2}}
# canary: {"event":"PostToolUse","tool":"Edit","copy":["scripts/check-restatement.mjs"],"files":{"README.md":"alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima mike november oscar papa","docs/a.md":"alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima mike november oscar papa"},"stdin":{"tool_name":"Edit","tool_input":{"file_path":"__FIXTURE__/README.md"}},"expect":{"exit":2}}
# Path skeleton, deny predicate and gate-hit telemetry: lib/hook-lib.sh owns all three and
# documents why (including why this is sourced script-relative). Do not restate it here.
. "$(dirname "${BASH_SOURCE[0]}")/../../pdca-workflow/hooks/lib/hook-lib.sh" 2>/dev/null || exit 0
input=$(cat)
fp=$(hook_fp "$input")   # forward slashes, absolute — the case arms below need both
[ -z "$fp" ] && exit 0
root="${CLAUDE_PROJECT_DIR:-.}"
cd "$root" || exit 0   # gates assume repo-root cwd; never run them elsewhere.
PY=$(command -v python3 || command -v python)  # Linux/CI ship python3 only; git-bash ships python.

# "THE GATE SAID NO" AND "THE GATE COULD NOT RUN" ARE DIFFERENT ANSWERS, and only the first may
# block. This treated every non-zero status as a verdict, so a missing interpreter or an absent
# gate script turned every matching Edit into a hard block — the identical defect fixed in
# adr-lint-post-edit.sh, left live in its sibling because that fix closed the exemplar it was shown
# and not the class. Both preflights AND 126/127 are needed: the first covers "not installed", the
# second covers a command that resolves but cannot execute.
# HONEST LIMIT: a gate script that IS present and DOES run but dies on a syntax error exits 1,
# which is indistinguishable here from "found a real problem". That one still blocks, by design —
# guessing the difference would let a broken gate pass silently, which is the worse failure.
run_gate() {  # $1 = gate name for telemetry; rest = the gate command
  gname="$1"; shift
  command -v "$1" >/dev/null 2>&1 || return 0                      # interpreter absent
  # Scoped to the "<interpreter> <script>" shape, which is the only shape every call site below
  # uses. A script passed AFTER a flag (`node --foo g.mjs`) is NOT covered and will hard-block: a
  # missing module exits 1, not 126/127, so it never reaches the arm below. An earlier version of
  # this comment claimed that arm caught it — it does not; 126/127 covers exec failure of the
  # INTERPRETER, nothing about its arguments. Stated as a known limit rather than a false comfort.
  { [ $# -lt 2 ] || [ "${2#-}" != "$2" ] || [ -f "$2" ]; } || return 0   # gate script absent
  # `rc=0; ... || rc=$?`, not `out=$(...); rc=$?`. The second form is correct today only because
  # this file does not `set -e`; under it, the assignment's non-zero status would abort the hook
  # before rc is ever read, making every branch below dead and silently restoring the fail-closed
  # behaviour this function exists to remove. Costs nothing to be immune to a future `set -e`.
  rc=0
  out=$("$@" 2>&1) || rc=$?
  [ "$rc" -eq 0 ] && return 0
  [ "$rc" -eq 126 ] || [ "$rc" -eq 127 ] && return 0               # not executable / not found
  hook_gate_hit "$gname" "$fp"
  printf '%s\n' "GATE FAILED (fix now, before continuing): $out" >&2; exit 2
}

case "$fp" in
  */skills/*)
    # Derive the skill dir RELATIVE to $root, preserving any plugin prefix (#256): a bare
    # `skills/<name>` capture strips `pdca-workflow/`-style prefixes, so the dir guard below
    # silently skipped every plugin-scoped skill. Normalize root's backslashes the same way as
    # fp's, or the prefix strip fails on Windows and reintroduces the same silent skip.
    rootn=$(hook_norm_slashes "$root")
    relfp=${fp#"$rootn"/}
    # If the strip missed (root is the "." fallback, or carries a trailing slash), retry
    # against $PWD — after `cd "$root"` above it IS the absolute root — else an absolute fp
    # keeps its full prefix, the dir guard tests a nonsense path, and the gate silently skips.
    [ "$relfp" = "$fp" ] && relfp=${fp#"$(hook_norm_slashes "$PWD")"/}
    # "skills" must match as a WHOLE path component — a greedy `.*skills\/` also matched folder
    # names merely ENDING in "skills" (skills/building-skills/scripts/x derived .../scripts as
    # the skill dir and failed the gate on a missing SKILL.md).
    skilldir=$(printf '%s' "$relfp" | sed -n 's/^\(\(.*\/\)\{0,1\}skills\/[^/]*\)\/.*/\1/p')
    [ -n "$skilldir" ] && [ -d "$root/$skilldir" ] && run_gate validate.py "$PY" "$root/skills/building-skills/scripts/validate.py" "$root/$skilldir" ;;
esac
case "$fp" in
  */benchmarks/*.workflow.js) run_gate check-workflow.mjs node "$root/scripts/check-workflow.mjs" ;;
esac
case "$fp" in
  */README.md|*/docs/*.md|*/benchmarks/*.md) run_gate check-restatement.mjs node "$root/scripts/check-restatement.mjs" ;;
esac
exit 0
