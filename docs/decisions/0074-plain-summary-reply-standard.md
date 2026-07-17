---
id: 0074
title: "Reply-summary standard: one plain-language summary, ~100 words, cap 350"
status: accepted
tier: lite
summary: "Owner directive (17-Jul, quoted): replace the TL;DR + ELI15 dual summary with ONE concise plain-language summary — 'as short as possible... target 100 words', hard cap 300-350 — covering what was done and how it helped, standard for all who use pdca-workflow. Shipped as an output style: repo .claude/output-styles/plain-summary.md (dogfooded) + pdca-workflow/templates/plain-summary.md offered by /pdca-init."
---

# 0074 — one plain-language reply summary

- Decision: every substantive assistant reply ends with a single **Summary** section — target
  ~100 words, hard cap 350, outcome first, plain sentences, deviations stated, no padding —
  replacing the TL;DR/ELI15 split. The style file is the SSoT for the rules.
- Why: owner-directed (asked, quoted — not inferred), informed by this session's observed
  failure mode: the dual format restated everything twice and the plain-language half was
  routinely the clearer one. Word-cap (not chars) because the consumer is human attention,
  not a context window — budget in the unit the consumer pays.
- Enforced: `.claude/output-styles/plain-summary.md` (this repo, `outputStyle` in
  .claude/settings.json) and `pdca-workflow/templates/plain-summary.md` (consumers, offered by
  /pdca-init step 5). Convention, not a gate — no linter counts reply words.
