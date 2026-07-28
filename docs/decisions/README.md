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

## Retired ids

A decision one file owns lives in that file, not here (owner altitude test, 28-Jul-2026 —
home: doc-budgets.md). These records were deleted after their content hoisted to the owning
file; ids are never renumbered or reused, so a cite of one resolves HERE:

- 0004 -> pdca-workflow/skills/pdca-init/references/panel-generation.md (step 4, version-control the panel)
- 0012 -> .github/workflows/gates.yml (header: required-CI rationale)
- 0018 -> pdca-workflow/agents/retrospect.md (Method, backstory-sweep clause; reopen: recurrence -> a dedicated pre-PR doc-review step, not a bigger prompt)
- 0029 -> scripts/check-workflow.mjs (header)
- 0032 -> pdca-workflow/skills/decide/references/adr-template.md (tag-routing, named-signal pending rule)
- 0038 -> skills/engineering-principles/references/jit-documentation.md (Decision Test, shipping-boundary row)
- 0044 -> skills/building-skills/scripts/validate.py (R6.2)
- 0054 -> scripts/check-pr-body.mjs (header, title/Partial guard)
- 0060 -> .claude/hooks/budget-edit-guard.sh (header)
- 0064 -> .github/workflows/gates.yml (comment above the test-*.sh loop, hook-test convention)
- 0065 -> skill-bench/skills/bench/references/pre-registration.md (Saturation/floor pre-screen + Design-for-signal; reopen clause ends the pre-screen section)
- 0066 -> skill-bench/skills/bench/references/cost-and-verdict.md (grading-cost estimate line)
- 0070 -> benchmarks/README.md (same-PR reconcile rule; hoisted by PR #216)
- 0072 -> .claude/hooks/three-dot-warn.sh (header, diff-only predicate)
- 0073 -> skill-bench/skills/bench/references/cost-and-verdict.md (ceiling_usd = 2x estimate)
- 0076 -> skill-bench/skills/bench/references/cost-and-verdict.md (derived estimates + warn escalation)
- 0077 -> .gitattributes (comment above the merge=union lines)
- 0078 -> scripts/check-pr-body.mjs (body-side closing-keyword guard)
- 0088 -> pdca-workflow/scripts/adr-lint.mjs (docIndexDrift + stale-discharge comments)
