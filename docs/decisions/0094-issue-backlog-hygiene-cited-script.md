---
id: 0094
title: "Issue-backlog hygiene promotes one rung: a script retrospect runs and cites"
status: accepted
tier: lite
summary: "Retrospect's hygiene sweep covered git custodial state but never the issue backlog. ADR 0083's reopen clause fires: issue-hygiene.mjs emits dormancy and tracking-checklist signals the retrospect agent must run and cite, replacing the CLAUDE.md retitle rule. Agents propose; closing and retitling stay owner actions."
---

# 0094 — issue-backlog hygiene is a cited script, not a rule

- Decision: `pdca-workflow/scripts/issue-hygiene.mjs` reports two measured signals over open
  issues — dormancy, and an inventory line per multi-item tracking issue. The retrospect agent
  RUNS it and CITES the output. It proposes only: closing, retitling and re-scoping stay owner
  actions — issues are the work-state home (ADR 0021), and closing one destroys that state.
  CLAUDE.md's retitle rule is deleted, not supplemented.
- Why: ADR 0083 decided this class for git custodial state and set the reopen condition — a sweep
  missing visible cruft promotes one rung, to a script whose output the agent must cite. Issues
  are the same class; the prompt bullet never reached them. The tracking signal is an inventory,
  not a threshold: the motivating case had 13 boxes, none ticked, one direction already shipped,
  so tick state cannot be the trigger.
- Rejected: a duplicate/batching detector on title+body token overlap — measured here it ranked
  the one real pair 27th of 55 (~4% precision); the couplings worth batching are semantic, and a
  mostly-noise report trains people to skip it. A standalone triage agent or skill (0083:
  gold-plating). A CLAUDE.md rule alone, the shape deleted here.
- Reopen-if: the owner rejects more proposals than accepts -> thresholds are wrong; tune or
  retire them, don't add a judging layer.
- Enforced: `pdca-workflow/scripts/issue-hygiene.mjs` + test; the retrospect agent's Method.
