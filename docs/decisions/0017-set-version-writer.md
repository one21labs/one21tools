---
id: 0017
title: "set-version.mjs: one writer for registry versions, no second checker"
status: accepted
summary: "A repo-governance script (root scripts/, node zero-dep, tested) writes a version to its ONE home: plugin.json when the plugin ships one (marketplace entry syncs only if it redundantly states a version — derive-don't-mirror per ADR 0011), else the marketplace entry; target `marketplace` writes metadata.version. WRITER ONLY — the drift check stays adr-lint's manifestDrift; no duplicate gate. Idea ported from NeoLabHD/context-engineering-kit's make set-version, node-native."
---

# 0017 — set-version writer for the plugin registry

- Date: 2026-07-07
- Owner: PM
- Panel: owner-direct in a cross-repo review session (owner asked to port the version-command idea from the context-engineering-kit marketplace); gates (node tests, adr-lint) ran as Check.
- Context: versions live in three shapes — marketplace `metadata.version`, inline entry versions (dev-skills, engineering-skills), and pdca-workflow's plugin.json — all hand-edited. The manifests are Sacred ("a broken or duplicate entry breaks /plugin install", CLAUDE.md); a hand edit can fat-finger JSON or write the version to the wrong home, and adr-lint's manifestDrift only CATCHES the split after the fact. Prevent > detect.

## Decision
1. **`scripts/set-version.mjs` + `set-version.test.mjs`** at the repo root — the repo-governance population (node, zero-dep, per the ADR 0010 reframe), NOT inside a plugin dir: it operates on the registry, so shipping it to plugin consumers would be muda.
2. **Home-resolution rule (the decision logic, pure `plan()`):** target `marketplace` -> `metadata.version`; a plugin whose entry `source` has a `.claude-plugin/plugin.json` -> that file is the home, and the marketplace entry is synced ONLY if it already states a version (an omitting entry never gains one — derive-don't-mirror, ADR 0011); otherwise the marketplace entry IS the home. Rejects a malformed version; unknown targets throw with the valid list.
3. **Writer only.** The matching CHECK already gates in adr-lint (`manifestDrift`); a `--check` here would be a second home for the same predicate.
4. Wire `scripts/*.test.mjs` into the gates JS test step; one nav line in CLAUDE.md.

## Justification
Poka-yoke on Sacred files at near-zero cost (~100 lines, pure logic tested): the wrong-home mistake becomes unmakeable rather than caught-in-review. Port the proven shape (context-engineering-kit's make targets) without importing make — node is the runtime every consumer provably has (ADR 0010).

## Assumptions
- [verified] the drift predicate lives once — adr-lint.mjs `manifestDrift` is the gate; set-version.mjs contains no version-comparison check.
- [checkable] `plan()` respects derive-don't-mirror: the entry-without-version case is pinned by a test (an omitting entry never gains a version) and plan never mutates its inputs — owner: gates (node --test); result: green.
- [checkable] the script round-trips the real manifests (2-space indent + trailing newline; `git diff` shows only the version lines after a bump) — owner: verifier, run on the marketplace bump shipped with this ADR; result: clean.
- [unverifiable] a writer (not a git hook or CI auto-bump) is the right automation level — REOPEN-IF: a release ships with a forgotten bump twice; then consider a gates check tying the marketplace version to plugin changes.

## Rejected alternatives
- Port the Makefile — imports a make dependency for two commands; node already runs every gate.
- Add `--check` to the script — duplicates adr-lint's manifestDrift; two homes for one predicate drift.
- Auto-bump from a git hook — magic writes to Sacred files; a wrong auto-bump is worse than a missing one.
- Put it in pdca-workflow/scripts — ships registry tooling inside a consumer-installable plugin.

## Revisit triggers
- A consumer wants versioned releases of the script itself -> reconsider the plugin-vs-root home.
- Claude Code ships native marketplace version tooling -> delete this and delegate.
