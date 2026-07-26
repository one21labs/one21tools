---
id: 0018
title: "retrospect sweeps the diff's doc text for git-tellable backstory"
status: accepted
tier: lite
summary: "Add one signal to the retrospect agent's git-signal list: git-tellable backstory in the range's changed doc text (how-it-got-here narration, prior-state retelling — git history owns it). Budget-neutral: the agent sat at 2989/3000, so low-value wording was compressed to fit. Not an adr-lint rule — backstory is substance, not shape. One home: the agent's Method; the skill's step-2 list is not extended."
---

# 0018 — retrospect sweeps shipped doc text for backstory muda

- Decision: one signal clause in the retrospect agent's git-signal list
  (`pdca-workflow/agents/retrospect.md` Method): the diff's own changed doc text gets swept for
  backstory, citing CLAUDE.md's cut-on-sight list. The `/retrospect` skill's step-2 orchestrator
  list is not extended (fresh eyes are the point — the author-orchestrator wrote the narration
  and is blind to it). Budget-neutral: paid for by compressing restatement already in the
  prompt. Not a lint rule — backstory is substance, not shape (0003).
- Why: the failure class shipped once (an ADR amendment's Context narrated fork history) and was
  caught only by owner review — the most expensive gate. One prompt clause converts a muda-list
  item into a checked step every PR already walks.
- Rejected: an adr-lint backstory regex (substance-not-shape, misses real narration); extending
  the skill's step-2 list (restates the agent-owned method); raising the agent char budget
  (grandfathers bloat).
- Reopen-if: git-tellable backstory reaches owner review again -> consider a dedicated pre-PR
  doc-review step, not a bigger prompt.
- Enforced: `pdca-workflow/agents/retrospect.md` Method (git-tellable-backstory clause).

## Act
- [outcome] verified — clause ships at `pdca-workflow/agents/retrospect.md:19`.
- [process] shipped without its `## Act`; caught by a later outcome audit.
