---
name: pdca-init
description: Use when adopting the PDCA feedback workflow in a project. Scaffolds a themed CLAUDE.md and the ADR decision log, then generates a project-tailored advisor panel. Explicit-invoke only; never auto-fire.
disable-model-invocation: true
---

# /pdca-init — adopt the PDCA workflow in this project

Set up the files the workflow needs that a plugin cannot install for you. Explicit-invoke only.
Idempotent: never overwrite an existing CLAUDE.md, ADR, or panel agent — propose a diff and ask
instead.

Arguments (optional): $ARGUMENTS = notes about the project's domain to steer panel generation.

Run this loop:

1. **Read the project.** Read CLAUDE.md (if any), the README, the package/build manifest, and
   the top-level source headers to infer: what the product does, its domain, its Sacred files /
   core module, its test + build + render commands, and the decision axes that matter.

2. **Scaffold CLAUDE.md.** If none exists, write one from `references/claude-md-template.md`,
   filling the project specifics you inferred (stack, Sacred files, test/build/render commands).
   Keep it to the always-loaded minimum (~60 lines). If the project has product analytics, add a
   `metrics command:` line so `/roadmap-review` can run it before gating/conversion calls (see
   `../roadmap-review/references/metrics-engine.md`). If CLAUDE.md already exists, only ADD the
   missing workflow themes (cut muda, one-home/altitude, the PDCA feedback trigger, `/retrospect`
   before a PR); never rewrite the user's content.

3. **Scaffold the decision log + its guard.** If `docs/decisions/` is absent, create it: copy
   `../roadmap-review/references/adr-template.md` into `docs/decisions/README.md` (its canonical
   home — it carries the ADR rules, the template, AND the shared-assumption register). No index
   file: the ADR files are the catalog, skimmed via their `summary`/`status` frontmatter (poka-yoke
   — a mirror you don't keep can't drift). Copy `../../scripts/adr-lint.mjs` + `adr-lint.test.mjs`
   into the project's `scripts/` and tell the user to run `node scripts/adr-lint.mjs` pre-merge /
   in CI — the corpus poka-yoke (`../roadmap-review/references/adr-lint.md`).

4. **Generate the advisor panel.** This is the point of per-project customization — follow
   `references/panel-generation.md`. Infer the 4-8 advisors THIS project's decisions actually
   need (a correctness lens for each distinct way the product can be wrong, plus the value / cost
   / risk / differentiation axes the correctness experts don't own), write each into
   `.claude/agents/` from `references/advisor-template.md`, and record the roster + why each was
   chosen (a short `docs/decisions/panel.md`) so the user can edit it.

5. **Confirm.** Summarize what you scaffolded and the panel you generated; tell the user to
   review/edit the panel, then run `/roadmap-review` for their first decision. Offer (don't
   auto-apply) the optional advisory CI: copy `../../templates/claude-review.yml` into
   `.github/workflows/` and print its OAuth-token / required-check setup steps.

The meta-roles (`pm`, `tech-lead`, `red-team`, `verifier`, `retrospect`) ship with this plugin
and need no scaffolding — only the domain panel is project-specific.
