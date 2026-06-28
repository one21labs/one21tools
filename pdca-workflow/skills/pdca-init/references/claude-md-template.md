# <Project> — CLAUDE.md template

Copy this to your project root as CLAUDE.md and fill the <bracketed> parts. Keep it to the
always-loaded minimum (~60 lines — a proxy for its token cost); over-length signals content
belongs in a lower home, so push detail there (a source header, the roadmap, an agent file) and
leave a pointer. Delete this heading block once filled.

---

## Stack & navigation
<Language / framework / build. Where state lives. How to run it.>
<Test + build + render commands, e.g. `npm test`, `npm run build` — run all before every push.>
File headers own each file's role + constraints. Start at <the core module> (the product).

## Sacred (do not break)
- <the core module> = the product. Never modify without updating its paired test.
- <persistence/storage invariant — key prefix, on-disk format>. Add a migration fn; never change the format.
- Schema version in every saved record. Increment on shape change.

## Conventions
- Watch for and cut **muda** as you go — duplicated logic / one-home violations, dead code or
  fields, premature abstraction, drift, git-tellable backstory (git is the SSoT — see Docs).
  Cite-or-silence; don't gold-plate.
- Poka-yoke: prefer a design that makes an error impossible over one that only detects it — delete
  the mirror, don't guard it; derive, don't duplicate; compute the verdict, don't assert it. A
  guard/test is the fallback when prevention can't be designed in.
- One component/module per concern; inline until reused in 2+ places.
- Reuse existing helpers; don't duplicate. Editors patch only their own fields.

## Docs — one home per fact
Every fact has ONE home at the lowest altitude that owns it; higher docs reference, never restate.
Git history is the SSoT for backstory — docs state the current truth, never narrate how it got there
(retired/renumbered IDs, what-folded-into-what, "Learned" logs = drift; cut on sight).
Altitude: STRATEGY > ROADMAP > README > CLAUDE.md > source headers > code. Code is bottom-altitude
but TOP authority for executable facts (schema versions, signatures, filenames, dims) — a doc that
restates them rots.
A copy above its home is drift. Touch a source file -> update its header in the same change.

## Never
- <project inviolables, e.g. no console.log in committed code; no async wrapper around a sync API>
- ship without the core test green
- ship a process-gating script (a CI action, a metrics threshold, a render/lint gate) without an
  executable test of its decision logic
- git push to <deploy branch> without intent — it auto-deploys to production

## Shipping — version, release, PR
- Version tracks the shipped APP. Background/meta work (tooling, process docs) does NOT bump it.
- App change: bump the version (patch = fix/UX, minor = a roadmap feature) — never hand-edit.
- PR: title = the change in one line; body = Purpose / Changes / Testing / Deferred.
- Run `/retrospect` on the branch before opening the PR (process improvements land in it).

## Feedback = PDCA trigger
User feedback (bug report, feature ask, behavioral observation) triggers `/roadmap-review`
immediately — Plan (advise -> PM decides -> ADR + roadmap entry), Do, Check (tests + render +
fresh-eyes gate), Act (ship + iterate the system). **Never fix directly** before planning — a
judgment call (threshold, scope, policy) triggers the panel even when it's meta/tooling.

## Review panels (agent grading)
- Fresh eyes: each reviewer a NEW agent, only the artifact + a neutral task; never pass a prior
  grade or the grade you want (priming anchors and inflates).
- Independent instances in parallel; the grade is a signal, never the objective.
- Verify before acting: reproduce every finding against the code yourself — agents are
  confidently wrong. Never relay or act on an unverified claim, either direction.
- Inherit settled calls from `docs/decisions/`; don't re-litigate. Full process: `/roadmap-review`.
