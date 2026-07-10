---
id: 0039
title: "Route #93 authoring-time prevention rules to their shipped reference homes"
status: accepted
summary: "Adopt eight one-line authoring-time prevention rules from #93 (audit method + trigger cadence; search-before-state; ban expiring status prose; test-the-surface; root-cause handoff + issue-shape; JIT timing row; routing-bypass anti-pattern), each at its shipped reference home per ADR 0038. Reject item 9c (in-flight-kill economics) as gold-plate."
---

# 0039 — Route #93 authoring-time prevention rules to their shipped reference homes

- Date: 2026-07-10
- Owner: PM
- Panel: lean-process-engineer, process-economist, session-operator, plugin-adopter.
- Context: The #93 RCA found ~40 muda items survived green gates because enforcement is diff-scoped + incident-reactive while the dominant waste is corpus-scoped + authoring-time-preventable (#93 root cause). Several prevention rules are verified unhoused or mis-routed; each belongs in a shipped reference (ADR 0038), one line each.

## Decision
Adopt these authoring-time prevention rules, each at its shipped home (per ADR 0038):

| # | Rule | Shipped home |
|---|------|--------------|
| 1 | Corpus-scoped audit method (per-area finders, cite-or-silence, one strong-tier synthesis); recur by a real trigger (per-N-merged-PRs), NOT a fixed calendar cadence | waste-identification.md Audit Process (:67-84) |
| 3 | Search-before-state authoring rule | ssot-enforcement.md Step 5 (:129-134) |
| 4 | Ban expiring status prose ("advisory today", "when wired") — status lives in the artifact, docs point | ssot-enforcement.md Documentation table (:59-67) |
| 5 | Test-the-surface: a shipped artifact's test exercises it the way its consumer invokes it | validation-rules.md |
| 8a | Audit Process hands off to root-cause-analysis.md (group findings by root cause before countermeasures) | waste-identification.md Audit Process |
| 8b | Issue-shape: one issue per root cause; body carries Root cause / Fix / Prevention | waste-identification.md Audit Process |
| 9a | Timing row in the Decision Test: a rule that must fire at an action-moment (tool call, fan-out) → hook/always-loaded, not a JIT reference | jit-documentation.md Decision Test (:18-25) |
| 9b | Routing-bypass anti-pattern: a CLAUDE.md deep-link into a skill's references/ bypasses its SKILL.md routing → link the skill/SKILL.md | claude-md.md Anti-Patterns (:54-62) |

REJECT item 9c (in-flight-kill economics row in subagents.md).

**PR shape (O8):** the eight rows touch 5 files across 3 skills (engineering-principles: waste-identification/ssot-enforcement/jit-documentation; optimizing-context: claude-md; building-skills: validation-rules), but they are ONE concern — the single decision "place authoring-time prevention rules in shipped homes" — so ONE PR implements them (CLAUDE.md one-concern is satisfied by the shared concern, not by file locality). Meta/tooling content, version-exempt. If 0038 has not yet landed when this builds, sequence 0038 first — both edit jit-documentation.md's Decision Test (0038's 9d shipping-boundary row, 0039's 9a timing row) and must not collide.

## Justification
Each rule is a verified-unhoused, one-line addition to a file that already ships (cost ~0, additive, no drift surface). Item 1 reframed: accept the METHOD (houses in the shipped audit process) but reject a FIXED cadence — recur by trigger, else Overproduction. Value: closes the method-chain break (#93 Branch B — waste-identification.md Audit Process ends at Categorize/Countermeasure with no root-cause handoff, verified :82-84) and the routing-bypass mechanism, in homes every consumer inherits. 9c rejected: gold-plate — the issue's own text flags it, one retracted sunk-cost defense needs no permanent rule, item 6's hook (ADR 0040) partly obviates it; recording-for-record without prevention value is the muda CLAUDE.md warns against.

## Assumptions
- [verified] waste-identification.md Audit Process (:67-84) ends at "Categorize → Countermeasure" with no root-cause-analysis handoff — read 2026-07-10 (:82, :84); the gap #93 Branch B names.
- [verified] shipped homes exist: ssot-enforcement.md Documentation table :59-67 + Step 5 :129-134; claude-md.md Anti-Patterns :54-62; jit-documentation.md Decision Test :18-25 — all read 2026-07-10.
- [checkable] each home stays under its char cap after the one-line add (references cap 12,000; ssot 6,897 / claude-md 6,954 / jit 3,771 measured) — owner: verifier; result: ample headroom.
- [unverifiable] a trigger-based audit cadence catches corpus waste at acceptable cost vs a fixed cadence — REOPEN-IF two consecutive audits find < 3 items each (over-cadenced) or > 20 (under-cadenced).

## Rejected alternatives
- Fixed weekly/per-N audit cadence — Overproduction when the trigger hasn't fired.
- Repo-only homes (CLAUDE.md, .github/ISSUE_TEMPLATE) for items 3/4/8b — violates ADR 0038; consumers don't inherit them.
- Adopt 9c — gold-plate.

## Revisit triggers
- A corpus audit finds a class none of these rules addresses → extend the taxonomy, not the count.
- The audit-cadence trigger proves mis-tuned (see REOPEN-IF).
