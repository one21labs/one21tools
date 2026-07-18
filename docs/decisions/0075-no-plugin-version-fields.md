---
id: 0075
title: "Delete plugin version fields — updates key on git content (supersedes 0017/0048 machinery)"
status: accepted
tier: lite
summary: "All version fields removed from marketplace.json (metadata + entries) and every plugin.json; set-version.mjs + test deleted. Owner decision 17-Jul-2026, grounded in current docs: the field is optional everywhere, and a SET version only delivers updates when bumped — a forgotten bump silently BLOCKS consumers (PR #231's shipped description was invisible to installed copies). Omitted, updates key on the git commit SHA: nothing to maintain, forget, or collide on."
---

# 0075 — no plugin version fields

- Decision: no `version` field in any plugin manifest; updates are git-content-keyed (omitted
  version = commit SHA). set-version.mjs retired; ADR 0017's writer role and 0048's bump
  cadence are mooted — the poka-yoke rung above both (delete the mirror, don't resync it).
- Why: 0048's trigger died in the 16-Jul ceremony cut; #231 then shipped un-bumped — which the
  docs reveal is update-BLOCKING, not cosmetic. Every alternative cadence exists to maintain a
  field whose only function here is that failure mode. Residuals: no human-readable release
  numbers; non-plugin commits surface as phantom updates — fine when main is the publish event.
- Enforced: absence (nothing to drift; manifestDrift treats omission as non-drift by design).
  Revisit: external consumers needing stability pins → reintroduce explicit versions.
