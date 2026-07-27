#!/usr/bin/env bash
# PreToolUse hook (matchers: Skill AND Agent|Task -- both wired in hooks.json) for the
# pdca-workflow plugin (ADR 0049 decision 2; Agent|Task surface added for ADR 0086 / #276):
# append one git-visible log line whenever a panel/loop primitive is invoked, on EITHER of its
# two observable tool surfaces:
#   - Skill tool: `skill-spawn <name>` for advise, red-team, verify, retrospect (the ADR 0081
#     closeout-denominator), with or without the pdca-workflow: plugin prefix.
#   - Agent/Task tool: `agent-spawn <subagent_type>` for any PLUGIN-OWNED agent
#     (subagent_type `pdca-workflow:*`) -- the surface panel agents actually spawn through,
#     which the Skill matcher never sees (#276: the ADR 0086 red-team run and a /retrospect
#     run were both zero-logged).
# SLASH-COMMAND COUNTING (#276 build decision): a user-typed /retrospect or /advise loads skill
# content with NO Skill tool call, so the command invocation itself is unobservable to hooks;
# it is counted at the Agent layer when the loaded skill spawns its pdca-workflow:* agent --
# the one tool surface that path does cross.
# Pure observability: ALWAYS exits 0, NEVER denies, never blocks -- the /retrospect git-signal
# arm reads the log later to count panel spawns on a branch. One line per fire: ISO-8601 UTC
# date + event tag + name as given. Cannot recurse: this hook fires on Skill/Agent tool use and
# only appends to a file (no skill, agent, or tool is invoked from here).
#
# liveness: boundary-coupled -- a retrospect run's adoption artifact carries a Retrospect-Run
# commit trailer (an independently logged series in git); expected vs observed compared by the
# consumer repo's scorecard (ADR 0086; this repo: scripts/scorecard.mjs). Declaration grammar
# home: the consumer repo's check-gate-tests (this repo: scripts/check-gate-tests.mjs).
# canary: {"event":"PreToolUse","tool":"Skill","stdin":{"tool_name":"Skill","tool_input":{"skill":"red-team"}},"expect":{"append":"docs/pdca/session-log.txt","match":" skill-spawn red-team$"}}
# canary: {"event":"PreToolUse","tool":"Skill","stdin":{"tool_name":"Skill","tool_input":{"skill":"pdca-workflow:retrospect"}},"expect":{"append":"docs/pdca/session-log.txt","match":" skill-spawn pdca-workflow:retrospect$"}}
# canary: {"event":"PreToolUse","tool":"Agent","stdin":{"tool_name":"Agent","tool_input":{"subagent_type":"pdca-workflow:retrospect","prompt":"x"}},"expect":{"append":"docs/pdca/session-log.txt","match":" agent-spawn pdca-workflow:retrospect$"}}
# canary: {"event":"PreToolUse","tool":"Task","stdin":{"tool_name":"Task","tool_input":{"subagent_type":"pdca-workflow:red-team","prompt":"x"}},"expect":{"append":"docs/pdca/session-log.txt","match":" agent-spawn pdca-workflow:red-team$"}}
#
# LOG LOCATION: $CLAUDE_PROJECT_DIR/docs/pdca/session-log.txt. Chosen because (verified against
# this repo's .gitignore): `.claude/*` is gitignored (only settings.json, output-styles/, agents/,
# hooks/ are unignored), so anything under .claude/ would be git-INVISIBLE -- defeating the purpose --
# and `*.log` is gitignored too, so the file is .txt, not .log. docs/ is tracked, already the
# home of committable process state (docs/decisions/). The retrospect rubric
# (agents/retrospect.md) cites this path.
#
# FIRING SCOPE (ADR 0071): docs/pdca/ is also the PDCA adoption marker (scaffolded by
# /pdca-init) -- this hook logs only where the dir ALREADY exists and never creates it. The
# marker is opt-in state; a hook that mkdir'd its own marker would opt every project in on the
# first panel (or builtin `verify`) invocation, the exact write-pollution ADR 0050 rules out.
#
# WRITE MECHANICS: single-line `>>` append with O_APPEND semantics -- atomic enough for
# line-sized writes even when the sibling three-dot-warn hook (repo-side) appends to the SAME
# file; neither hook reads/rewrites the file, so there is no read-modify-write race.
#
# ACCEPTED LIMITATIONS: a bare `verify` invocation also matches the Claude Code built-in verify
# skill, not only pdca-workflow's -- an over-log (one extra counted line), never a miss; the log
# records the name exactly as invoked so the reader can tell the prefixed form apart. A Skill
# invocation that goes on to spawn a pdca-workflow:* agent logs on BOTH surfaces (one
# skill-spawn + one agent-spawn) -- an over-log, never a miss; the distinct event tags let a
# reader dedup. CONSUMER-NAMED advisor agents (built from advisor-template.md with repo-local
# names) spawn outside the pdca-workflow:* namespace and are NOT agent-logged -- a generic
# plugin cannot know consumer agent names; zero agent-spawn lines is not proof of zero panels,
# and the retrospect agent cross-checks ADR Panel: lines for exactly this reason. Name
# extraction uses the house no-jq sed pattern ([^"]* stops at the first quote), exact here
# because skill/agent names contain no quotes; a literal "subagent_type" phrase inside a prompt
# string VALUE is JSON-escaped (\") and lacks the contiguous bytes the pattern requires (same
# safety argument as explicit-model-guard.sh). Fails OPEN (exit 0, no log line) on
# malformed/empty stdin or a missing skill/subagent_type field.
# hook_scrub's one home. Script-relative, and a missing lib exits 0 — this hook is pure
# observability and must never become the reason a spawn did or did not happen.
. "$(dirname "${BASH_SOURCE[0]}")/lib/hook-lib.sh" 2>/dev/null || exit 0

input=$(cat)
tool=$(printf '%s' "$input" | sed -n 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')

log_line() {  # $1 = event tag, $2 = name as given
  root="${CLAUDE_PROJECT_DIR:-.}"
  [ -d "$root/docs/pdca" ] || return 0
  # Scrub via the lib's one policy: this log is whitespace-delimited and read per line, so an
  # embedded newline or tab would split a row or shift a field for its counters.
  printf '%s %s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(hook_scrub "$1")" "$(hook_scrub "$2")" \
    >> "$root/docs/pdca/session-log.txt" 2>/dev/null
}

case "$tool" in
  Skill)
    skill=$(printf '%s' "$input" | sed -n 's/.*"skill"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
    [ -z "$skill" ] && exit 0
    case "$skill" in
      advise|red-team|verify|retrospect|pdca-workflow:advise|pdca-workflow:red-team|pdca-workflow:verify|pdca-workflow:retrospect)
        log_line skill-spawn "$skill" ;;
    esac
    ;;
  Agent|Task)
    agent=$(printf '%s' "$input" | sed -n 's/.*"subagent_type"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
    [ -z "$agent" ] && exit 0
    case "$agent" in
      pdca-workflow:*)
        log_line agent-spawn "$agent" ;;
    esac
    ;;
esac
exit 0
