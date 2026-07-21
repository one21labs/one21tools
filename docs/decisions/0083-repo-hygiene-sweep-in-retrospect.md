---
id: 0083
title: "The repo-hygiene sweep lives in the retrospect flow, not a scheduled job"
status: accepted
summary: "9 stale remote branches accumulated unseen (8 squash-merge leftovers + 1 orphan claude/* push with no PR, #266): every gate inspects work going in, none inspects the state left behind. Source fix: deleteBranchOnMerge enabled on the repo settings. The residual class (orphan claude/* refs, gone-upstream locals, stray worktrees/stashes) gets a sweep bullet in the retrospect agent's Method — retrospect already fires at every session's step-back moment (ADR 0081), so the sweep recurs for free. Owner declined a scheduled weekly cloud sweep: new infrastructure plus per-run cost for a class already near-closed at the source."
---

# 0083 — repo-hygiene sweep in retrospect

- Date: 2026-07-21
- Owner: PM (owner-directed; the want is quoted: steward the process — the cruft "would have just
  continued to accumulate" if unflagged; cadence and scope selected by the owner in-session)
- Panel: none (routine, owner-settled placement; recorded directly)
- Context: on 21-Jul-2026 the owner found 9 stale remote branches no session had ever flagged.
  Two properties hid them: squash merges keep merged branches out of `git branch -r --merged`,
  and every existing gate (retrospect-before-PR, claim comments, CI budgets) faces inbound work,
  never the repository state a session leaves behind. The failure mode is task-scoped narrowing:
  "PR merged, issue closed" terminated each session's attention (sibling of ADR 0081's
  pressure-narrowing — there judgment narrows at failure; here attention never widens past the
  task).

## Decision
The retrospect agent's Method gains one repo-hygiene bullet — the command list and flagged
classes live in `pdca-workflow/agents/retrospect.md` (its one home), governed by the principle:
prefer a structural fix (a setting, a gate) over a vigilance rule. No new agent, hook, or
schedule. Complement, already applied at the source: `deleteBranchOnMerge` enabled on the repo,
closing the squash-merge leak for all future merges.

## Justification
Custodial state had no owner, and a vigilance rule would leak (Process-Level Poka-yoke doctrine).
Retrospect is the one surface guaranteed to run when a session steps back — ADR 0081 made it the
standing session-close default with mechanically counted skips — so a sweep bullet there recurs
for free and inherits 0081's compliance measurement. A scheduled cloud sweep covers session-gap
weeks but adds infrastructure and per-run cost for a residual class the source fix already
shrank; the owner declined it. Prompt content only: no decision logic, so no gate/test (same
reasoning as ADR 0082); the agent char budget (3,500) binds — addition measured at 271 chars
against 290 headroom before editing.

## Assumptions
- [unverifiable] WEAKEST: a prose Method bullet actually fires — the sweep depends on the agent
  executing it, not on any mechanical check. REOPEN-IF a later session's retrospect misses
  visible cruft (a stale branch, an orphan ref present during its run); then promote one rung:
  a script the agent runs whose output it must cite, or a gate-hit line (ADR 0080).
- [checkable] the deleteBranchOnMerge setting held: the next squash-merged PR's head branch
  disappears without manual action — observable on this PR itself if squash-merged.
- [checkable-doc] no settled ADR contradicted: 0081 extended (one Method bullet), not amended;
  0082's no-gate-for-prompt-content reasoning reused; 0080 cited only as the promotion path.

## Rejected alternatives
- Scheduled weekly cloud sweep — covers no-session weeks, but new infrastructure + recurring
  spend for a near-closed class; owner declined (option was put to the owner explicitly).
- Standalone hygiene agent/skill — a whole new surface for three git commands; gold-plating.
- Vigilance rule in CLAUDE.md alone — instructs attention that task focus demonstrably narrows;
  rejected by the same logic as 0081's rejection of prompt-only mitigation.

## Revisit triggers
- The [unverifiable] REOPEN-IF fires (sweep misses visible cruft) → promote to a cited script
  or gate-hit telemetry.
- The residual class grows a new member (e.g. a new surface that accumulates state) → extend
  the bullet, or revisit the declined schedule if the class outgrows session cadence.
