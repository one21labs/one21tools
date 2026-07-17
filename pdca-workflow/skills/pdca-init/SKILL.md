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

1. **Read the project.** Scan the repo to infer the stack — don't assume one. Read CLAUDE.md (if
   any), the README, the build manifest + lockfile (`package.json`, `pyproject.toml`, `Cargo.toml`,
   `go.mod`, `Gemfile`, a `Makefile`, etc.), and the top-level source headers to infer: what the
   product does, its domain, its language/build, its Sacred files / core module, its test + build
   commands (and a render/verify command only if there is a display or output layer), and the
   decision axes that matter.

2. **Scaffold CLAUDE.md.** If none exists, write one from `references/claude-md-template.md`,
   filling the project specifics you inferred (stack, Sacred files, test/build commands) and
   DROPPING template lines that don't apply to this stack — the template is a generic scaffold, not
   a checklist to keep verbatim (e.g. the persistence/schema Sacred items for a stateless tool, the
   deploy Never for a library, the render check for a non-UI project). Keep it to the always-loaded
   minimum (~60 lines). If the project has product analytics, add a
   `metrics command:` line so `/decide` can run it before gating/conversion calls (see
   `../decide/references/metrics-engine.md`). If CLAUDE.md already exists, only ADD the
   missing workflow themes (cut muda, one-home/altitude, the PDCA feedback trigger, `/retrospect`
   before a PR); never rewrite the user's content.

3. **Scaffold the adoption marker + the decision log + its guard.** If `docs/pdca/` is absent,
   create it with an empty `session-log.txt` (committed): the dir is BOTH the panel spawn-log's
   home and the marker the plugin's enforcement hooks require before firing in a project — no
   `docs/pdca/`, no hooks (the hooks never create it themselves). If `docs/decisions/` is absent, create it: copy
   `../decide/references/adr-template.md` into `docs/decisions/README.md` (its canonical
   home — it carries the ADR rules, the template, AND the shared-assumption register). The copy is
   deliberately vendored, frozen at adoption: a plugin update must not silently rewrite a project's
   decision rules, and the plugin cache is per-user (a link would dangle for teammates/CI). Only a
   repo hosting the plugin source itself links instead of copying. No index
   file: the ADR files are the catalog, skimmed via their `summary`/`status` frontmatter (poka-yoke
   — a mirror you don't keep can't drift). Copy `${CLAUDE_PLUGIN_ROOT}/scripts/adr-lint.mjs`,
   `adr-lint.test.mjs`, `char-budget.mjs`, and `char-budget.test.mjs` (the linter's import — without
   it `adr-lint.mjs` throws `ERR_MODULE_NOT_FOUND`) into the project's `scripts/` and tell the user
   to run `node scripts/adr-lint.mjs` pre-merge / in CI — the corpus poka-yoke
   (`../decide/references/adr-lint.md`).

4. **Generate the advisor panel.** This is the point of per-project customization — follow
   `references/panel-generation.md`; its Method owns the inference, roster size, target dir,
   version-control guard, and `panel.md` record — don't restate them here.

5. **Confirm.** Summarize what you scaffolded and the panel you generated; tell the user to
   review/edit the panel, then run `/decide` for their first decision. Offer (don't
   auto-apply) the optional advisory CI: copy `${CLAUDE_PLUGIN_ROOT}/templates/claude-review.yml` into
   `.github/workflows/` and print its OAuth-token / required-check setup steps.

The meta-roles (`pm`, `tech-lead`, `red-team`, `verifier`, `retrospect`) ship with this plugin
and need no scaffolding — only the domain panel is project-specific.
