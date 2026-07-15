# ADR corpus linter — spec

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
6. **Lite tier** (`tier: lite` frontmatter — settled decisions, ADR 0020) — exempt from the
   falsifiability gate (settled = nothing left to test), but REJECTED if it carries a revisit
   trigger or open assumption (`REOPEN-IF`, a `## Revisit triggers` section, or an `[unverifiable]`
   bullet): that means the decision isn't actually settled, so it must graduate to a full ADR.
7. **Budget** — no ADR exceeds its char budget: full ADRs default to 6,000 (configurable via
   `--budget`), lite ADRs to 1,500 (`LITE_ADR_CHAR_BUDGET`). Cap + predicate SSoT in
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
12. **Decision-set connectivity** (`decisionSetProblems`, ADR 0051; opt-in via
    `--new-adrs=<ids-or-paths>`) — when a change adds MORE THAN ONE new ADR, they must be one
    connected component of the undirected cite graph (an edge = either record cites the other):
    entangled records ship together, unrelated decisions ship separately. Flag absent or a single
    new ADR = skipped, so only the PR-context CI step (which passes the diff-added files) can fire it.
    Because CI fires this only at PR time, a long-lived branch gets no connectivity feedback while
    it accumulates ADRs — before opening a PR that adds more than one, run it locally:
    `adr-lint.mjs docs/decisions --new-adrs=<the added ids>`.

A failure prints the offending files and exits non-zero; a clean corpus exits zero.

## Run / install
```
# never pipe — gate-pipe-guard denies it; output is short enough to read unpiped
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
