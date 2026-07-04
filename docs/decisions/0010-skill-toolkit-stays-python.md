---
id: 0010
title: "Skill toolkit scripts stay Python; reject cross-runtime migration"
status: accepted
summary: "Keep the building-skills scripts (validate/init/package.py + validate_test.py) in Python; reject the Python->JS/TS migration. The migration's 'one gate owns all caps' prize is not just costly (ZIP writer, emoji-regex risk) but undesirable: validate.py (dev-skills plugin) and char-budget.mjs (pdca-workflow plugin) are independently-installable artifacts ADR 0009 deliberately decoupled — unifying their caps creates the cross-plugin dependency 0009 forbids. The genuine consolidation the ask gropes toward is intra-Python: extract validate_name into validate.py (tests-first) so init.py stops re-implementing the name rules."
---

# 0010 — Skill toolkit scripts stay Python

- Date: 2026-07-01
- Owner: PM
- Panel: opposing counsel on Call A (2 sonnet advisors — steelman-migrate + steelman-keep), never primed. Verifier + red-team ran the gate (reproduced the ImportError below).
- Context: the ask is to migrate the four `skills/building-skills/scripts/` files (validate.py, init.py, package.py, validate_test.py) Python->JS/TS one-by-one — days after ADR 0009 rejected "one gate for all caps" as impossible across two runtimes (0009:31). The crux: is dissolving that premise a legitimate revisit or a same-day re-litigation?

## Decision
Keep all four Python. Reject the migration (all four). **Reframe (not migrate-vs-keep):** the repo's scripts are two populations by ROLE — repo-governance gates (`adr-lint.mjs`, `char-budget.mjs`) are already node per ADR 0001 (node = the universal gate runtime); the skill-authoring toolkit (validate/init/package.py) ships inside the `dev-skills` plugin for authors to run + copy, is Python by Anthropic skill-creator lineage, and is taught as THE convention (`python .../validate.py|init.py|package.py`, SKILL.md:124,136,148). The genuine consolidation the ask gropes toward is intra-Python and in-scope: init.py:26-29,61-87 duplicates validate.py's name constants (validate.py:30,36,37) and re-implements `validate_name`, which validate.py inlines inside `validate_skill` (validate.py:106-138) — there is no standalone function to import today.

**Build (validate.py-side refactor, tests-first — one PR):** (i) EXTRACT `validate_name` from `validate_skill` in validate.py, keeping the folder-match check (:137) OUT of the shared function (init has no folder yet); (ii) ADD name-rule cases to validate_test.py (empty / XML / >64 / bad-char / edge + consecutive hyphens / reserved) BEFORE the dedup — it has none today; (iii) then init.py imports NAME_MAX/NAME_PATTERN/RESERVED_WORDS + the extracted `validate_name`, dropping its copies. `validate.py <dir>` + `node --test` green.

## Justification
The migration's headline prize — BODY_MAX_CHARS/REFERENCE_MAX_CHARS (validate.py:32,34) joining char-budget.mjs's DOC_BUDGETS as one cap SSoT — is not merely costly, it is UNDESIRABLE: validate.py lives in `dev-skills`, char-budget.mjs in `pdca-workflow` (marketplace.json:10-38) — independently-installable plugins that ADR 0009 point 3 deliberately decoupled ("no cross-plugin doc dependency"). Unifying their caps would CREATE the coupling 0009 avoided. That plugin boundary is the deeper reason under 0009's "unavoidable across two runtimes" (0009:22) — clarified, it strengthens keep. Sealing costs: package.py:47 needs a ZIP writer Node stdlib lacks (a dependency breaks the zero-dep norm both .mjs assert, char-budget.mjs:9-10; a hand-rolled writer is muda); validate.py:43-54's astral-plane emoji regex is a silent-regression hazard on a CLAUDE.md Never rule. No new fact forces reopening 0009.

## Assumptions
- **[checkable] WEAKEST: the skill toolkit is a Python-idiom asset authors run + copy** — SKILL.md:124,136,148 teach the `python` invocation as THE author convention, mirroring the upstream skill-creator toolkit; keeping Python preserves that match, migration diverges. TEST (verifier): those lines + workflows.md teach it; no in-repo consumer requires a JS-only runtime.
- [verified] validate.py's caps (dev-skills) and char-budget.mjs's caps (pdca-workflow) are separate marketplace plugins — marketplace.json:10-38; 0009 point 3 forbids a cross-plugin dependency.
- [checkable] the dedup preserves behavior — validate.py has NO standalone `validate_name` (inline in `validate_skill`, :106-138) and validate_test.py has NO name-rule coverage today, so the extract-then-test-then-import order (build above) is mandatory; a bare import would ImportError. — owner: verifier.
- [unverifiable] Anthropic's upstream skill-creator toolkit stays Python. REOPEN-IF it goes JS.

## Rejected alternatives
- Migrate all three to .mjs for one-gate SSoT — the prize is cross-plugin coupling 0009 forbids; re-litigates a same-day ADR with no new fact.
- Migrate validate.py only — orphans init.py's Python twin or forces porting two files; still hits the plugin boundary.
- Rewrite in TS — needs a build step; CLAUDE.md: "no app, build, or deploy."
- Bare `from validate import validate_name` with no extraction — ImportError (no such function today); dedup-before-tests would ship an untested refactor of a gating script (Never rule).

## Revisit triggers
- `dev-skills` and `pdca-workflow` merge into one plugin/runtime, OR a consumer needs the toolkit in a JS-only environment, OR Anthropic's skill-creator toolkit goes JS -> revisit the runtime.
