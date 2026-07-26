---
id: 0004
title: "Version-control the generated advisor panel; close the .claude/agents gitignore trap"
status: accepted
tier: lite
summary: "pdca-init writes advisors to .claude/agents/, but the common .claude/* gitignore silently drops them, breaking the documented panel-tuning workflow. Fix: panel-generation.md tells consumers to version-control the panel via a glob-form .claude/* + !.claude/agents/ negation (a bare .claude/ must be converted first). Keep the discovery dir, no relocation, no new machinery."
---

# 0004 — version-control the advisor panel

- Decision: `panel-generation.md` step 4 instructs consumers to keep advisors in
  `.claude/agents/` (Claude Code's project-agent discovery dir — do not relocate) and, when the
  project ignores `.claude/`, convert a bare `.claude/` rule to the glob form `.claude/*` (a
  bare rule blocks any child negation) then add `!.claude/agents/`. Guidance only — no
  script/CI/linter, since advisors live in the consumer's repo where the plugin can't enforce
  VCS.
- Why: the common `.claude/*` gitignore silently drops generated advisors, so an ADR's `Panel:`
  line references a roster no reviewer can see and the documented generate-edit-tune workflow
  breaks. Prevent beats a caveat that gets ignored.
- Rejected: relocate advisors out of `.claude/agents/` — breaks Claude Code's discovery. A
  global VCS mandate — unenforceable from a plugin. Caveat-only — detect-not-prevent, the trap
  stays silent.
- Reopen-if: Claude Code changes where it discovers project agents -> revisit the
  keep-in-place choice. A consumer reports advisors still untracked after `/pdca-init` ->
  scaffold the negation automatically instead of instructing it.
- Enforced: `pdca-workflow/skills/pdca-init/references/panel-generation.md` step 4; this repo's
  own panel is tracked per ADR 0028.
