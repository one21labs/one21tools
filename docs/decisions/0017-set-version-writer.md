---
id: 0017
title: "set-version.mjs: one writer for registry versions, no second checker"
status: superseded by 0075
tier: lite
summary: "A version writer got no companion drift-checker: adr-lint's manifestDrift stayed the one predicate. The writer itself is gone (ADR 0075 removed version fields entirely); the surviving rule is that a writer does not earn a second checker."
---

# 0017 — set-version writer for the plugin registry (superseded)

- Residual rule: a writer does not earn a mirror-checker. `manifestDrift` in adr-lint was, and
  stays, the one drift predicate — a second `--check` mode would have been a second home for the
  same question.
- Superseded: ADR 0075 deleted version fields outright, so there is no version left to write.
- Enforced: none — retired; see `0075-no-plugin-version-fields.md`.
