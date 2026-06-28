# ADR ledger linter — spec

The ADR system is an append-only, manually-numbered ledger. Manual numbering across parallel
branches invites two silent drifts — duplicate IDs and INDEX↔file divergence — and the line
budget rots without enforcement. `adr-lint` is the **poka-yoke**: it fails the build on those, so
they surface at merge instead of being discovered later. Per "no process-gating script without a
test of its decision logic," it ships with a decision-logic test (`scripts/adr-lint.test.mjs`).

This file is the **spec** — the four checks, the required INDEX format, and the install path. A
runnable node reference ships at `scripts/adr-lint.mjs` (zero-dependency, cross-platform); a
consumer on another stack reimplements the four checks against this spec.

## The four checks (over `docs/decisions/`)
1. **No duplicate IDs** — no two `NNNN-*.md` files share the same `NNNN`. (Parallel branches grab
   the same int; this catches it at merge.)
2. **Every file is indexed** — every `NNNN-*.md` on disk is linked in `INDEX.md`.
3. **Every index link resolves** — every `INDEX.md` link points to a file that exists, and the
   link's ID label matches the filename (`[0007](0007-slug.md)`, not `[0007](0009-slug.md)`).
4. **Budget** — no ADR exceeds the line budget (default 70 — the absolute max from
   `adr-template.md`; configurable). Over budget = bloat or a missed lower home.

A failure prints the offending IDs/files and exits non-zero. A clean ledger exits zero.

## Required INDEX.md row format (load-bearing)
Check 2/3 regex the index for markdown links of the exact form:

```
| [NNNN](NNNN-slug.md) | <decision, one line> | <ships> |
```

`adr-template.md` pins this same format ("INDEX.md — catalog + shared register"). If you change
the row syntax, change both — the linter and the scaffolded ledger must agree, or the linter fails
on its own init output.

## Run / install
```
node scripts/adr-lint.mjs                  # lints ./docs/decisions, budget 70
node scripts/adr-lint.mjs docs/decisions --budget=50
node --test "scripts/*.test.mjs"           # the decision-logic test
```

`/pdca-init` copies `adr-lint.mjs` + `adr-lint.test.mjs` into the consuming repo's `scripts/` and
points the project at running it pre-merge / in CI (alongside the project's own tests). Wire it
wherever the project gates merges; "monotonic by luck" is not a guard.
