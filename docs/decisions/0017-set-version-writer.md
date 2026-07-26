---
id: 0017
title: "set-version.mjs: one writer for registry versions, no second checker"
status: superseded by 0075
tier: lite
summary: "A repo-governance script wrote a version to its ONE home (plugin.json when the plugin ships one, else the marketplace entry) — writer only, no duplicate drift-checker (adr-lint's manifestDrift stayed the one check). Superseded by ADR 0075: plugin manifests carry no version field at all, updates key on git content; set-version.mjs was deleted."
---

# 0017 — set-version writer for the plugin registry (superseded)

- Date: 2026-07-07
- Decision: `scripts/set-version.mjs` wrote a version to its one home per a fixed resolution rule (plugin.json if the plugin ships one, else the marketplace entry; derive-don't-mirror), with no `--check` mode — the drift check stayed adr-lint's `manifestDrift`, one predicate, one home.
- Superseded: ADR 0075 (2026-07-17) removed ALL version fields from every manifest — updates key on git content instead, so there is no version left to write. `set-version.mjs` and its test were deleted; this record stays for the rejected-alternatives history (why a second checker wasn't added here).
- Enforced: none — retired; see ADR 0075 for the current mechanism.
