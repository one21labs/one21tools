---
id: 0047
title: "Executable-home rule + detection-latency ladder as named policy; wave-1 build scope"
status: accepted
summary: "A decidable requirement is never homed in prose — its core needs an executable home (rung 1-4) where a surface binds it (owner rule); the ladder (1 prevent > 5 prose) ranks WHICH rung, upgrades need cited scar. Homed at engineering-principles in general form; jit-documentation.md:23 keeps its 9a anchor + a pointer (not superseded). Wave-1 build scope: publication guard, check-workflow + check-restatement (WARN) per-edit, a gate-has-test lint. Reject validate.py (no scar); three-dot warn+counted log; name the Workflow seam."
---

# 0047 — Executable-home rule + detection-latency ladder

- Date: 2026-07-10
- Owner: PM
- Panel: lean/economist/session-operator (reframed-accept) + owner + red-team (7 breaks) + verifier (PASS). Sweep+prototypes: scratchpad/sweep-detail.txt.
- Context: poka-yoke is doctrine (ENGINEERING_PRINCIPLES.md:50) but never ranked into rungs; jit-documentation.md:23 is only a binary action-moment/JIT branch (Decision Test row 2); retrospect.md:30-33 reinvents home-routing (#21). Top sweep candidates are decidable requirements prose failed (PR#134 pipe-mask, #75). ADR 0038/0039/0040 decide this ordering ad hoc.

## Decision
- **Rule (owner):** a DECIDABLE requirement is never homed in prose — its CORE needs an executable home (rung 1-4) at authoring time where an AVAILABLE SURFACE binds it (a tool-call moment it fires at). No surface yet (sync-before-spend) => interim prose DEFERRING to 0043's trigger. Judgment shells stay rung-5.
- **Ladder:** 1 prevent (deny) > 2 detect-at-creation (PostToolUse) > 3 commit > 4 CI > 5 prose. Executable home MANDATORY; the rung + any earlier-rung upgrade needs cited scar + economics. A full-coverage mechanism deletes its rung-5 prose mirror (detector: check-restatement.mjs); a CI backstop stays.
- **Preconditions (detail at (e)):** (i) a partial predicate ships with its residue recorded (ADR 0030); (ii) undecidable-intent rules WARN, never deny (cry-wolf); (iii) surface-bound.
- Retrospect (retrospect.md:32-33): a scar-cited recurring miss -> propose a one-rung promotion.

**(e) ONE home — engineering-principles, general form.** The Poka-yoke row (ENGINEERING_PRINCIPLES.md:50) names the ladder + rungs GENERALLY; repo scars stay HERE, never the shipped file (ADR 0038 inversion guard). jit-documentation.md:23 STAYS (Decision Test row 2 = 0039:26 item-9a anchor, cited by 0040:33) + gains a pointer — NOT superseded (that orphans cites + inverts altitude). Others point (ADR 0046).

**(a) Wave-1 — BUILD SCOPE (not yet in-repo; each hook predicate ships as a testable file in the CI glob — Never rule):**
- Publication guard (PreToolUse Bash): scars #75, anthropics/skills#1414. Forces `gh pr/issue create` to `--body-file` with disclosure + Retrospective (ADR 0030). Its external (one21labs/*) deny is only a PARTIAL in-repo backstop (hazard is CROSS-repo); CLAUDE.md:70-73's prose stays STRUCTURALLY load-bearing.
- check-workflow.mjs per-edit (PostToolUse Edit|Write, benchmarks/**/*.workflow.js): scar #53; additive to CI.
- check-restatement.mjs per-edit: WARN-only (12-word heuristic = undecidable intent, precondition ii; after-write, doesn't re-block the fix); deny + ALLOW_PAIRS stay at rung-4 CI; diff-scoped (unscoped scan rejected).
- gate-has-test lint: a `scripts/*.mjs`/hook gate implies its `*.test.mjs` in the CI glob — dogfoods "no gate without a test".

**(b) validate.py per-edit — REJECT.** Already HAS a rung-4 CI home; a rung-2 upgrade needs a scar, none cited (#17/#22); ~0 cost isn't a trigger (gold-plating). Revisit on first violation.

**(c) three-dot-diff hook — WARN + counted.** Repeat scar (21706df, PR#59) earns a rung-2 nudge; two-dot intent is undecidable, deny false-blocks (precondition ii). The warn appends to a counted session log (shared with ADR 0049's spawn-log); deny only after zero false-positives on `origin/main..` there.

**(d) Workflow-tool seam — NAME, do not mechanize.** ADR 0040's deny hook matches Agent|Task only and check-workflow lints benchmarks/** only, so an ad-hoc Workflow-script agent() outside benchmarks/ bypasses both. No scar -> the bar blocks it (home in the revisit trigger).

## Justification
Codifies what 0038/0039/0040 decide ad hoc (S/low/med) — poka-yoke-of-the-poka-yoke; splits MUST-it-be-executable (decidable core) from WHICH-rung (scar + economics); the scar bar self-enforces (refutes (b),(d)); wave-1 predicates ship testable (the gate-has-test lint dogfoods the rule).

## Assumptions
- [checkable, in-session] the scar bar is self-enforcing; verifier confirms no wave-1 accept lacks a cited scar.
- [checkable] pr-create-guard extracts a testable predicate and does NOT false-deny a benign command containing `gh pr create` — pending; signal: the build's test (prototype 9/9).
- [checkable] check-restatement per-edit is net-positive ONLY diff-scoped + WARN, not full-NxN blocking — pending; signal: the build's test + a scoped-scan measurement.
- [checkable] the gate-has-test lint fails a gate missing its test — verifier at build.
- [unverifiable] a PostToolUse warn/exit redirects the agent vs being rationalized past — REOPEN-IF a retro shows a shipped hook was ignored.

## Rejected alternatives
- Superseding jit-documentation.md:23 in place — orphans 0039:26/0040:33 cites + inverts altitude (ADR 0038); it stays + points.
- (The other rejections — deleting CLAUDE.md:70-73, deny/unscoped check-restatement — are in the Decision.)

## Revisit triggers
- A decidable requirement rests at prose despite an available surface, OR a rung upgrade ships without a scar -> the rule isn't applied.
- First model-inheritance miss via an ad-hoc Workflow script -> mechanize the seam (a PreToolUse hook on the Workflow tool, or widen check-workflow).
- three-dot counted log clean on `origin/main..` -> promote (c) to deny; first SKILL.md failing validate.py on main -> promote (b) to rung 2.
