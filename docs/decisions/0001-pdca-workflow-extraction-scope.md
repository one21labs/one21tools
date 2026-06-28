---
id: 0001
title: "pdca-workflow extraction scope"
status: accepted
summary: "Generic framework in; domain layer + runnable metrics engine + standalone review-system.md out"
---

# 0001 — pdca-workflow extraction scope

- Date: 2026-06-27
- Owner: PM
- Panel: none standing (this repo ships the framework, not a product). Informed by a fan-out
  gap-analysis + adversarial-verification pass over ltconfig (the source) vs the extracted plugin,
  applying the framework's own cite-or-silence / verify-before-acting discipline.
- Context: PR 1 extracts ltconfig's PM-led PDCA review/retrospect loop into the `pdca-workflow`
  plugin. What is generic framework vs project-supplied domain is itself a YAGNI judgment call —
  the framework's own rule (run a lightweight review/ADR before building) applies to its own
  extraction. This ADR records the scope so the divergence from the source is intentional, not drift.

## Decision
IN (generic, shipped by the plugin): the advise->decide->verify topology; the structural agents
(`pm`, `tech-lead`, `red-team`, `verifier`, `retrospect`) stripped of ltconfig cites; the three
skills; the ADR system + canonical template (frontmatter-cataloged, no index mirror;
version-agnostic; rationalize-in-place; shared register); a runnable zero-dep `adr-lint.mjs` + its
decision-logic test; the `metrics-engine.md` analyze() contract; an opt-in `claude-review.yml`
template; the principles (cite-or-silence, fresh-eyes, verify-before-acting, lowest-home routing,
poka-yoke prevention>detection).

OUT / project-supplied (deferred): the runnable metrics engine — ship the **spec only**, not code
(doubly project-specific: stack + analytics provider); a standalone `review-system.md` scaffold —
**folded into the `/decide` skill**, which is the process system-of-record (one process
home); the domain layer — advisor personas, thresholds, the Sacred file list, render harnesses —
left for each consumer's `.claude/agents/` + CLAUDE.md.

## Justification
Second-consumer test (YAGNI): extract only what a second consumer needs. A runnable metrics engine
would couple the plugin to a stack + analytics provider; a language-neutral contract + a
provider-swap note serves any stack. Folding review-system.md into the skill avoids two process
homes (in-repo drift). adr-lint is the exception that ships runnable — node is the one universal
runtime, no app coupling.

## Assumptions
- [verified] `adr-lint.mjs` runs green on this corpus; its decision-logic test passes.
- [checkable] no structural agent/skill carries an ltconfig/oil&gas cite (config-driven targets) — gate verifies.
- [checkable-doc] the retrospect "process doc" references were retargeted to the skill (no dangling scaffold).
- [unverifiable] a second consumer needs no runnable metrics engine — REOPEN-IF one asks (shared register, README.md).

## Rejected alternatives
- Scaffold a standalone `review-system.md` — two process homes; the skill already declares itself the SoR.
- Ship the runnable metrics engine — doubly non-generic; the spec + provider-swap note suffices.
- Skip the in-repo ADR — forgoes dogfooding the framework on its own extraction; the request asked for it.

## Revisit triggers
- A second consumer needs the runnable metrics engine (then port ltconfig's `analyze()` behind the adapter seam).
- The plugin's `adr-template.md` diverges from ltconfig's in a way that matters to a consumer.
