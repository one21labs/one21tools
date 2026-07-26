---
id: 0010
title: "Skill toolkit scripts stay Python; reject cross-runtime migration"
status: accepted
tier: lite
summary: "Keep the building-skills scripts Python; reject Python->JS/TS migration. The migration's 'one gate owns all caps' prize is undesirable: validate.py and char-budget.mjs live in independently-installable plugins ADR 0009 deliberately decoupled. The genuine consolidation is intra-Python: extract validate_name into validate.py so init.py stops re-implementing it."
---

# 0010 — skill toolkit scripts stay Python

- Decision: keep validate.py/init.py/package.py/validate_test.py Python; reject migrating to
  JS/TS. Scripts split by ROLE: repo-governance gates are node per ADR 0001; the skill-authoring
  toolkit ships inside `dev-skills` for authors to run + copy, Python by upstream skill-creator
  lineage. The real consolidation is intra-Python: extract `validate_name` out of `validate_skill`
  in validate.py (tests-first), then have init.py import it instead of re-implementing it.
- Why: the migration's prize — one shared cap constant across validate.py and char-budget.mjs —
  is undesirable: the two files live in independently installable plugins (`dev-skills`,
  `pdca-workflow`) ADR 0009 deliberately decoupled; unifying caps would CREATE that dependency.
- Rejected: migrate all three to .mjs for one-gate SSoT (re-litigates 0009) — rewrite in TS
  (needs a build step) — bare import with no extraction (`validate_name` isn't standalone today).
- Reopen-if: `dev-skills` and `pdca-workflow` merge into one plugin.
- Enforced: `skills/building-skills/scripts/validate.py`, `validate_test.py`.
