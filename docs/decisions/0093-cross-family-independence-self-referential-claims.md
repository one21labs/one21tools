---
id: 0093
title: "Self-referential loop claims need cross-family independence, not just a fresh same-family checker"
status: accepted
tier: lite
summary: "26-Jul-2026 (#236): a fresh same-family verifier + red-team + ~20 lanes over one session's own work missed three defects, all claims about the SELF; a cross-family agent found all three. Fresh clears contaminated reasoning, not shared priors. No backend ships (ADR 0050)."
---

# 0093 — cross-family independence for self-referential claims

- Decision: a self-referential claim binds the SPAWN step of both check primitives — the checker
  comes from a lineage other than the maker's (model size and context freshness are not lineage),
  and an adopter with only one lineage checks anyway but must carry the shortfall into the result
  instead of absorbing it. Each primitive words its own degraded outcome. No backend ships.
- Why: 26-Jul, a fresh same-family verifier + red-team + ~20 sweep lanes over one session's own
  work caught real defects and missed three, all self-referential: an issue still demanding a
  mechanism the session had just deleted; an additive remedy for an additive bias; the unbuilt
  half of its own diagnosis. A cross-family agent found all three. Fresh clears contaminated
  REASONING, not shared PRIORS — same-family sees frame-internal claims, never the frame.
- Rejected: hardcoding a cross-family backend into the shipped prompts — ADR 0050 forbids the
  dependency, and #236's fallback contract already covers adopters with no second family
  (mirroring `judge.py`'s resolve_judge / SAME_FAMILY_NOTE). Also rejected: folding this into
  ADR 0062 — its "independent" means independent CONSTRUCTIONS, a different sense; bolting this
  onto a spend/plateau record is topic drift and buries the reopen-if.
- Reopen-if: a same-family construction catches this blind-spot class -> demote to advisory.
- Enforced: `pdca-workflow/skills/verify/SKILL.md`, `pdca-workflow/skills/red-team/SKILL.md`.
