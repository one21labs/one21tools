---
id: 0008
title: "Doc-size budgets are char budgets, not line budgets"
status: accepted
summary: "Doc size is capped in chars, not lines (line caps are gameable by long lines): CLAUDE.md and the ADR tiers cap by the named constants in char-budget.mjs, no exemptions, enforced by adr-lint; source headers + STRATEGY/ROADMAP/README left unbudgeted"
---

# 0008 — Doc-size budgets are char budgets, not line budgets

- Date: 2026-06-30
- Owner: PM
- Context: a LINE cap measures layout, not the signal/token cost the budget targets.

## Decision
Budget docs in CHARS, not lines. Cap VALUES + the over-budget predicate are SSoT in
`pdca-workflow/scripts/char-budget.mjs` (`DOC_BUDGETS` for `CLAUDE.md`, the always-loaded layer;
`ADR_CHAR_BUDGET` full tier, `LITE_ADR_CHAR_BUDGET` lite, ADR 0092), enforced by `adr-lint.mjs`
(the corpus + `oversizeDocs()`), unit-tested in `adr-lint.test.mjs`/`char-budget.test.mjs`. No
exemptions: over-budget records are rewritten under the cap, never grandfathered. NOT budgeted:
source header comments, `STRATEGY.md`, `ROADMAP.md`, `README.md`. Budget system home:
`pdca-workflow/skills/decide/references/doc-budgets.md`.

## Justification
A char count can't be gamed by long lines and captures the real intent (signal/token efficiency)
with no API call in CI. Rewrite-under-budget beats a grandfather allowlist while only a couple of
records are ever over cap at once. Source headers aren't budgeted: their failure mode is drift,
not length.

## Assumptions
- [unverifiable] the per-file caps are right (efficiency without undue restriction). REOPEN-IF
  a legitimate addition can't fit without cutting a load-bearing crux -> revisit the cap or the
  always-loaded set.

## Rejected alternatives
- Keep line budgets — gameable by long lines.
- Grandfather over-budget legacy records — correct only once MANY are over budget at once.
- Token budgets — need `count_tokens` (no API in CI) and are model-specific; chars are the
  ungameable, CI-checkable proxy.

## Revisit triggers
- A legitimate `CLAUDE.md` addition can't fit its cap without cutting a crux.
- The corpus accumulates MANY settled records over the PER-FILE cap at once -> re-evaluate a
  grandfather allowlist for that batch.
