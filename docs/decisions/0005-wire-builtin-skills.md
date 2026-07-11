---
id: 0005
title: "Wire Claude Code built-in skills into the plugin's execution seams"
status: accepted
summary: "Name the always-applicable built-ins as defaults at their seams (/simplify at the muda-apply step, matching the existing /code-review at the gate); mention the run-coupled built-ins (/verify, /run, /run-skill-generator) only as scoped 'if the project has a runnable surface (app/service/CLI/library)' examples beside the existing conditional seam, not unconditional defaults — preserving ADR 0002's tool-agnostic portability and the no-output degrade."
---

# 0005 — Wire built-in skills into the execution seams

- Date: 2026-06-28
- Owner: PM
- Panel: 3 advisors (reuse / portability-muda / placement lenses) + `verifier` + `red-team` — dogfooded `/decide` BY HAND (the plugin's `/decide` command is not installed this session).
- Context: the plugin leaves generic execution seams — "run the project's render/verify step (per
  CLAUDE.md)" (`verifier.md:26`, `decide/SKILL.md:71`) and the muda-apply step (`retrospect/SKILL.md`
  step 6) — and already names ONE built-in, `/code-review`, at the gate (`verifier.md:18`). Claude
  Code's other built-ins (`/verify`, `/run`, `/simplify`, `/run-skill-generator`) are concrete
  implementations of those seams, available to every Claude Code user (the plugin is itself a CC
  plugin, so naming them adds no dependency). Open question: name them as defaults, or keep the
  generic phrasing (ADR 0002 deliberately stripped hardcoded stack/tool assumptions)?

## Decision
Split by applicability:
- Always-applicable, app-agnostic built-ins -> named as the default at their one home, matching the
  `/code-review` precedent: `/simplify` at `retrospect/SKILL.md` step 6 (the muda-apply step).
- Run-coupled built-ins (`/verify`, `/run`, `/run-skill-generator`) -> mentioned ONLY as scoped "if
  the project has a **runnable surface** (app, service, CLI, or testable library)" examples beside the
  EXISTING conditional at `verifier.md:26` ("a product with no output layer skips this"); never
  unconditional. The predicate is "runnable surface," NOT "has a GUI" — a CLI/library (this repo's own
  scripts: `adr-lint`, `validate.py`, `node --test`) is runnable and in-scope; only a truly
  output-less artifact skips. `/run-skill-generator` scaffolds the run-harness `/verify` and `/run` then drive.
One home each (no duplication across decide/verifier/retrospect/claude-md-template); `/code-review` stays at `verifier.md:18`.

## Justification
The `/code-review` precedent shows naming an always-applicable built-in is right; `/simplify` is the
same class (app-agnostic quality cleanup), so consistency extends to it. The app-coupled built-ins
degrade to nothing for an app-less project (this repo), so promoting them to unconditional defaults
would re-introduce the coupling ADR 0002 removed and mislead the most representative consumer; gating
them behind the existing conditional keeps portability. Guidance wiring only — no machinery.

## Assumptions
- [verified] `/code-review` is already named at `verifier.md:18` (the precedent); the render/verify conditional exists at `verifier.md:26`.
- [checkable] `/verify`, `/run`, `/simplify`, `/code-review`, `/run-skill-generator` are Claude Code built-in bundled skills (present in this session) — the named defaults resolve.
- [checkable] the edits keep the "no output layer skips this" conditional and add no machinery; adr-lint stays green — verify `node pdca-workflow/scripts/adr-lint.mjs docs/decisions`.
- [unverifiable] built-in skill names stay stable across Claude Code versions — REOPEN-IF one is renamed/removed (the "e.g." phrasing degrades, does not break).

## Rejected alternatives
- Hard-wire all five as unconditional defaults — re-introduces ADR 0002's stripped coupling; `/verify`/`/run`/`/run-skill-generator` mislead app-less projects.
- Do nothing (generic seams only) — leaves the re-derivation muda and the inconsistency with the already-named `/code-review`.
- Put the pointers in `claude-md-template.md` — duplicates the agent-level pointer across template + verifier + retrospect (muda); the template stays stack-generic.

## Revisit triggers
- A Claude Code built-in named here is renamed/removed -> update the "e.g." aside.
- A consumer finds the generic seam too implicit to discover the built-ins -> reconsider naming them more prominently.

## Act (post-ship — 2026-06-28, PR #8)
