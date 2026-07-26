---
id: 0011
title: "Close the skill/plugin intent gaps (audit remediation register)"
status: accepted
tier: lite
summary: "Disposition of a 3-lens intent-gap audit. B1 drops code-standards' unbacked 'correctness' trigger; B5 omits version from the marketplace mirror; B8 keeps pdca-init's COPY default (LINK dangles into the per-user cache), LINK only for self-hosting. Five smaller cite-or-silence cuts shipped in the same PR; one low-priority gap deferred."
---

# 0011 — close the skill/plugin intent gaps

- Decision: disposition of a 3-lens intent-gap audit (an artifact's trigger/description outran its content). **B1** dropped code-standards' unbacked "correctness" trigger — out of scope for dev-skills, routed to the consumer's own review tooling. **B5** pdca-workflow's `version` is omitted from the marketplace mirror (plugin.json's fallback is documented); `description` stays inline, gated on whether `/plugin browse` renders it from plugin.json (not `claude plugin validate`, which passes either way). **B8** pdca-init keeps COPY as the consumer default (a LINK into the per-user plugin cache dangles for teammates/CI); LINK scoped to self-hosting only. Five smaller cite-or-silence fixes shipped in the same PR; one low-priority gap deferred.
- Why: restore intent at the home that resolves for the consumer — omit a mirror only where a lower home resolves at install, keep a vendored copy where a link would dangle.
- Rejected: a correctness section on code-standards; LINK as the pdca-init default (dangles for teammates/CI); a sync-generator before trying to delete the mirror; one ADR per gap.
- Reopen-if: a second consumer's pdca-init template use shows COPY doesn't serve -> confirm the default holds. Claude Code changes marketplace/plugin.json resolution -> re-decide B5.
- Enforced: `skills/code-standards/SKILL.md` (B1); `.claude-plugin/marketplace.json` (B5); `pdca-workflow/skills/pdca-init/SKILL.md` (B8).
