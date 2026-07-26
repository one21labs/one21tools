---
id: 0083
title: "The repo-hygiene sweep lives in the retrospect flow, not a scheduled job"
status: accepted
tier: lite
summary: "9 stale remote branches accumulated unseen (8 squash-merge leftovers + 1 orphan claude/* push with no PR, #266): every gate inspects work going in, none inspects the state left behind. Source fix: deleteBranchOnMerge enabled on the repo settings. The residual class (orphan claude/* refs, gone-upstream locals, stray worktrees/stashes) gets a sweep bullet in the retrospect agent's Method — retrospect already fires at every session's step-back moment (ADR 0081), so the sweep recurs for free. Owner declined a scheduled weekly cloud sweep."
---

# 0083 — repo-hygiene sweep in retrospect

- Decision: the retrospect agent's Method gains one repo-hygiene bullet — command list and
  flagged classes live in `pdca-workflow/agents/retrospect.md` (its one home). No new agent,
  hook, or schedule. Complement already applied at the source: `deleteBranchOnMerge` enabled on
  the repo, closing the squash-merge leak for future merges.
- Why: custodial state had no owner, and a vigilance rule would leak (Process-Level Poka-yoke).
  Retrospect is the one surface guaranteed to run when a session steps back (ADR 0081's standing
  session-close default), so a sweep bullet there recurs for free. Prompt content only: no
  decision logic, so no gate/test (same reasoning as ADR 0082).
- Rejected: a scheduled weekly cloud sweep (infrastructure + recurring spend, owner declined); a
  standalone hygiene agent/skill (gold-plating for three git commands); a CLAUDE.md vigilance
  rule alone (task focus demonstrably narrows past it, per ADR 0081).
- Reopen-if: a later session's retrospect misses visible cruft (a stale branch, an orphan ref
  present during its run) -> promote one rung: a script the agent runs whose output it must
  cite, or a gate-hit line (ADR 0080).
- Enforced: `pdca-workflow/agents/retrospect.md` Method; repo setting `deleteBranchOnMerge`.
