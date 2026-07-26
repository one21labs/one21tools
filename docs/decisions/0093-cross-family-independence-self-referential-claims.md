---
id: 0093
title: "Self-referential loop claims need cross-family independence"
status: accepted
summary: "26-Jul-2026 (#236): a fresh same-family verifier + red-team + ~20 lanes over one session's own work missed three defects, all claims about the SELF; a cross-family agent found all three. Ships one token, FRAME-UNCHECKED, and no resolver."
tier: lite
---

# 0093 — cross-family independence for self-referential claims

- Decision: a claim about this loop's OWN behaviour cannot be discharged by a spawned subagent —
  the maker's lineage by construction (size and context freshness are not lineage). Both
  check primitives route such a claim outside the lineage or return one shared token,
  `FRAME-UNCHECKED`: not a pass, not a break, carried into whatever consumes the verdict.
  `/decide` takes it as an `[unverifiable]` assumption, never a block. The plugin states the
  requirement and ships NO resolver.
- Why: a fresh same-family verifier + red-team + ~20 sweep lanes over one session's own
  work caught real defects and missed three, all self-referential: an issue demanding a
  mechanism the session had deleted; an additive remedy for an additive bias; the unbuilt half
  of its own diagnosis. A cross-family agent found all three. Fresh clears contaminated
  REASONING, not shared PRIORS — same-lineage sees frame-internal claims, never the frame.
- Rejected: shipping a resolver (probe a second-family CLI, pin a model) — the principle ships,
  this repo's grok/copilot invocation does not; copy `skill-bench`'s resolve-else-caveat shape
  only. Wording the skills as if spawn could switch family — Claude Code subagents
  cannot, so the honest product is the token. Folding into ADR 0062 — its "independent" means
  independent CONSTRUCTIONS.
- Reopen-if: a same-lineage construction catches this blind-spot class -> demote to advisory.
- Enforced: `pdca-workflow/skills/verify/SKILL.md`,
  `pdca-workflow/skills/red-team/SKILL.md`, `pdca-workflow/skills/decide/SKILL.md`.
