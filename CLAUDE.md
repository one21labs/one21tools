# one21tools

Goal (home: README.md): quality output, autonomously, judged as the person receiving it.
Prioritize all work against it.

## Stack & navigation
No app, build, or deploy — the "code" is markdown + JSON + scripts: skills live in `skills/<name>/SKILL.md` (+ `references/`,
`scripts/`); plugins are top-level dirs (e.g. `pdca-workflow/`) with a `.claude-plugin/plugin.json`,
registered in `.claude-plugin/marketplace.json`; the deterministic parts are real scripts.
Validate a skill: `python skills/building-skills/scripts/validate.py <dir>`.
Lint the decision log + every char budget (CLAUDE.md, agent prompts, manifest drift):
`node pdca-workflow/scripts/adr-lint.mjs docs/decisions`. Before editing
any budgeted doc: measure headroom + the addition first, cut muda elsewhere to fit (doc-budgets.md).
Bump a version: `node scripts/set-version.mjs <plugin|marketplace> <x.y.z>`.

## Muda — ruthlessly cut on sight
Duplicated logic / one-home violations, dead code or
fields, premature abstraction, drift, git-tellable backstory. The taxonomy + audit method live in
the **`engineering-principles`** skill (`waste-identification` / `ssot-enforcement`) — reference it,
don't restate. Operationalized, not a slogan:
- **Cite-or-silence:** every muda call cites a `file:line`; never manufacture a "consolidation" to
  look useful. **Don't gold-plate** — premature process machinery is itself muda.
- **Poka-yoke (prevent > detect):** delete the mirror, don't guard or resync it; derive, don't duplicate.
- **Forcing functions:** `adr-lint` guards the decision log; the advisory muda-review CI posts
  inline findings, never blocks. `/retrospect` is on-demand — run it when something felt wrong,
  never as ritual.

## Sacred (do not break)
- The **manifests = the registry**: `.claude-plugin/marketplace.json` + each plugin's
  `plugin.json`. A broken or duplicate entry breaks `/plugin install`. Keep the JSON valid.
- **SKILL.md frontmatter:** `name` FIRST (must match the folder), description-as-trigger;
  `disable-model-invocation` for explicit-invoke skills. Run `validate.py` after any SKILL.md edit.
- `docs/decisions/` is version-agnostic, frontmatter-cataloged (no index); run `adr-lint` pre-merge.

## Docs — one home per fact
Every fact has ONE home at the lowest altitude that owns it; higher docs reference, never restate
(backstory rules: `ssot-enforcement.md`). Altitude: README > CLAUDE.md > SKILL.md /
manifests / scripts (the "code" here — they own skill names, manifest fields, the registry, the
deterministic logic; a doc that restates them rots).

## Never
- ship a SKILL.md that fails `validate.py`, or invalid marketplace/plugin JSON
- ship a process-gating script (e.g. `adr-lint`, a CI gate) without a test of its decision logic
- emoji in any skill content

## Shipping — PR
- **Size PRs for reviewability, not one-concern (ADR 0056)**: ship cohesive work together across
  files; split only for a clean revert boundary or to keep main green. Version bumps get their own PR (`set-version.mjs`, ADR 0048).
- **Sync before spend** (ADR 0043): before executing an issue, `git fetch origin main` + re-read
  the issue and search PRs citing it; repeat before the final push. When issue-write is
  available, post an "in progress" claim comment at start; clear it on completion. Retitle a
  tracking issue whose title no longer matches its remaining scope before working under it.
- **gh quirks:** `gh issue view` needs `--json` here (Projects-classic deprecation); `gh pr edit`
  fails the same way — PATCH the body via `gh api`.
- **Read the PR's review comments before merging** — the advisory muda-review CI posts inline
  findings; address each or say why not. Merging unread leaves muda on `main`.
- **Squash-merge is the owner's per-PR call** (not automatic). After a squash-merge the branch still
  shows commits "ahead" of `main`, so judge merged-ness by PR state + file diff, not
  `git log main..branch` ahead-count. After any upstream PR merges, `git fetch` + rebase your live
  branch onto `origin/main` before ranging, branching, or `/retrospect` — a stale local `main` re-adds the
  squashed commits as a phantom range. Preview a branch/PR with three-dot
  (`origin/main...branch`), never two-dot (tip-to-tip: a behind-branch reads as reverting main).
- PR body: Purpose / Changes / Testing / Deferred (ADR 0030).
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
This repo dogfoods its own `pdca-workflow` plugin. A judgment call gets DECIDED and recorded
(ADR in `docs/decisions/`) before it's built — directly for routine calls, with a panel only
when genuinely contested, with one fresh adversary (verify/red-team) when the result ships or
is hard to reverse (ADR 0062). Inherit settled ADRs; don't re-litigate — but an ADR resting on
an unsourced want is challengeable, not settled.

## Judgment
A want you can't QUOTE is your own — ask, don't infer. Before deciding what someone
experiences, go experience it as they would. A perfectly-formed record can still be
senseless — form is no substitute for a person in the frame.
