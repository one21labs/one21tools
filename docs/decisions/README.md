# Decision log — one21tools

Authoritative Decision Records (ADRs) for this repo's meta/tooling judgment calls (plugin scope,
marketplace shape, process). One file per decision: `NNNN-slug.md`, each starting with
`id`/`title`/`status`/`summary` frontmatter. **No index file** — the ADR files are the catalog,
skimmed via their frontmatter (poka-yoke: a mirror you don't keep can't drift).

**Rules + the ADR template live in the plugin** — this repo is the `pdca-workflow` plugin's own
first consumer, so the canonical rules (numbering, one-ADR-per-PR, rationalize-in-place,
version-agnostic, the template) are the shipped template, not a copy:
[pdca-workflow/skills/decide/references/adr-template.md](../../pdca-workflow/skills/decide/references/adr-template.md).

Guard: `node pdca-workflow/scripts/adr-lint.mjs docs/decisions` (run pre-merge).

## Shared assumption register

A shared `[unverifiable]` fact several ADRs depend on lives here once; each references it, so one
signal reopens them all.

| Assumption | Affects | Resolve with |
|------------|---------|--------------|
| A second consumer (a non-LTconfig project adopting the plugin) needs no runnable metrics engine — the language-neutral `metrics-engine.md` spec suffices | 0001 | a real second consumer's request, or its absence after the plugin is used elsewhere |
