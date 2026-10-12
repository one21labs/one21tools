---
id: 0100
title: "G<8 shortfall (#322): author one more blind round, then retire whatever still falls short"
status: accepted
tier: lite
summary: "ADR 0095 trigger 2 fired for 4 (skill, model) pairs. Author blind tasks once more for code-standards, optimizing-context, and building-skills on Sonnet, and run a fresh grid. Pre-registered stop: any pair still below G=8 afterwards loses its measured claim, with no third authoring round."
---

# 0100 — G<8 shortfall: author once, then retire

- Decision: owner, 12-Oct-2026, chose to spend the unspent ~$54 of that day's $100 cap. Blind-author
  ids 11+ (code-standards 6, optimizing-context 10, building-skills 3), prescreen them bare on
  both models, and run a FRESH grid over all survivors for those pairs. Any pair still below G=8
  after that batch is recorded as unmeasured. Its diagnostic numbers may still be cited as
  diagnostic. There is no third authoring round.
- Why: code-standards cleared zero on both models at G=6-7, so this is a likely-real claim 1-2
  tasks short. Estimated cost, from the 12-Oct per-cell costs: under $25.
- Rejected: retiring optimizing-context now. Its Opus null is G=5 and diagnostic, and its Sonnet
  direction (+0.10) is unresolved at about $10 marginal cost. Grading only the new tasks and
  pooling them with the 12-Oct cells: pooling across batches is chosen after seeing G, and a
  fresh grid costs little more.
- Reopen-if: the new blind tasks saturate at or above the 12-Oct blind rate (8 of 16 on Opus). If
  so, authoring is not converging, so retire instead of trying again.
- Enforced: `benchmarks/2026-10-12-g8-shortfall/metadata.json` (pre-registered stop rule)
