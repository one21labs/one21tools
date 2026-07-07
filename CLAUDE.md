# one21tools

## Stack & navigation
No app, build, or deploy — the "code" is markdown + JSON + scripts: skills live in `skills/<name>/SKILL.md` (+ `references/`,
`scripts/`); plugins are top-level dirs (e.g. `pdca-workflow/`) with a `.claude-plugin/plugin.json`,
registered in `.claude-plugin/marketplace.json`; the deterministic parts are real scripts
(`adr-lint.mjs`, `validate.py`). Validate a skill: `python skills/building-skills/scripts/validate.py <dir>`.
Lint the decision log: `node pdca-workflow/scripts/adr-lint.mjs docs/decisions`.
Bump a version: `node scripts/set-version.mjs <plugin|marketplace> <x.y.z>` — writes the
version's one home (plugin.json when the plugin has one, else the marketplace entry).

## Muda — ruthlessly cut on sight
Cut muda the moment you see it, not later — duplicated logic / one-home violations, dead code or
fields, premature abstraction, drift, git-tellable backstory. The taxonomy + audit method live in
the **`engineering-principles`** skill (`waste-identification` / `ssot-enforcement`) — reference it,
don't restate. Operationalized, not a slogan:
- **Cite-or-silence:** every muda call cites a `file:line`; never manufacture a "consolidation" to
  look useful. **Don't gold-plate** — premature process machinery is itself muda.
- **Poka-yoke (prevent > detect):** delete the mirror, don't guard or resync it; derive, don't duplicate.
- **Forcing functions:** `/retrospect` before every PR; `adr-lint` guards the decision log; the
  advisory muda-review CI (`pdca-workflow/templates/claude-review.yml`) when wired.

## Sacred (do not break)
- The **manifests = the registry**: `.claude-plugin/marketplace.json` + each plugin's
  `plugin.json`. A broken or duplicate entry breaks `/plugin install`. Keep the JSON valid.
- **SKILL.md frontmatter:** `name` FIRST (must match the folder), description-as-trigger;
  `disable-model-invocation` for explicit-invoke skills. Run `validate.py` after any SKILL.md edit.
- `docs/decisions/` is version-agnostic, frontmatter-cataloged (no index); run `adr-lint` pre-merge.

## Docs — one home per fact
Every fact has ONE home at the lowest altitude that owns it; higher docs reference, never restate.
Git history is the SSoT for backstory — state the current truth, never narrate how it got there
("Learned" logs, retired-ID notes = drift; cut on sight). Altitude: README > CLAUDE.md > SKILL.md /
manifests / scripts (the "code" here — they own skill names, manifest fields, the registry, the
deterministic logic; a doc that restates them rots).

## Never
- ship a SKILL.md that fails `validate.py`, or invalid marketplace/plugin JSON
- ship a process-gating script (e.g. `adr-lint`, a CI gate) without a test of its decision logic
- emoji in any skill content

## Shipping — PR
- **One concern per PR**; a cross-cutting cleanup gets its own branch (e.g. skills-SSoT vs the
  plugin). A version bump is scoped to the artifact changed (a plugin's `plugin.json`).
- **Squash-merge is the owner's per-PR call** (not automatic). After a squash-merge the branch still
  shows commits "ahead" of `main`, so judge merged-ness by PR state + file diff, not
  `git log main..branch` ahead-count. After any upstream PR merges, `git fetch` + rebase your live
  branch onto `origin/main` before ranging or `/retrospect` — a stale local `main` re-adds the
  squashed commits as a phantom range.
- PR body: Purpose / Changes / Testing / Deferred. Run `/retrospect` on the branch before opening it.

## Feedback = PDCA trigger
This repo dogfoods its own `pdca-workflow` plugin. A judgment call (a threshold, scope, or policy
question — even meta/tooling) triggers `/decide` immediately — advise -> PM decides -> ADR in
`docs/decisions/` -> verify (fresh-eyes + red-team). Never fix a judgment call directly before
deciding it. Inherit settled ADRs; don't re-litigate.
