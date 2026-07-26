---
id: 0046
title: "Poka-yoke against altitude/restatement: deterministic lint + sharpened review + pointer-only rule"
status: accepted
tier: lite
summary: "Three thin layers, one artifact each: a zero-dep literal-overlap lint (scripts/check-restatement.mjs, fixture=test, one gates.yml line) gate-blocks the literal class; a one-line sharpened muda-review prompt covers the paraphrase class pre-merge; a pointer-only cross-reference row in ssot-enforcement.md is the authoring rule. The 14 offending ADR<->reference pairs were fixed in the same PR so the lint ships clean with no baseline. Rejected a specialized agent and a baseline/debt register — simplest set that works."
---

# 0046 — Poka-yoke against altitude/restatement (one-home)

- Decision: (1) literal class -> a zero-dep lint at `scripts/check-restatement.mjs`; the
  known-truth fixture is its test. Fixed the 14 offending pairs in the same PR — no
  baseline.json. (2) paraphrase class -> one sharpened line in
  `pdca-workflow/templates/claude-review.yml` naming the failure mode; residual stays with
  trigger-based audits (ADR 0039). (3) authoring rule -> one ssot-enforcement.md row: a
  cross-reference carries an ID/path, zero restated content — the lower home owns the
  operational text, the ADR keeps only the decision delta.
- Why: simplest set covering both classes pre-merge — a deterministic script for the decidable
  literal class, a prompt cue for the semantic class. Fixing the pairs in-PR removes the only
  reason a baseline would exist.
- Rejected: a specialized restatement-finder agent (owner directive "no Rube Goldberg"); a
  baseline/debt register (unnecessary once fixed in-PR); lint in validate.py (wrong scope);
  jscpd/npm tools (violate zero-dep).
- Reopen-if: a paraphrase restatement ships despite the prompt -> reconsider a semantic surface.
- Enforced: `check-restatement.mjs`; `claude-review.yml`; `ssot-enforcement.md`.

## Act
- [outcome] verified — lint green on the cleaned corpus.
