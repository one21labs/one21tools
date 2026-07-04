---
id: 0011
title: "Close the skill/plugin intent gaps (audit remediation register)"
status: accepted
summary: "Disposition of a 3-lens intent-gap audit. Judgment calls: B1 drop code-standards' unbacked 'correctness' trigger; B5 omit version from the marketplace mirror (documented fallback), gate description-omission on the /plugin browse catalog; B8 keep pdca-init's COPY default (a link into the per-user plugin cache dangles), LINK only for self-hosting. Five cite-or-silence cuts (B2/B4/B6/B7/B9 — B4's fabricated citation confirmed + cut); B3 deferred. One PR, scoped commits."
---

# 0011 — Close the skill/plugin intent gaps

- Date: 2026-07-01
- Owner: PM
- Panel: 3 intent-gap audit lenses (sonnet — dev-skills; engineering-principles + marketplace; pdca-workflow), never primed. Verifier + red-team + web citation-check ran the gate; findings folded below.
- Context: the audit found one defect class — an artifact whose stated intent (trigger, description, dogfooded example) outruns its content. This register records each gap's disposition + PR grouping.

## Decision
**Judgment calls (priority-ordered):**
- **B1 code-standards SKILL.md:3 promises a "correctness" audit; body 8-143 has none.** DROP the "correctness" trigger word — keep code-standards scoped to standards. Do NOT add a correctness section: correctness is OUT OF SCOPE for dev-skills (route it to the consumer's own review tooling — /code-review, /verify, the verifier agent do NOT ship in this marketplace).
- **B5 pdca-workflow's version+description sit in BOTH marketplace.json:35-36 and plugin.json:2-4; the descriptions have ALREADY drifted (plugin.json:4 adds "for AI-assisted projects").** OMIT `version` now — plugin.json fallback is documented. For `description`, `claude plugin validate` passes even omitted, so it is NOT the gate — the hazard is a blank pre-install `/plugin browse` listing; delete-the-mirror ONLY IF that catalog renders it from plugin.json, else keep it inline behind a tested drift check (adr-lint.mjs, tested). Scoped to pdca-workflow — the ./skills entries have no plugin.json, so marketplace.json is already their single home.
- **B8 pdca-init/SKILL.md:35-38 says COPY the template; this repo dogfoods LINK (docs/decisions/README.md:8-11).** KEEP COPY as the consumer default — a consumer's plugin lives in the per-user cache (plugins.md:234-242), so a committed README linking `../../pdca-workflow/...` dangles for teammates/CI/GitHub and breaks on uninstall; a vendored frozen-at-adoption copy is legitimate, not drift (pdca-init/SKILL.md:9). Scope LINK to self-hosting (this repo IS the plugin source), documented in pdca-init as the exception.

**Directed cuts (cite-or-silence):**
- B2 optimizing-context references/skills.md:3,69 cite absent "skill-creator"/"skill-builder" -> replace with building-skills.
- B4 engineering-principles SKILL.md:75,83 (bibliography at references/ENGINEERING_PRINCIPLES.md:204-213): CUT the fabricated (Jiao,2025) attribution (keep the plain 0.95^10 compounding math unattributed); RE-ATTRIBUTE the team-archetypes claim to **DORA(2025)** with the real source (dora.dev) — see WEAKEST below.
- B6 README:57-62 ~/.claude/skills symlink-fallback claim is uncorroborated -> corroborate vs official docs or replace.
- B7 hooks/retrospect-reminder.sh:9-14 anchors "gh pr create" at command start, so `cd repo && gh pr create` fires no reminder -> match the substring anywhere in the command value.
- B9 doc-budgets.md is undiscoverable (pdca README:29-30 omits it; no inbound link) -> add to the README box list + one cross-ref from decide/SKILL.md.

**Accept-deferred (low priority):** B3 optimizing-context SKILL.md:86-98 mechanism-guides table reads as building-skills progressive-patterns.md:111-123's "Bad (disconnected)" -> carve a narrow exception for a genuine many-equal-siblings index.

**Shipping:** one PR (one register = one concern), commits by scope: dev-skills B1+B2; pdca-workflow B7+B9+B8; marketplace/README B5+B6; engineering-principles B4.

## Justification
One defect class -> restore intent at the home that actually resolves for the consumer: omit a mirror only where the lower home resolves at install (B5 version); keep a vendored copy where a link would dangle (B8); cite-or-silence the rest.

## Assumptions
- **[verified] WEAKEST RESOLVED (verifier web-check): the (Jiao,2025) citation is FABRICATED** — no such publication; per this ADR's own escalation, B4 CUTS it (compounding math kept unattributed). DORA(2024) is REAL-BUT-MISATTRIBUTED — the archetypes are the 2025 report -> B4 re-attributes to DORA(2025).
- [checkable] version fallback to plugin.json is documented (safe to omit); description-omission is gated on the `/plugin browse` catalog rendering it (NOT on `claude plugin validate`, which passes regardless) — else description stays inline behind a tested drift check. — owner: verifier.
- [verified] B7 reproduced live (prefixed `gh pr create` fires no reminder); B2/B9 cites confirmed (skills.md:3,69; README:29-30).
- [unverifiable] B3's working links keep the table functionally reachable. REOPEN-IF a reader mis-navigates it.

## Rejected alternatives
- Add a correctness section to code-standards (B1) — over-reaches dev-skills' scope; correctness is the consumer's own review tooling's job.
- Make LINK the consumer default (B8) — a linked path into the per-user plugin cache dangles for teammates/CI (plugins.md:234-242); vendored copy is the safe default.
- A marketplace sync-generator before ruling out omission (B5) — guards a mirror before trying to delete it.
- One ADR per gap — proliferation; one audit's disposition is one register.

## Revisit triggers
- A second consumer exercises pdca-init's template path -> confirm the vendored-copy default holds (link only self-hosting).
- Claude Code changes how marketplace vs plugin.json metadata resolves -> re-decide B5.
