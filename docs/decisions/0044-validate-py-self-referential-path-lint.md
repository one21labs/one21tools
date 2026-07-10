---
id: 0044
title: "validate.py flags self-referential repo-anchored script paths in skill content"
status: accepted
summary: "Add an R6 lint to validate.py: flag a path prefixing the skill's OWN folder name before /scripts/ (skills/<folder_name>/scripts/... or <folder_name>/scripts/...), which breaks in an installed plugin. Anchored on skill_path.name so cross-skill refs (a different folder) are excluded; adds an info-string-aware fenced-block scanner (not zero machinery); two escape hatches ship WITH it (runnable-block-only scope + inline validate:allow-self-path marker) so building-skills can still teach the anti-pattern; validate_test.py covers flagged + not-flagged cases (#115)."
---

# 0044 — validate.py flags self-referential repo-anchored script paths in skill content

- Date: 2026-07-10
- Owner: PM
- Panel: lean-process-engineer, session-operator, plugin-adopter.
- Context: The defect fixed in fix-building-skills-paths recurred within its own audit: commands in SKILL.md/references/*.md anchored as `skills/<this-skill>/scripts/…` break in an installed plugin (the `skills/<name>/` prefix exists only in the source repo) (#115). validate.py's R6 already walks references/*.md (validate.py:251-254) and binds folder_name = skill_path.name (:150), so the lint reuses the existing walk — but it adds a real new component: an info-string-aware fenced-code-block scanner (R6 today reads raw lines for emoji/char-cap, not code blocks), so "no new machinery" overstates it.

## Decision
Add an R6 lint: flag a path prefixing the skill's OWN folder name immediately before `/scripts/` (i.e. `skills/<folder_name>/scripts/…` or `<folder_name>/scripts/…`), anchored on `skill_path.name` so a cross-skill reference (a DIFFERENT folder) is excluded. Two escape hatches ship WITH the lint (not deferred), because building-skills' own docs will legitimately show this path as a worked anti-pattern:
1. **Scope to RUNNABLE fenced blocks only** — info-string `bash`/`sh`/`shell`/`console`; a path shown for teaching sits in a ```text/unlabeled block or inline prose and is not flagged.
2. **Inline override** — a `# validate:allow-self-path` marker on the offending line suppresses the flag for the rare runnable block that must display the pattern.
Ship with validate_test.py cases: the fix-building-skills-paths defect (flagged), a cross-skill ref (not flagged), and each escape hatch (not flagged). Never rule.

## Justification
Verified mechanically safe on the cross-skill axis: validate_skill walks only the skill's own SKILL.md + references/*.md (:251-254) and matches its own folder name (:150), so it structurally cannot false-positive on a cross-skill ref (different folder name). The remaining false-positive — building-skills teaching the pattern as an anti-pattern in its OWN docs (which the lint's own-name anchor WOULD catch) — is killed by the two escape hatches shipped with the lint, not deferred. The convention is already bare `scripts/foo.py` (validation-rules.md, SKILL.md examples), so the rule flags a real portability break. Low-moderate effort (R6 walk reused, fenced-block scanner added), low risk (own-name anchor + runnable-block scope + inline override), moderate value (catches a proven-recurring class).

## Assumptions
- [verified] validate.py R6 walks the skill's own references/*.md (:251-254); folder_name = skill_path.name (:150); scripts walked via rglob (:242) — read 2026-07-10; structurally own-scoped.
- [checkable] zero current matches across the shipped skills post-fix (convention is already bare scripts/…) — owner: verifier; result: confirm by running the lint over skills/ at implementation; no known offender remains.
- [checkable] the lint fires on the fix-building-skills-paths pattern and NOT on a cross-skill reference to a different folder — owner: verifier; the validate_test.py case is the acceptance gate.

## Rejected alternatives
- Match any `skills/*/scripts/` path (not own-name-anchored) — false-positives on legitimate cross-skill references.
- Lint prose/tree diagrams too — a self-name path in an illustrative tree is not a runnable command; scope to fenced command blocks.

## Revisit triggers
- The two escape hatches prove insufficient for a real teaching case (e.g. a runnable example that must not carry the marker) → widen the override or the block-scope rule.
- A portability break slips through in a non-fenced surface (inline code the lint doesn't scan) → extend the scanner to inline spans.

## Act (post-ship — 2026-07-10)
- [outcome] zero current offenders corpus-wide and the #115 defect reproduces as a test case — verified (PR #130); both escape hatches shipped with the lint.
- [process] red-team B5 moved the escape hatches from a revisit trigger into the day-one cut.
