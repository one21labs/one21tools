#!/usr/bin/env bash
# PreToolUse hook (matcher: Skill) for the pdca-workflow plugin (ADR 0049 decision 2): append
# one git-visible log line whenever one of the plugin's panel primitives -- advise, red-team,
# verify -- is invoked, with or without the pdca-workflow: plugin prefix. Pure observability:
# ALWAYS exits 0, NEVER denies, never blocks -- the /retrospect git-signal arm reads the log
# later to count panel spawns on a branch. One line per fire: ISO-8601 UTC date + skill name as
# given. Cannot recurse: this hook fires on Skill tool use and only appends to a file (no skill,
# agent, or tool is invoked from here).
#
# LOG LOCATION: $CLAUDE_PROJECT_DIR/docs/pdca/session-log.txt. Chosen because (verified against
# this repo's .gitignore): `.claude/*` is gitignored (only settings.json, output-styles/, agents/
# are unignored), so anything under .claude/ would be git-INVISIBLE -- defeating the purpose --
# and `*.log` is gitignored too, so the file is .txt, not .log. docs/ is tracked, already the
# home of committable process state (docs/decisions/), and a consumer without docs/ gets it
# created by the mkdir -p below. The retrospect rubric and the PR agent cite this path.
#
# WRITE MECHANICS: single-line `>>` append with O_APPEND semantics -- atomic enough for
# line-sized writes even when the sibling three-dot-warn hook (repo-side) appends to the SAME
# file; neither hook reads/rewrites the file, so there is no read-modify-write race.
#
# ACCEPTED LIMITATIONS: a bare `verify` invocation also matches the Claude Code built-in verify
# skill, not only pdca-workflow's -- an over-log (one extra counted line), never a miss; the log
# records the name exactly as invoked so the reader can tell the prefixed form apart. Skill name
# extraction uses the house no-jq sed pattern ([^"]* stops at the first quote), which is exact
# here because a skill name contains no quotes. Fails OPEN (exit 0, no log line) on
# malformed/empty stdin or a missing skill field. UNDER-log: a panel run via raw Agent-tool
# subagents (plugin skills not loaded) never fires the Skill matcher -- zero lines is not proof
# of zero panels; the retrospect agent cross-checks ADR Panel: lines for exactly this reason.
input=$(cat)
skill=$(printf '%s' "$input" | sed -n 's/.*"skill"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -z "$skill" ] && exit 0

case "$skill" in
  advise|red-team|verify|pdca-workflow:advise|pdca-workflow:red-team|pdca-workflow:verify)
    root="${CLAUDE_PROJECT_DIR:-.}"
    mkdir -p "$root/docs/pdca" 2>/dev/null || exit 0
    printf '%s skill-spawn %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$skill" >> "$root/docs/pdca/session-log.txt" 2>/dev/null
    ;;
esac
exit 0
