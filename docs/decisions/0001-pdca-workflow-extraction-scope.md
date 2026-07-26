---
id: 0001
title: "pdca-workflow extraction scope"
status: accepted
tier: lite
summary: "Generic framework in; domain layer + runnable metrics engine + standalone review-system.md out"
---

# 0001 — pdca-workflow extraction scope

- Decision: generic framework IN (shipped by the plugin): the advise->decide->verify topology;
  structural agents (pm, tech-lead, red-team, verifier, retrospect) stripped of source-repo cites;
  the three skills; the ADR system + canonical template (frontmatter-cataloged, no index,
  version-agnostic, rationalize-in-place); a runnable zero-dep `adr-lint.mjs` + its decision-logic
  test; the `metrics-engine.md` analyze() contract (spec only); an opt-in `claude-review.yml`
  template; the principles (cite-or-silence, fresh-eyes, verify-before-acting, lowest-home
  routing, poka-yoke). OUT / project-supplied: a runnable metrics engine (doubly project-specific
  — stack + analytics provider); a standalone `review-system.md` scaffold (folded into the
  `/decide` skill, one process home); the domain layer (advisor personas, thresholds, a Sacred
  file list) — left to each consumer's `.claude/agents/` + CLAUDE.md.
- Why: second-consumer test (YAGNI) — extract only what a second consumer needs. A runnable
  metrics engine would couple the plugin to one stack/provider; a language-neutral contract serves
  any stack. adr-lint ships runnable because node is universal, no app coupling.
- Rejected: a standalone `review-system.md` scaffold — two process homes; ship the runnable
  metrics engine — doubly non-generic; skip the in-repo ADR — forgoes dogfooding the framework.
- Reopen-if: a second consumer needs the runnable metrics engine -> port the source's `analyze()`
  behind the adapter seam.
- Enforced: `pdca-workflow/scripts/adr-lint.mjs` (+ its test) runs green on this corpus;
  `pdca-workflow/skills/decide/SKILL.md` is the sole process home.
