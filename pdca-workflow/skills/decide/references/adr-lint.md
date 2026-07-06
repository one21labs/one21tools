# ADR corpus linter — spec

The ADR system is an append-only, manually-numbered corpus. The cleanest poka-yoke is
**prevention over detection**: there is no materialized index to keep in sync — a mirror you
don't maintain can't drift, so the ADR files ARE the catalog (skim them by grepping the
`summary` / `status` frontmatter). `adr-lint` guards what prevention can't design away: bad
frontmatter, id collisions across parallel branches, release-version coupling, dangling cites,
unfalsifiable decisions, and budget rot. Per "no process-gating script without a test of its
decision logic," it ships with one (`scripts/adr-lint.test.mjs`).

This file is the **spec**. A runnable node reference ships at `scripts/adr-lint.mjs`
(zero-dependency, cross-platform); a consumer on another stack reimplements the checks against it.

## Frontmatter schema (every ADR starts with this)
```
---
id: NNNN                 # 4 digits, matches the filename prefix
title: "<short title>"
status: proposed         # proposed | accepted | superseded by NNNN
summary: "<one line for the skim catalog>"
---
```

## The checks (over `docs/decisions/*.md`)
1. **Frontmatter valid** — each ADR has frontmatter with a 4-digit `id` that matches its filename,
   plus a non-empty `title` and `summary` (the catalog skim values).
2. **Ids unique** — no two files share an `id` (parallel branches grabbing the same int).
3. **Version-agnostic** — no `vX.Y.Z` release version anywhere in an ADR; name the cut/feature, not
   the release. (Release versions live in the project's tracker; sequence + ship-state derive from the ADR corpus — see adr-template.md.)
4. **No dangling cites** — every `ADR NNNN` / `[NNNN]` cited inside an ADR resolves to a file on
   disk (the renumber/fold catcher; a self-cite is fine).
5. **Falsifiability (Plan-phase criterion-minting gate)** — every ADR states at least one criterion
   the Check can later test: a `- [checkable]`/`- [checkable-doc]`/`- [contradiction]` assumption
   bullet, OR a `- [unverifiable]` paired with a REOPEN-IF (revisitable on a signal). An ADR with
   none is **UNFALSIFIABLE**. This checks PRESENCE of a real tagged bullet (not a prose mention);
   whether a stated criterion is genuinely falsifiable is the PM's/gate's semantic call, not lint's.
6. **Budget** — no new/edited ADR exceeds the char budget (default 6,000 — the norm from
   `adr-template.md`; cap + predicate SSoT in `char-budget.mjs`;
   configurable via `--budget`). A char count can't be gamed by long lines (see ADR 0008). No
   exemptions — an over-budget ADR is rewritten under the cap, not grandfathered. Over budget = bloat or a missed
   lower home. `main()` also char-checks the named docs (`CLAUDE.md`) via `oversizeDocs()`.

A failure prints the offending files and exits non-zero; a clean corpus exits zero.

## Run / install
```
node scripts/adr-lint.mjs                  # lints ./docs/decisions, char budget from char-budget.mjs
node scripts/adr-lint.mjs docs/decisions --budget=8000
node --test scripts/*.test.mjs             # the decision-logic tests (adr-lint + char-budget)
```

`/pdca-init` copies `adr-lint.mjs` + `adr-lint.test.mjs` into the consuming repo's `scripts/` and
points the project at running it pre-merge / in CI.

**Project-specific guards (add locally).** A project with a roadmap/changelog + a versioned manifest
(e.g. `package.json`, `Cargo.toml`, a release tag) can also assert its tracker agrees with the shipped version, and that every
`ADR NNNN` cited in source resolves — both omitted here because a generic consumer may have neither.
