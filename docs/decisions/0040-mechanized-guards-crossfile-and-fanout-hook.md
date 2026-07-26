---
id: 0040
title: "Mechanize #93 cross-file checks and the model-tier fan-out hook; reject the mirror cmp gate"
status: accepted
tier: lite
summary: "Mechanize two #93 guards in shipped scripts: cross-file checks in validate.py + amendment-backlink in adr-lint.mjs; a PreToolUse hook DENYING a model-less Agent/Task call on an unmodeled surface (named agents/forks carved out), each with a decision-logic test. Reject a cmp gate on the claude-review.yml mirror per ADR 0015:20."
---

# 0040 — Mechanize #93 cross-file checks and the model-tier fan-out hook; reject the mirror cmp gate

- Decision: `validate.py` gains duplicate-heading/ToC/dangling-pointer cross-file checks;
  `adr-lint.mjs` gains an ADR amendment-backlink check (dogfooded here). A PreToolUse hook
  (`explicit-model-guard.sh`) DENIES an Agent/Task call that omits `model` AND targets an
  unmodeled surface (`subagent_type` absent/`general-purpose`) — a named frontmatter-modeled agent
  or `fork` is carved out. Each check ships a decision-logic test. A cmp gate on the
  claude-review.yml mirror is REJECTED per ADR 0015:20 (never guard a mirror).
- Why: the hook denies (not warns) the unmodeled fan-out that cost ~564k tokens once — a warning
  executes anyway, and `check-workflow.mjs` guards only the Workflow `agent(` surface, not the
  interactive Agent tool where the miss occurred.
- Rejected: warn-only hook; `check-workflow.mjs` + a pointer alone (wrong surface); the cmp gate.
- Reopen-if: the hook can't decide model/subagent_type from tool_input -> fall back to a
  CLAUDE.md line.
- Enforced: `pdca-workflow/hooks/explicit-model-guard.sh` +
  `pdca-workflow/scripts/explicit-model-guard.test.mjs`; `pdca-workflow/scripts/adr-lint.mjs`;
  `skills/building-skills/scripts/validate.py`.

## Act (post-ship — 2026-07-10)
- [outcome] hook denies/carves out correctly (11-case test); 8 live fires in `docs/pdca/gate-hits.txt` — verified.
- [outcome] the backlink guard found one offender, fixed same-PR — verified.
