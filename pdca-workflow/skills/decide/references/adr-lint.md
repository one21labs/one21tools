# ADR corpus linter — spec

## Table of Contents
- [Frontmatter schema](#frontmatter-schema-every-adr-starts-with-this)
- [The checks](#the-checks-over-docsdecisionsmd)
- [Run / install](#run--install)

The ADR system is an append-only, manually-numbered corpus. The cleanest poka-yoke is
**prevention over detection**: there is no materialized index to keep in sync — a mirror you
don't maintain can't drift, so the ADR files ARE the catalog (skim them by grepping the
`summary` / `status` frontmatter). `adr-lint` guards what prevention can't design away: bad
frontmatter, id collisions across parallel branches, release-version coupling, dangling cites,
unfalsifiable decisions, and budget rot. Per "no process-gating script without a test of its
decision logic," it ships with one (`scripts/adr-lint.test.mjs`).

This file is the **spec** — the authoritative, numbered guard list. A runnable node reference
ships at `scripts/adr-lint.mjs` (zero-dependency, cross-platform; its header points back here
rather than re-listing the guards); a consumer on another stack reimplements the checks against
this list.

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
4. **No dangling cites** — every `ADR NNNN` / `[NNNN]` / `superseded by NNNN` cited inside an ADR
   resolves to a file on disk (the renumber/fold catcher; a self-cite is fine).
5. **Falsifiability (Plan-phase criterion-minting gate)** — every FULL ADR states at least one
   criterion the Check can later test: a `- [checkable]`/`- [checkable-doc]`/`- [contradiction]`
   assumption bullet, OR a `- [unverifiable]` paired with a same-bullet REOPEN-IF (revisitable on a
   signal). An ADR with none is **UNFALSIFIABLE**. This checks PRESENCE of a real tagged bullet (not
   a prose mention); whether a stated criterion is genuinely falsifiable is the PM's/gate's semantic
   call, not lint's.
6. **Lite tier** (`tier: lite` frontmatter — the DEFAULT, ADR 0062/0092) — exempt from the
   falsifiability gate (nothing left to test), and it MAY carry a `Reopen-if:` line. REJECTED if
   it carries the assumption machinery instead — a tagged bullet
   (`[unverifiable]`/`[checkable]`/`[checkable-doc]`/`[contradiction]`/`[verified]`) or an
   `## Assumptions` section: that reasoning must survive, so it graduates to a full ADR.
   Positive bar (ADR 0087): the body must also carry an `Enforced:` line (settled = enforced
   somewhere findable — the lite shape in adr-template.md), and every file-like token it cites
   (a closed extension list: mjs/js/ts/md/sh/yml/yaml/json/py/txt) must resolve on disk: exact
   repo-relative path or basename anywhere in the tree (`.git`/`node_modules` excluded; a `:NN`
   line suffix is ignored). ALL unquoted occurrences of the marker are validated — a
   backtick-quoted mention is prose about the marker, not the marker, and satisfies nothing
   (first-occurrence-only would let prose shadow the real line; an UNQUOTED prose mention alone
   does still satisfy presence — accepted residual, it can never shadow token validation). A
   token-free free-form line ("absence", a CI-run description) passes — whether it truly
   enforces is review's semantic call, not lint's.
7. **Budget** — no ADR exceeds its char budget: caps live in `char-budget.mjs` (never restated here; configurable via
   `--budget`), lite ADRs to their own cap (`LITE_ADR_CHAR_BUDGET`). Cap + predicate SSoT in
   `char-budget.mjs`; full budget rationale (why chars not lines, no-exemptions rule) in
   `adr-template.md`'s Template section — canonical, not restated here. Advisory (ADR 0067,
   never fails): a `--new-adrs` full ADR past `ADR_CHAR_MARGIN` WARNs — the margin reserves
   `## Act` room; lite and legacy ADRs exempt.
8. **Amendment backlink** (ADR 0040) — an ADR that ACTIVELY amends another ("amends ADR NNNN") must
   be cited back from the amended ADR's own text; an unpointed amendment is invisible from the
   record it changes (adr-template.md "Rationalize in place"). A passive "amended by NNNN" already
   carries its own cite, so only the active voice is checked.

`main()` also runs guards outside the ADR corpus proper, sharing the same `lint`/`char-budget`
machinery:
9. **manifestDrift** — a field present in BOTH a marketplace plugin entry and that plugin's own
   `plugin.json` must be identical (`plugin.json` is the lower home; an entry-side omission is not
   drift).
10. **Agent checks** (`agentProblems`) — every agent prompt under `pdca-workflow/agents` and
    `.claude/agents` stays under `AGENT_CHAR_BUDGET`, and its frontmatter `name:` matches its
    filename.
11. **Named-doc budget** (`oversizeDocs`) — char-checks `CLAUDE.md` against `DOC_BUDGETS`.
12. **Decision-set advisory** (`decisionSetWarnings`, ADR 0051 as amended; opt-in via
    `--new-adrs=<ids-or-paths>`) — when a change adds MORE THAN ONE new ADR, cite-unconnected
    members (edge = either record cites the other) get a WARN, never a failure: the PR is the
    batching unit (a deliberate work package is fine); the WARN surfaces an accidental
    grab-bag at review. Flag absent or a single new ADR = nothing reported; only the
    PR-context CI step (which passes the diff-added files) emits it.

13. **Outcome vocabulary** (ADR 0079; a corpus check, numbered here to keep checks 1-12's
    historical numbers stable) — every `- [outcome]` row carries exactly ONE whole-word of
    `verified` / `violated` / `still-open`: the controlled input any metrics-engine consumer
    would classify on. A free-text synonym ("FALSIFIED") or a double-tag is
    unclassifiable — and a dropped miss reads as no miss.

14. **Stale status on recorded discharge** (ADR 0088; a corpus check) — a `;`-split clause of a
    line containing "discharg" that cites an ADR id existing on disk FAILS if that ADR's
    frontmatter is still `status: proposed`: the state-changing event was recorded into a
    sibling file and the target's status never flipped. The clause (not the whole line) is the
    unit, so an unrelated proposed cite sharing the line stays quiet; date-adjacent and
    unknown 4-digit tokens never match.
15. **Doc-indexed constant cross-check** (`docIndexDrift`, ADR 0088; a `main()` guard over every
    .md OUTSIDE the decisions dir) — a line that backtick-names a `char-budget.mjs` scalar
    constant (or `DOC_BUDGETS` plus a backticked filename matching a key's BASENAME) and contains
    a 3+-digit number must include that constant's current value: comma-insensitive,
    presence-direction only (extra numbers on the line are fine). The decisions dir is excluded
    because records legitimately hold as-of-decision numbers.

A failure prints the offending files and exits non-zero; a clean corpus exits zero.

## Run / install
```
# run it so the EXIT CODE survives: bare, or redirect to a file, or `set -o pipefail` first —
# a bare pipe reports the filter's status, not the gate's, and a red gate then reads green
node scripts/adr-lint.mjs                  # lints ./docs/decisions, char budget from char-budget.mjs
node scripts/adr-lint.mjs docs/decisions --budget=8000
node --test scripts/*.test.mjs             # the decision-logic tests (adr-lint + char-budget)
```

`/pdca-init`'s SKILL.md is the copy-set SSoT: it vendors this linter, its test, and their
`char-budget.mjs` dependency (+ test) into the consuming repo's `scripts/`, and points the project
at running it pre-merge / in CI.

**Project-specific guards (add locally).** A project with a roadmap/changelog + a versioned manifest
(e.g. `package.json`, `Cargo.toml`, a release tag) can also assert its tracker agrees with the shipped version, and that every
`ADR NNNN` cited in source resolves — both omitted here because a generic consumer may have neither.
