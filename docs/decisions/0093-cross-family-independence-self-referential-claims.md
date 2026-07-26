---
id: 0093
title: "Self-referential loop claims need cross-family independence in verify/red-team"
status: accepted
tier: lite
summary: "#236 (26-Jul): a same-family stack (fresh verifier, red-team, ~20 sweep lanes) missed 3 defects a cross-family agent caught, all claims about the session's own blind spots/remedy/diagnosis. verify/red-team SKILL.md now name that claim class as needing a checker independent of the thing tested. No backend hardcoded (ADR 0050)."
---

# 0093 — cross-family independence for self-referential loop claims

- Decision: `/verify` and `/red-team` SKILL.md each gain: a claim about the loop's OWN
  behavior (its blind spots, its remedy's shape, its diagnosis's completeness) needs a checker
  independent of the thing tested — prefer a different model family for that class; same-family
  freshness clears contaminated reasoning, not shared priors. No backend ships in the plugin
  (ADR 0050); an adopter without a second family states the self-family caveat, never a silent
  substitution.
- Why: #236's 26-Jul session ran fresh verifier + red-team + ~20 sweep lanes on its own work,
  caught real defects, then a cross-family agent found 3 more — all self-referential (a zombie
  issue an artifact-deletion audit didn't grep for; an additive fix for an additive bias; its
  own diagnosis's unbuilt half). Same-family is uncontaminated by the session's reasoning but
  shares its priors — verifies frame-internal claims, can't see the frame.
- Rejected: hardcoding a cross-family backend into the shipped agent prompts — violates ADR
  0050; the fallback contract (#236, 18-Jul) covers second-family-less adopters already,
  mirroring `judge.py`'s `resolve_judge`/`SAME_FAMILY_NOTE`.
- Reopen-if: a same-family construction catches this same blind-spot class -> demote to
  advisory-only.
- Enforced: `pdca-workflow/skills/verify/SKILL.md` + `pdca-workflow/skills/red-team/SKILL.md`.
