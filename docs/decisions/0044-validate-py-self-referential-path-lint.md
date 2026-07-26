---
id: 0044
title: "validate.py flags self-referential repo-anchored script paths in skill content"
status: accepted
tier: lite
summary: "Add an R6 lint to validate.py: flag a path prefixing the skill's OWN folder name before /scripts/ (skills/<folder_name>/scripts/... or <folder_name>/scripts/...), which breaks in an installed plugin. Anchored on skill_path.name so cross-skill refs are excluded; two escape hatches ship with it (runnable-block-only scope + inline validate:allow-self-path marker) so building-skills can still teach the anti-pattern."
---

# 0044 — validate.py flags self-referential repo-anchored script paths

- Decision: R6 flags any path prefixing the skill's own folder name immediately before
  `/scripts/`, anchored on `skill_path.name` so a cross-skill reference (a different folder) is
  excluded. Two escape hatches ship with it, not deferred: (1) scope to runnable fenced blocks
  only (`bash`/`sh`/`shell`/`console`) — a teaching example in prose or unlabeled block isn't
  flagged; (2) an inline allow marker suppresses the flag for a runnable block that must
  display the pattern. Shipped with `validate_test.py` cases for the flagged defect, a
  cross-skill reference, and each escape hatch.
- Why: the path-portability defect recurred within its own audit (#115) — a self-referenced
  path breaks once installed elsewhere, since that prefix exists only in the source repo. The
  own-name anchor makes the lint structurally incapable of false-positiving cross-skill.
- Rejected: match any `skills/*/scripts/` path, not own-name-anchored — false-positives on
  legitimate cross-skill references. Lint prose/tree diagrams too — illustrative, not runnable.
- Reopen-if: the escape hatches prove insufficient for a real teaching case -> widen the
  override. A break slips through a non-fenced surface (inline code) -> extend the scanner.
- Enforced: `skills/building-skills/scripts/validate.py` R6 + `validate_test.py`.
