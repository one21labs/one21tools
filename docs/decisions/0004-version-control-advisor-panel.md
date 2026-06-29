---
id: 0004
title: "Version-control the generated advisor panel; close the .claude/agents gitignore trap"
status: accepted
summary: "pdca-init writes advisors to .claude/agents/, but the common `.claude/*` gitignore silently drops them, so a Panel:-referenced roster never reaches the repo and the documented panel-tuning workflow breaks. Fix: panel-generation tells consumers to version-control the panel via a glob-form `.claude/*` + `!.claude/agents/` negation (a bare `.claude/` must be converted first; prevent>detect); keep the discovery dir, no relocation, no new machinery. This framework repo stays per-call (no standing roster)."
---

# 0004 — Version-control the advisor panel

- Date: 2026-06-28
- Owner: PM
- Panel: 3 advisors (reproducibility / muda-YAGNI / poka-yoke-location lenses) + `verifier` + `red-team` — dogfooded `/decide`. No standing product panel (framework repo).
- Context: `/pdca-init` writes the project advisor panel to `.claude/agents/` (`pdca-init/SKILL.md:4`,
  `panel-generation.md:25`) and promises "this is what the user edits to tune the panel"
  (`panel-generation.md:28`). But the common Claude Code gitignore `.claude/*` (this repo's
  `.gitignore:9`, only `!settings.json` excepted) silently ignores those files. So the advisors an
  ADR's `Panel:` line references never reach the repo, no reviewer can see/diff them, and the user's
  tuning is lost — the documented generate->edit->tune workflow is broken. Open question: should the
  plugin require version-controlling advisors, and how?

## Decision
Plugin guidance states advisors SHOULD be version-controlled (consistent with its own tracked
meta-roles in `pdca-workflow/agents/`); it does NOT globally mandate consumer VCS (unenforceable —
advisors live in the consumer repo; no executable guard reaches them). Concretely, `panel-generation.md`
step 4 instructs (poka-yoke, prevent>detect): keep advisors in `.claude/agents/` (Claude Code's
project-agent discovery dir — do NOT relocate) and, when the project ignores `.claude/`, ensure the
rule is the glob form `.claude/*` (a bare `.claude/` excludes the dir itself and no negation can
re-include its children — convert it first) then add `!.claude/agents/`, so generated advisors are
tracked-by-default. No new script/CI/linter (consumer-side;
machinery would be muda). This framework repo keeps per-call lenses (no standing roster — inherits
0001/0002); each decision's lenses are recorded in its ADR `Panel:` line.

## Justification
Prevent>detect beats a caveat: the trap silently breaks the documented panel-tuning workflow, so a
one-line negation that tracks advisors by default beats a warning that gets ignored. Relocation
rejected — it sacrifices Claude Code's `.claude/agents/` auto-discovery. A global mandate rejected —
the plugin can't enforce a consumer's `.gitignore`; guidance + poka-yoke is the reachable lever. The
`Panel:` line records WHICH lenses ran, not their definitions; the plugin already version-controls its
own agents, so advisors (the project analog) should be too.

## Assumptions
- [verified] the trap is real — `.gitignore:9` `.claude/*` ignores `.claude/agents/*.md` (only `!settings.json` excepted); `git check-ignore` confirms. The negation only works under the glob `.claude/*`; a bare `.claude/` stays ignored even with `!.claude/agents/**` (reproduced) — hence the convert-first instruction.
- [checkable] Claude Code discovers PROJECT advisors at `.claude/agents/` (so relocation breaks discovery; the negation keeps it) — verify vs Claude Code agent-loading docs.
- [checkable] fix is guidance-only: `panel-generation.md` gains the poka-yoke, no script/CI added, adr-lint corpus stays green — verify `node pdca-workflow/scripts/adr-lint.mjs docs/decisions`.
- [unverifiable] consumers act on the `!.claude/agents/` instruction (the plugin can't enforce their VCS) — REOPEN-IF a consumer reports advisors still untracked despite pdca-init.

## Rejected alternatives
- Globally REQUIRE/mandate version-controlled advisors — unenforceable from a plugin; "should + poka-yoke" is the reachable lever.
- Relocate advisors out of `.claude/agents/` to a tracked dir — breaks Claude Code's project-agent discovery.
- Caveat-only ("track them if you want") — detect-not-prevent; the trap is silent, so it keeps biting.
- Do nothing — the generate->edit->tune workflow stays broken for any `.claude/`-ignoring consumer.
- A standing advisor roster for THIS repo — framework-not-product (0001/0002); per-call lenses + the ADR `Panel:` line suffice.
- A new adr-lint/CI guard for advisor tracking — consumer-side; machinery the plugin can't run = muda.

## Revisit triggers
- Claude Code changes where it discovers project agents -> revisit the keep-in-`.claude/agents/` choice.
- A consumer reports advisors still untracked after `/pdca-init` -> strengthen the step (e.g. scaffold the negation automatically).
