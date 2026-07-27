# Decision log — one21tools

Authoritative Decision Records (ADRs) for this repo's meta/tooling judgment calls (plugin scope,
marketplace shape, process). One file per decision: `NNNN-slug.md`, each starting with
`id`/`title`/`status`/`summary` frontmatter.

**The rules, the template, the no-index-file rationale, and the size budgets live in the plugin.**
This repo hosts the plugin source, so it links the shipped template rather than vendoring a copy —
read the rules there, never here:
[pdca-workflow/skills/decide/references/adr-template.md](../../pdca-workflow/skills/decide/references/adr-template.md).

Guard: adr-lint — command in [CLAUDE.md](../../CLAUDE.md), spec in
[adr-lint.md](../../pdca-workflow/skills/decide/references/adr-lint.md).
