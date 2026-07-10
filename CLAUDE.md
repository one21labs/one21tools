# one21tools

Goal (home: README.md): quality output, autonomously. Prioritize all work against it.

## Stack & navigation
No app, build, or deploy — the "code" is markdown + JSON + scripts: skills live in `skills/<name>/SKILL.md` (+ `references/`,
`scripts/`); plugins are top-level dirs (e.g. `pdca-workflow/`) with a `.claude-plugin/plugin.json`,
registered in `.claude-plugin/marketplace.json`; the deterministic parts are real scripts
(`adr-lint.mjs`, `validate.py`). Validate a skill: `python skills/building-skills/scripts/validate.py <dir>`.
Lint the decision log: `node pdca-workflow/scripts/adr-lint.mjs docs/decisions`.
Check benchmark workflows: `node scripts/check-workflow.mjs` (syntax + `model:` on every agent() call).
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
- `docs/decisions/` is version-agnostic, frontmatter-cataloged (no index); run `adr-lint` pre-merge,
  and RE-RUN it after any edit made after the last pass — a post-lint touch-up is how budget breaks ship.

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
- **Sync before spend** (ADR 0043): before executing an issue, `git fetch origin main` + re-read
  the issue and search PRs referencing it; repeat before the final push — parallel sessions close
  issues concurrently (issue #30 ran twice). When issue-write permission is available, post a
  one-line "in progress (session X)" claim comment at start and clear it on completion.
- **Read the PR's review comments before merging** — the advisory muda-review CI posts inline
  findings; address each or say why not. Merging unread leaves muda on `main`.
- **Squash-merge is the owner's per-PR call** (not automatic). After a squash-merge the branch still
  shows commits "ahead" of `main`, so judge merged-ness by PR state + file diff, not
  `git log main..branch` ahead-count. After any upstream PR merges, `git fetch` + rebase your live
  branch onto `origin/main` before ranging, branching, or `/retrospect` — a stale local `main` re-adds the
  squashed commits as a phantom range. Preview what a branch/PR changes with three-dot
  (`origin/main...branch`), never two-dot — two-dot is tip-to-tip and shows a branch merely behind
  `main` as reverting main's content.
- PR body: Purpose / Changes / Testing / Deferred / Retrospective. Run `/retrospect` on the branch
  before opening it, then record the outcome as a body line: `Retrospective: run | unavailable |
  skipped-<reason>` (ADR 0030) — `skipped-batch:<link>` is a sanctioned reason when debt is paid by
  a batch retrospect covering prior small PRs; `unavailable` when the plugin didn't load in-session
  (ADR 0022). No size floor: "tiny PR" is not a valid reason on its own.
- **Disclose Claude authorship** on every issue and PR Claude writes (this repo AND external repos,
  e.g. anthropics/skills): end the body with "*Disclosure: written by Claude (Claude Code) under
  the direction of the repo owner.*" The Claude-Session commit trailer alone is not disclosure.
- **No external publication without approval**: never file or edit issues/PRs/comments in a repo
  outside one21labs/* without the owner's per-item approval of the exact text. An internal issue
  saying "file upstream" authorizes DRAFTING, not posting — leave the draft in the internal issue
  and stop.
- **Deferred = issues** (ADR 0021): a deferred item someone must act on gets a GitHub issue; the
  PR's Deferred section links it. No handoff/TODO files — work-state tracks in issues,
  decision-state stays in ADRs.

## Feedback = PDCA trigger
This repo dogfoods its own `pdca-workflow` plugin. A judgment call (a threshold, scope, or policy
question — even meta/tooling) triggers `/decide` immediately — advise -> PM decides -> ADR in
`docs/decisions/` -> verify (fresh-eyes + red-team). Never fix a judgment call directly before
deciding it. Inherit settled ADRs; don't re-litigate.
