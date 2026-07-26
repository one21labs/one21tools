---
id: 0049
title: "Defer proactive trigger-testing of the model-invocable primitives; mechanize the reactive trigger with a spawn-log hook"
status: accepted
tier: lite
summary: "Decline proactively TP/FP-testing the three always-loaded pdca descriptions (advise/red-team/verify) — ADR 0016's tight triggers hold and zero misfires are observed. But the primitives emit no git artifact, so 0016's reactive trigger is blind in autonomous mode: mechanize it with a PreToolUse spawn-log hook (rung-2, ADR 0047). When a misfire is seen, run an 8+8 both-arm set for the offending skill on the next benchmark."
---

# 0049 — defer proactive trigger-testing; mechanize 0016's reactive trigger

- Date: 2026-07-10
- Decision: decline the proactive TP/FP instrument for advise/red-team/verify — inherit ADR 0016's reactive REOPEN-IF; zero wasteful fires observed. Mechanize the reactive trigger instead: a PreToolUse spawn-log hook matching the Skill tool, appending every fire to a git-visible session log the retrospect arm reads — the primitives emit no other git artifact, so the backstop is otherwise blind in autonomous mode. On the FIRST misfire, author an 8-should-fire + 8-should-not-fire set for that skill only (ADR 0033's runner), piggybacked on the next benchmark run.
- Why: poka-yoke + muda. The tight descriptions ARE the prevention; a backstop must be ABLE to fire, which needed an observability fix, not the probabilistic instrument (fails ADR 0024's cost-per-decision test at zero observed misfires).
- Rejected: test now, full TP/FP x3 — spends on a zero-frequency risk. Pure defer with no artifact fix — the trigger stays blind. Should-not-fire-only set — forecloses the false-negative detector.
- Reopen-if: a primitive fires unbidden -> run the 8+8 set, trim per ADR 0033 if the description is at fault. The hook slips or can't match the Skill tool -> backstop stays interactive-only.
- Enforced: `pdca-workflow/hooks/spawn-log.sh`; ADR 0016's REOPEN-IF governs scope.
