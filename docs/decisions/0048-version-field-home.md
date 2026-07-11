---
id: 0048
title: "Version bumps batch off feature PRs via a forcing function, not new machinery"
status: accepted
summary: "The marketplace.json version-field rebase collisions (9 touches #122-#138; dev-skills bumped five times across five PRs in one day) come from coupling a bump to each feature PR, not an SSoT defect — the version already has ONE home (ADR 0017 + adr-lint). Fix by cadence: feature PRs don't bump; each plugin's bump is its own PR, triggered by the /retrospect pre-PR checklist and tracked by a GitHub issue (ADR 0021), reconciling 0017:28 without a gate. Reject a merge-time bot/gate/lock (disproportionate). Reject the per-plugin plugin.json split as a COLLISION fix (disproportionate; fixes only cross-plugin), decided separately on ENFORCEMENT grounds (ADR 0050)."
---

# 0048 — Version bumps batch off feature PRs, not new collision machinery

- Date: 2026-07-10
- Owner: PM
- Panel: counsel A (convention, don't-gold-plate), counsel B (structural split into per-plugin plugin.json); PM verified B's load-bearing claims against the manifests; red-team.
- Context: Retrospect finding (issue #139): `.claude-plugin/marketplace.json` was the most-churned file across #122-#138 (9 touches); parallel PRs bumping the same plugin's version line collided and rebased (dev-skills bumped five times in a day). No release workflow or tags exist — `/plugin marketplace update` pulls main, so MERGE-TO-MAIN is the publish event. Open question: serialize by convention, bump at merge time (bot/gate), bump once per batch, or accept the rebase cost.

## Decision
Reframe: not an SSoT/mirror defect — set-version.mjs (ADR 0017) + adr-lint's `manifestDrift` already guarantee each version ONE home. It is contention from coupling a bump to every feature PR. Fix the cadence with a forcing function, add no machinery:
1. **A feature PR does NOT bump a plugin version.** Each plugin's bump is its own dedicated PR via `set-version.mjs` (writes the one home). Forcing function (the repo's method, CLAUDE.md:33): the pending bump is filed as a GitHub issue at batch start (ADR 0021) and the `/retrospect` pre-PR checklist is the trigger that clears it — replacing the per-PR churn signal this decision removes. Plugin-agnostic: pdca-workflow's plugin.json (churned 3x) too.
2. **Accept the residual** rare collision: each version is a single JSON line, so any conflict is inherently one-line, and sync-before-spend (ADR 0043) resolves it.
3. **Shipped home — REWRITE CLAUDE.md:49** (its `plugin.json` parenthetical is already wrong for the ./skills plugins) to: "Version bumps don't ride feature PRs; each plugin bumps in its own PR via set-version.mjs (ADR 0048)." This ADR carries the rationale.

## Justification
Proportionate, zero engineering cost. Batching off feature PRs removes BOTH same-plugin and cross-plugin collisions at the source — strictly dominating "serialize" (option 1), which only orders around them. A merge-time bot/gate/lock is gold-plating (CLAUDE.md:21) for a one-line rebase: a new process-gating script needs its own decision-logic test (Never list) + new CI + new failure modes. **Reconcile ADR 0017:28** — it reserves a version↔plugin gates check IF a forgotten bump ships twice; the issue + `/retrospect` forcing function is the non-gate substitute that keeps bumps visible now that per-PR churn no longer signals them, and 0017:28's gate stays the named escalation if it fails. Overrule counsel B: a split is a disproportionate COLLISION fix, decided separately (ADR 0050).

## Assumptions
- [verified] dev-skills and engineering-skills BOTH declare `source: ./skills` (marketplace.json:15,27) and no `plugin.json` exists under `skills/` (`find skills -name plugin.json` empty) — a single `./skills/.claude-plugin/plugin.json` names one plugin, so B's "each gets its own plugin.json" is structurally blocked without also splitting the source dir.
- [verified] a marketplace entry validly omits an inline version when a plugin.json supplies it (pdca-workflow live: entry omits it, marketplace.json:33-37; plugin.json:3 supplies it) — so stripping the skills' inline versions WITHOUT a plugin.json home would blank the version (Sacred risk); B's "just strip the keys" is unsafe.
- [verified] batching cannot make a consumer MISS content — `/plugin marketplace update` keys staleness on git content, not the version field (a version-less entry updates fine, ADR 0011:37); the displayed number is advisory, so the only residual is a stale number, not missing content.
- [checkable] each plugin version is a single JSON line, so any collision is one-line — owner: PM; verified from marketplace.json:8,14,26 + plugin.json:3; result: verified.
- [unverifiable] the issue + `/retrospect` trigger keeps bumps from rotting vs per-PR bumping — REOPEN-IF content ships un-bumped past the trigger, or collisions recur after the norm lands.

## Rejected alternatives
- **Merge-time bump bot / gate / lock** — disproportionate machinery for a one-line rebase (see Justification).
- **Per-plugin plugin.json split (counsel B)** — as a COLLISION fix, disproportionate and fixes only cross-plugin, not the dominant SAME-plugin case. Decided separately on ENFORCEMENT grounds (ADR 0050); its version home then follows plugin.json existence (ADR 0017/set-version), agnostic to this cadence.
- **Serialize version-bump PRs (option 1)** — orders around collisions; batching removes them.
- **Accept-only, no norm (option 4)** — leaves the per-PR bump habit that generated five bumps in a day.

## Revisit triggers
- Content ships un-bumped past the `/retrospect` trigger, or a forgotten bump twice (0017:28) → adopt the version↔plugin gates check (0017's named remedy).
- Collisions recur after the norm lands → reconsider merge-time automation.
- The shared source is split (engineering-principles moves to its own source dir) → the per-plugin plugin.json home reopens.
- Claude Code ships native marketplace version tooling → delegate (mirrors 0017's trigger).
