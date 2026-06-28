# Decision log — one21tools

Architecture Decision Records (ADRs) for this repo's meta/tooling judgment calls (plugin scope,
marketplace shape, process). One file per decision: `NNNN-slug.md`. `INDEX.md` is the catalog +
the shared-assumption register.

**Rules + the ADR template live in the plugin** — this repo is the `pdca-workflow` plugin's own
first consumer, so the canonical rules (numbering, one-ADR-per-PR, ship-state, the template) are
the shipped template, not a copy:
[pdca-workflow/skills/roadmap-review/references/adr-template.md](../../pdca-workflow/skills/roadmap-review/references/adr-template.md).

Guard: `node pdca-workflow/scripts/adr-lint.mjs docs/decisions` (run pre-merge).
