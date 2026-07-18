---
id: 0040
title: "Mechanize #93 cross-file checks and the model-tier fan-out hook; reject the mirror cmp gate"
status: accepted
summary: "Mechanize two corpus-scoped guards in shipped scripts (#93 item 2: cross-file checks in validate.py + amendment-backlink in adr-lint.mjs; item 6: a PreToolUse hook that DENIES a model-less Agent/Task call on an unmodeled surface — subagent_type absent/general-purpose; named agents and forks carved out), each with a decision-logic test. Reject item 7 (a cmp gate on the claude-review.yml mirror) per ADR 0015:20."
---

# 0040 — Mechanize #93 cross-file checks and the model-tier fan-out hook; reject the mirror cmp gate

- Date: 2026-07-10
- Owner: PM
- Panel: lean-process-engineer, process-economist, session-operator, plugin-adopter.
- Context: The #93 RCA: cross-file duplication/drift and the implicit-model fan-out miss are invisible to every diff-scoped check (#93 items 2, 6). Two guards should mechanize in SHIPPED gate scripts (ADR 0038); one proposed guard (item 7, a cmp step on the claude-review.yml mirror) is rejected.

## Decision
1. **Item 2 — mechanize cross-file checks in shipped scripts.** validate.py gains: duplicate top-level headings, ToC↔heading match, dangling internal skill/reference pointers (it already walks references/*.md at validate.py:251-254). adr-lint.mjs gains an ADR amendment backlink ("Amend ADR NNNN" ⇒ NNNN cites the amender). Each ships with a decision-logic unit test (Never rule).
2. **Item 6 — enforce explicit model tier at the interactive fan-out surface via a shipped PreToolUse hook.** A hook in `pdca-workflow/hooks/` DENIES (not merely warns) an Agent/Task call that omits `model` AND targets an unmodeled surface — `subagent_type` absent or `general-purpose`, the case that silently inherits the PARENT SESSION model (the ~564k miss). Carve out a named frontmatter-modeled agent and `fork` (both inherit the correct tier by design); the override IS the standard (set `model:` explicitly). Matching strategy + limits live in the hook's own header (one home). check-workflow.mjs:28-47 guards only the Workflow `agent(` surface, NOT the interactive Agent tool where the miss occurred — this hook covers a genuinely uncovered surface.
3. **Item 7 — REJECT the cmp gate on the claude-review.yml mirror.** Keep the re-copy discipline note.

## Justification
Item 6 has the best ratio in the batch — a deterministic shell hook (~0 per-call cost) against a measured ~564k-token recurrence (≈5% of weekly quota; #93 item 6). It DENIES the unmodeled fan-out rather than warning, so it actually prevents the launch the ~564k justifies against (a warning executes anyway); scoping the deny to `subagent_type` absent/general-purpose keeps false-positives near zero — a defined frontmatter-modeled agent omitting `model` inherits its own tier correctly and is not touched. Item 2 is ~0 marginal (validate.py + adr-lint run every PR already) and mechanizes the exact corpus-scoped class the RCA names. Item 7 rejected: adding a string-equality gate to a mirror is the anti-pattern ADR 0015:20 forbids ("that is 'guard the mirror,' which the doctrine forbids") — the poka-yoke is not-guarding the mirror; the re-copy note suffices.

## Assumptions
- [verified] hooks.json carries only PostToolUse/Bash → retrospect-reminder.sh; PreToolUse absent → additive — read 2026-07-10.
- [verified] validate.py walks the skill's own references/*.md (:251-254) and binds folder_name = skill_path.name (:150) — cross-file checks slot into the existing R6 walk.
- [verified] ADR 0015:20 forbids a string-equality gate to guard a mirror — read 2026-07-10.
- [verified] the Agent tool schema exposes an optional per-call `model` plus `subagent_type`; omitting `model` inherits the agent definition's frontmatter model when one exists, else the parent session model — so the deny MUST scope to unmodeled surfaces (subagent_type absent/general-purpose) to avoid false-positives on frontmatter-modeled agents (orchestrator fact-check 2026-07-10).
- [checkable] a PreToolUse hook DENIES a model-absent general-purpose Agent call and does NOT fire on a defined frontmatter-agent call omitting `model`; the injection test is the build's acceptance gate — owner: verifier; result: pending the build (named signal: the hook's own test), feasibility established above (ADR 0032 pattern).
- [checkable] each new check/hook ships a decision-logic unit test (Never rule) — owner: verifier at implementation.

## Rejected alternatives
- Warn-only hook — the fan-out executes anyway, so it doesn't prevent the ~564k spend it's justified against; deny (with the frontmatter/fork carve-out) is the poka-yoke.
- Drop item 6, rely on check-workflow.mjs + the CLAUDE.md pointer (O9) — check-workflow guards only the Workflow `agent(` surface, not the interactive Agent tool where the miss occurred; the prose pointer fails at the action moment (item 9a).
- Item 6 as a CLAUDE.md prose line only — fixes this repo, doesn't ship; violates ADR 0038 (kept as a supplement, not the home).
- Item 7 cmp gate — ADR 0015:20 conflict.
- A new repo-only check-benchmark-style gate for the cross-file class — validate.py/adr-lint are the shipped homes.

## Revisit triggers
- The hook can't decide model/subagent_type from tool_input on the real Agent surface (injection fails) → fall back to the CLAUDE.md line + a Workflow-only check-workflow.mjs extension.
- The deny false-positives on a legitimate parent-model general-purpose fan-out → downgrade to warn or widen the carve-out.
- A cross-file waste class recurs that validate.py's new checks miss → extend the checks.

## Act (post-ship — 2026-07-10)
- [outcome] hook denies/carves out correctly in its 11-case surface-invoked test (PR #133); the LIVE injection [checkable] is still-open — signal: first plugin-loaded session.
- [outcome] the backlink guard found one offender (0023↔0026), fixed same-PR — verified.
- [process] CLAUDE.md pointer dropped at build (budget); the hook is the decided mechanism.
