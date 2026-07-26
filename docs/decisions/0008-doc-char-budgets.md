---
id: 0008
title: "Doc-size budgets are char budgets, not line budgets"
status: accepted
summary: "Doc size is capped in chars, not lines (line caps are gameable by long lines): CLAUDE.md <=6,000, ADRs <=6,000 norm, enforced with no exemptions; caps SSoT in char-budget.mjs, enforced by adr-lint; source headers + STRATEGY/ROADMAP/README left unbudgeted"
---

# 0008 — Doc-size budgets are char budgets, not line budgets

- Date: 2026-06-30
- Owner: PM
- Context: the ADR size budget was a LINE cap (`adr-lint` `--budget=70`), gameable by cramming
  more onto longer lines — it measures layout, not the signal/token cost the budget targets
  (`0006-retrospect-agent-model-tier.md` passed at 70 lines / 8,813 chars).

## Decision
Budget docs in CHARS, not lines. Caps: `CLAUDE.md` <=6,000 (the always-loaded layer); ADRs
<=6,000 norm (full tier; lite tier <=2,000 per ADR 0092). Caps + the over-budget predicate are the
SSoT in `pdca-workflow/scripts/char-budget.mjs`; enforced by `adr-lint.mjs` (the corpus +
`oversizeDocs()` over `CLAUDE.md`), unit-tested in `adr-lint.test.mjs`/`char-budget.test.mjs`. No
exemptions: over-budget records are rewritten under the cap, never grandfathered. NOT budgeted:
source header comments, `STRATEGY.md`, `ROADMAP.md`, `README.md`. Budget system home:
`pdca-workflow/skills/decide/references/doc-budgets.md`.

## Justification
A char count can't be gamed by long lines and captures the real intent (signal/token efficiency)
with no API call in CI. Rewrite-under-budget beats a grandfather allowlist while only a couple of
records are ever over cap at once. Source headers aren't budgeted: their failure mode is drift,
not length.

## Assumptions
- [unverifiable] 6,000 is the right per-file cap (efficiency without undue restriction). REOPEN-IF
  a legitimate addition can't fit without cutting a load-bearing crux -> revisit the cap or the
  always-loaded set.

## Rejected alternatives
- Keep line budgets — gameable by long lines.
- Grandfather over-budget legacy records — correct only once MANY are over budget at once.
- Token budgets — need `count_tokens` (no API in CI) and are model-specific; chars are the
  ungameable, CI-checkable proxy.

## Revisit triggers
- A legitimate `CLAUDE.md` addition can't fit <=6,000 without cutting a crux.
- The corpus accumulates MANY settled records over the PER-FILE cap at once -> re-evaluate a
  grandfather allowlist for that batch.
