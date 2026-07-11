---
id: 0050
title: "Cross-plugin enforcement distribution: dependency chain via a per-plugin source split"
status: accepted
summary: "pdca-workflow stays the SINGLE enforcement-hooks carrier; every dependent marketplace plugin declares it in plugin.json `dependencies` (verified: auto-install, fail-closed, auto-enable) so any install auto-pulls the hooks — enforced, not advisory. dev-skills + engineering-skills share source ./skills and cannot each hold a plugin.json, so the mechanism REQUIRES splitting them into per-plugin source dirs carrying .claude-plugin/plugin.json with the bare dependency; the version home then follows plugin.json existence (ADR 0017/set-version). Cites ADR 0048 for cadence, no supersession. Cost: a Sacred restructure — the PR must prove /plugin install for all three plugins."
---

# 0050 — Cross-plugin enforcement distribution

- Date: 2026-07-10
- Owner: PM
- Panel: owner directive (enforcement on any install) + verified CC plugin-capability research + verifier (BLOCK -> reworked). Sibling to ADR 0047 (ladder), 0048 (bump cadence).
- Context: only pdca-workflow ships hooks/hooks.json (the ADR 0040 deny + 0047 wave-1 guards). dev-skills + engineering-skills source ./skills (marketplace.json:15,27), no plugin.json, no hooks. The owner wants the same poka-yoke on ANY install. No marketplace-level hooks mechanism exists (docs).

## Decision
- **Single carrier (SSoT):** pdca-workflow is the ONE home for the enforcement hooks — no duplication.
- **Enforced dependency:** every dependent marketplace plugin declares pdca-workflow in plugin.json `dependencies` (bare unversioned form), so installing it auto-pulls the carrier; its hooks then fire session-wide (the [checkable] below).
- **Per-plugin source split (the mechanism, on ENFORCEMENT grounds):** dev-skills + engineering-skills share `source: ./skills` and cannot each hold a plugin.json (one shared source names one plugin; verified). So restructure EACH into its own source dir carrying `.claude-plugin/plugin.json` with the bare dependency. The version home for those two then moves to their plugin.json — set-version.mjs branches on plugin.json EXISTENCE, not version-ownership (verifier ran plan()) — per ADR 0017. ADR 0048's bump-cadence is agnostic to WHERE the version lives, so this CITES 0048, not supersedes.
- **Cost + Sacred risk:** a restructure — marketplace source paths change and skills content moves or symlinks; a broken source path breaks `/plugin install` (Sacred). The restructure PR MUST prove `/plugin install` for all three plugins in its Testing section.
- **The distribution rule's own home (ladder, ADR 0047):** "a dependent plugin missing its enforcement dependency" is machine-decidable -> extend adr-lint.mjs (or a sibling check) to fail on omission, with a decision-logic test (Never rule). Rung-4 CI now; a rung upgrade needs scar tissue (0047).

## Justification
The dependency chain is the only shape meeting the owner's ENFORCED bar without duplication: it fails closed if the carrier is absent (docs), so a skills-only user cannot silently skip it. The shared-source split is the unavoidable COST of that bar (a shared plugin.json is blocked — one source, one plugin), not a preference. Duplicating hooks per plugin is guard-the-mirror (ADR 0015:20, 0040 item 7); the advisory note is the unguarded-if-skipped outcome the owner rejects. The rule follows its own ladder: machine-checkable => adr-lint, not prose.

## Assumptions
- [verified] plugin.json `dependencies` are officially supported (code.claude.com/docs/en/plugin-dependencies.md): auto-installed, FAIL CLOSED (`dependency-unsatisfied` -> plugin disabled), auto-ENABLED at the dependent's scope. Version CONSTRAINTS need a newer floor (see the doc); use the BARE form. A skills-only source carrying hooks is NOT documented.
- [verified] set-version.mjs branches on plugin.json EXISTENCE, not version-ownership — a version-less minimal plugin.json gains a version on the next bump (verifier ran plan()); so a split plugin.json becomes the version home (ADR 0017).
- [verified] dev-skills + engineering-skills share `source: ./skills` (marketplace.json:15,27); one shared source names one plugin -> a per-plugin plugin.json requires splitting the source (the restructure cost).
- [checkable] plugin hooks fire session-wide once enabled — docs say "when enabled" but don't equate plugin hooks to settings.json hooks; signal: pdca-workflow's explicit-model-guard fires in THIS plugin-loaded session (also closes ADR 0040:44's live-injection checkable). If not, the pull delivers no enforcement.
- [checkable] the adr-lint extension fails a dependent plugin missing the dependency, with a decision-logic test — verifier at build.

## Rejected alternatives
- A fabricated shared-source plugin.json for the two skill plugins — blocked (one source names one plugin; recreates the collision) — verified.
- "Version stays in the marketplace entry, no collision" — FALSE: set-version.mjs branches on plugin.json existence (verifier).
- Duplicate hooks per plugin — guard-the-mirror (ADR 0015:20); needs a drift check.
- Advisory "install pdca-workflow alongside" — leaves a skills-only user unguarded if skipped (owner non-goal).
- Skills as the hooks carrier — undocumented (plugin-dependencies.md); duplicated per skill.

## Revisit triggers
- The session-wide-hooks [checkable] fails -> the chain doesn't deliver enforcement; fall back to a documented required-install + a load-time guard.
- The restructure is judged too costly/risky vs the enforcement benefit -> fall back to the documented required-install (advisory residual; revisit on first unguarded install).
- Claude Code adds a marketplace-level hooks mechanism -> collapse the per-plugin dependency into it.

## Build order
- After ADR 0047 (ladder); cites ADR 0048 for cadence (no supersession). The restructure PR proves /plugin install for all three plugins (Sacred).
