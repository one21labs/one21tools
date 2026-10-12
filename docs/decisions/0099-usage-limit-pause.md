---
id: 0099
title: "skill-bench pauses every paid call at 80% of a subscription window and resumes after the reset"
status: accepted
tier: lite
summary: "Owner policy 12-Oct-2026 for every skill-bench user: detect 80% of a usage window, pause, restart after it resets. Enforced in the shared call path (usage_guard via hermetic_driver.do_call and the Claude judge), default on, threshold overridable; a limit-rejected call waits and re-issues instead of becoming an ERROR cell."
---

# 0099 — usage-limit pause

- Decision: owner, 12-Oct-2026, verbatim: "Detect automatically when you're at 80% of the session
  limit then pause and restart after it resets. Make this a policy for this skill - anyone using
  the plugin." Signal: the CLI's `rate_limit_event` (stream-json): per-window
  `utilization` and `resetsAt`. At >= 0.80 on any window, or a REJECTED status, every new call
  waits until the latest triggering reset + 60 s; in-flight calls finish. Default ON for every
  caller of the shared driver and the Claude judge; `$SKILL_BENCH_PAUSE_AT` overrides the
  threshold, and no setting retries into a window the limit already closed.
- Why: benchmark calls share the operator's own subscription windows; run to exhaustion they fail
  as empty ERROR cells and starve the operator's session (measured cases and mechanism:
  `usage_guard.py` header). A pause turns a hard failure into a wait and keeps 20% headroom.
- Rejected: a per-run cell cap — counts cells, not the window, so it neither prevents nor
  explains a rejection. Pausing only on REJECTED — leaves the operator at 100% mid-session.
  Polling a usage endpoint — none exposed; the event rides every call.
- Reopen-if: the CLI stops emitting `rate_limit_event`, or a pause outlives a window reset
  (decide() reads a stale `resetsAt`).
- Enforced: `skill-bench/scripts/lib/usage_guard.py` + `usage_guard_test.py`;
  `hermetic_driver.do_call`; `judge.ClaudeJudge.grade`.
