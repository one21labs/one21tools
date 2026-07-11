# <Project> — CLAUDE.md template

Copy this to your project root as CLAUDE.md and fill the <bracketed> parts. This is a **generic
scaffold for any stack** (app, library, CLI, service, docs/tooling repo) — keep the lines that fit
your project and **DROP the ones that don't** (e.g. the persistence items for a stateless tool, the
deploy line for a library, the render check for a non-UI project). Don't keep a line verbatim just
because it's here. Keep the result to the always-loaded minimum (~60 lines — a proxy for its token
cost); over-length signals content belongs in a lower home, so push detail there (a source header,
the roadmap, an agent file) and leave a pointer. Delete this heading block once filled.

---

## Stack & navigation
<Language / framework / build — inferred from the repo (the build manifest, lockfile, source
layout), not assumed. Where state lives, if any. How to run it.>
<The project's own test + build commands — run all before every push. Add a render/verify command
only if there is a display or output layer.>
File headers own each file's role + constraints. Start at <the core module> (the product).

## Sacred (do not break)
- <the core module(s)> = the product. Never modify without updating its paired test; a
  scope/signature change to it is a judgment call -> `/decide` before the first edit.
- <only if the product persists data: the on-disk / storage format is an invariant — never change
  it, add a migration; a schema version on every saved record, bumped on any shape change.>
- <any other inviolable this project must not break — keep only what applies.>

## Conventions
- Watch for and cut **muda** as you go — duplicated logic / one-home violations, dead code or
  fields, premature abstraction, drift, git-tellable backstory (git is the SSoT — see Docs).
  Cite-or-silence; don't gold-plate.
- Poka-yoke: prefer a design that makes an error impossible over one that only detects it — delete
  the mirror, don't guard it; derive, don't duplicate; compute the verdict, don't assert it. A
  guard/test is the fallback when prevention can't be designed in.
- One module per concern; inline until reused in 2+ places. Reuse existing helpers; don't duplicate.
- <project-specific conventions — naming, error handling, units, layering, etc.>

## Docs — one home per fact
Every fact has ONE home at the lowest altitude that owns it; higher docs reference, never restate.
Git history is the SSoT for backstory — docs state the current truth, never narrate how it got there
(retired/renumbered IDs, what-folded-into-what, "Learned" logs = drift; cut on sight).
Altitude (drop rungs the project lacks, e.g. STRATEGY/ROADMAP): STRATEGY > ROADMAP > README >
CLAUDE.md > source headers > code. Code is bottom-altitude but TOP authority for executable facts
(schema versions, signatures, filenames) — a doc that restates them rots. "Code" is whatever form
the product takes: for a skill/plugin/docs repo it is the `SKILL.md` / manifests / config plus any
scripts/source for the deterministic parts (e.g. a linter), owning their executable facts (skill
names, manifest fields, the registry, the logic) the same way. Touch a source artifact -> update its
header/frontmatter in the same change.

## Never
- <project inviolables — e.g. no debug logging in committed code; no async wrapper around a sync API>
- ship without the core test green
- ship a process-gating script (a CI action, a metrics threshold, a render/lint gate) without an
  executable test of its decision logic
- <if a push deploys or releases: git push to <branch> without intent — it ships to production>

## Shipping — version, release, PR
- Version tracks the shipped artifact, not background/meta work; a bump is its own PR, not
  bundled into a feature PR, via the project's version tool.
- One concern per PR. Sync before spend: `git fetch` + re-read the issue/citing PRs before
  executing and before the final push (guards duplicate spend across sessions); claim-comment if
  issue-write is available, clear it on completion.
- Three-dot (`main...branch`) for previews, never two-dot — post-squash, a stale local `main`
  re-adds merged commits as a phantom range under two-dot.
- PR: title = the change; body = Purpose / Changes / Testing / Deferred. Read review comments
  (human or automated) before merging — address each or say why not. Run `/retrospect` first;
  record: `Retrospective: run | unavailable | skipped-<reason>` (no size floor). End with a
  Claude disclosure line on every issue/PR Claude writes (a commit trailer alone isn't
  disclosure).
- Never file/edit outside this project's own org/namespace without the owner's per-item approval
  of the exact text — "file upstream" authorizes drafting, not posting.
- Deferred work gets an issue, not a handoff/TODO file — work-state in issues, decisions in ADRs.

## Feedback = PDCA trigger
User feedback (bug report, feature ask, behavioral observation) triggers `/decide`
immediately — Plan (advise -> PM decides -> ADR; + a tracker entry if the project keeps one), Do,
Check (tests + a fresh-eyes gate; + a produced-output check if there is an output layer), Act
(ship + iterate the system).
**Never fix directly** before planning — a judgment call (threshold, scope, policy) triggers the
panel even when it's meta/tooling.

## Review panels (agent grading)
- Fresh eyes: each reviewer a NEW agent, only the artifact + a neutral task; never pass a prior
  grade or the grade you want (priming anchors and inflates).
- Independent instances in parallel; the grade is a signal, never the objective.
- Verify before acting: reproduce every finding against the code yourself — agents are
  confidently wrong. Never relay or act on an unverified claim, either direction.
- Inherit settled calls from `docs/decisions/`; don't re-litigate. Full process: `/decide`.
