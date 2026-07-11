---
id: 0046
title: "Poka-yoke against altitude/restatement: deterministic lint + sharpened review + pointer-only rule"
status: accepted
summary: "Three thin layers, one artifact each: a zero-dep literal-overlap lint (repo scripts/check-restatement.mjs, fixture=test, one gates.yml line) gate-blocks the literal class; a one-line sharpened muda-review prompt naming the restatement failure mode covers the paraphrase class before merge (residual → trigger-audits, ADR 0039); a pointer-only cross-reference row in ssot-enforcement.md is the authoring rule. The 14 offending ADR↔reference pairs are fixed in the SAME PR (the lower/shipped home owns the operational text; the ADR keeps the decision delta + a cite), so the lint runs clean with no baseline. Reject a specialized agent — simplest set that works."
---

# 0046 — Poka-yoke against altitude/restatement (one-home)

- Date: 2026-07-10
- Owner: PM
- Panel: counsel A (mechanize), counsel B (don't-mechanize), lean-process-engineer (poka-yoke hierarchy); a run experiment (zero-dep shingle detector); owner directives (specialized-agent question; then "simplest solution is best — no Rube Goldberg").
- Context: Owner asked how to PERMANENTLY poka-yoke one-home/altitude restatement (a peer/higher doc carrying a span the owning home holds). Trigger: while implementing anti-duplication ADR 0041, the orchestrator introduced two altitude violations in benchmarks/README.md (a literal dup; a paraphrase gloss of ADR 0026), fixed PR #141. The live muda-review flagged neither (counsel A cites PR #127) — its one-home prompt line is generic. An experiment ran a zero-dep shingle detector over all repo .md, catching the literal class and finding a systemic ADR↔reference class.

## Decision
Three thin layers, one artifact each; no third semantic surface, no baseline, no deferred cleanup.
1. **Literal class → a zero-dep lint** at repo `scripts/check-restatement.mjs` (window=12 words, code-fences stripped, inline structural allowlist for the two intentional classes: agent personas, pdca-init template pairs). One gates.yml line; the known-truth fixture is its test (Never rule). HOME repo scripts/ (whole-tree scan + repo-specific allowlist = instance tooling, like check-workflow.mjs; ADR 0038). **Fix the 14 offending pairs (18 spans) in the SAME PR** so the lint runs clean on a clean corpus — no baseline.json, no debt register.
2. **Paraphrase class → one sharpened muda-review line.** Add to `pdca-workflow/templates/claude-review.yml` a single line naming the restatement failure mode (a peer/higher doc carrying a span the owning home holds). Pre-merge, it catches what the n-gram lint can't; the corpus-scoped residual stays with trigger-based audits (ADR 0039 item 1). Re-copy to the deployed .github/workflows instance.
3. **Authoring rule → one ssot-enforcement.md row:** a cross-reference carries an ID/path, zero restated content (formalizes PR #141; ships + travels, ADR 0038).

The RULE for the ADR↔reference class the experiment found (verified 0023↔empirical-evals.md, 0008↔doc-budgets.md; 14 pairs total): the lower/shipped home owns the operational text; the ADR keeps only the decision delta + a cite. Applied now (layer 1's same-PR fix), not filed.

## Justification
Simplest set that covers both failure classes at a pre-merge gate: a deterministic script for the decidable literal class (MEASURED — recall reproduced on #88, FP confined to two allowlistable classes; clears ADR 0024), a one-line prompt cue for the semantic/paraphrase class, one authoring row. Fixing the 14 pairs in-PR removes the only reason a baseline/debt-allowlist would exist — the corpus is clean, so the lint is green with nothing to suppress (the agent + baseline machinery is rejected below on the owner's "no Rube Goldberg"). **Overruled counsel B's don't-mechanize** — its [verified] point (the #141 violations predate the 0038/0039 merges) stands, but the case is the SYSTEMIC class + the whiff, not the n=1.

## Assumptions
- [verified] the systemic ADR↔reference class is real — grep confirmed verbatim: "a run counts toward a keep/cut verdict only if" (0023:16 ↔ empirical-evals.md:165); "a char count can't be gamed by long lines" (0008:32 ↔ doc-budgets.md:49).
- [verified] gates.yml globs scripts/*.test.mjs (:35) and runs scripts/check-*.mjs (:41,:47); adr-lint.mjs is zero-dep by design — a zero-dep scripts/ lint + fixture fits.
- [checkable] the detector reproduces the known-truth fixture (recall on #88 literals; FP only in the two allowlisted classes) AND, after the same-PR fix, runs clean over the corpus (the 14 pairs resolved) — owner: verifier re-runs the prototype as the committed test on the fixed tree.
- [unverifiable] the one-line prompt + trigger-audits acceptably cover the paraphrase class — REOPEN-IF a paraphrase restatement ships to main after this lands.

## Rejected alternatives
- A specialized restatement-finder agent — a third semantic surface; owner directive (simplest is best); its authoring-moment value is recall-dependent and both classes are caught pre-merge without it.
- A baseline/debt register or a separate deferred cleanup issue — unnecessary once the 14 pairs are fixed in-PR; the deferral/machinery is the Rube Goldberg the directive forbids.
- Lint in validate.py (single-skill-scoped) or vendored pdca-workflow/scripts (whole-tree scanner + allowlist are instance-specific).
- jscpd/npm copy-paste tools — violate the zero-dep gate constraint.

## Revisit triggers
- A literal restatement ships to main past the lint → widen the window or fix the allowlist (the falsifiable criterion).
- A paraphrase restatement ships despite the prompt + audits → reconsider a semantic surface (the agent question reopens).
- The structural allowlist grows unmaintainably → reconsider the operating point.

## Act (post-ship — 2026-07-10)
- [outcome] lint green on the cleaned corpus (18 spans fixed in-PR); the known-truth fixture is its test.
