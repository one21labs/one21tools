---
id: 0014
title: "Transcript extractor for /retrospect: precondition unmet — defer; add an orchestrator non-git-visible self-check"
status: accepted
tier: lite
summary: "0007's feasibility trigger fired; precondition FAILED — the transcript JSONL schema is reverse-engineered/unversioned, type:user != human-typed, attribution is line-level cross-file. Grep-only is infeasible. Rejected the extractor; adopted a cheaper lever (retrospect's step-4 non-git-visible self-check); re-deferred behind a sharpened precondition."
---

# 0014 — transcript extractor: precondition unmet, defer; add an orchestrator self-check

- Decision: reject the independent transcript extractor as specified — the real JSONL is
  reverse-engineered/unversioned, `type:"user"` isn't human-typed, attribution is line-level
  cross-file, so grep-only is infeasible and the feasible build is a shipped, secrets-handling
  parser. Instead, retrospect step 4 gained a one-line self-check: "did the user correct
  anything NOT reflected in a commit?" — orchestrator-side, zero shipped surface. Re-deferred:
  re-fire only when Claude Code ships a documented, versioned transcript schema or query API
  AND a per-message-to-commit attribution primitive.
- Why: the extractor's value is an independent witness, but the only feasible build is high
  surface (secrets + drift-prone schema) for friction already caught by the git-visible
  cross-check. The self-check captures most of that value at zero cost.
- Rejected: the extractor in any form — grep-only refuted empirically. Pure hold — leaves the
  non-git-visible residual unaddressed for free.
- Reopen-if: a user surfaces a non-git-visible retro miss the self-check should have caught
  (the only external observer) -> re-weigh the extractor. Claude Code ships the sharpened
  precondition's schema/API -> re-run the call.
- Enforced: `pdca-workflow/skills/retrospect/SKILL.md` step 4 (git-visible tag + self-check
  question).
