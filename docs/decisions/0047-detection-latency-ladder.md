---
id: 0047
title: "Executable-home rule + detection-latency ladder as named policy; wave-1 build scope"
status: accepted
summary: "A decidable requirement's core needs an executable home (rung 1-4) where a surface binds it; the ladder (1 prevent > 5 prose) ranks WHICH rung, and an upgrade needs a cited scar. Homed in general form at engineering-principles. Wave-1: publication guard, check-workflow, check-restatement (WARN), gate-has-test lint."
---

# 0047 — Executable-home rule + detection-latency ladder

- Date: 2026-07-10
- Owner: PM
- Context: poka-yoke was doctrine but never ranked into rungs; decidable requirements kept
  shipping as prose (PR#134 pipe-mask scar, #75) while ADR 0038/0039/0040 ordered rungs ad hoc.

## Decision
- **Rule:** a DECIDABLE requirement is never homed in prose — its CORE needs an executable home
  (rung 1-4) at authoring time where an AVAILABLE SURFACE binds it. No surface yet => interim
  prose deferring to ADR 0043's trigger. Judgment shells stay rung-5.
- **Ladder:** 1 prevent (deny) > 2 detect-at-creation (PostToolUse) > 3 commit > 4 CI > 5 prose.
  The rung, or any upgrade, needs a cited scar + economics. A full-coverage mechanism deletes its
  rung-5 prose mirror (check-restatement.mjs); a CI backstop stays.
- **Preconditions:** (i) a partial predicate ships with its residue recorded (ADR 0030); (ii)
  undecidable-intent rules WARN, never deny; (iii) surface-bound.
- **One home** — engineering-principles carries the ladder in GENERAL form; repo scars stay here
  (ADR 0038 inversion guard). `jit-documentation.md:23` keeps its 9a anchor (cited by ADR
  0039/0040) + a pointer — not superseded.
- **Wave-1 scope** (each a testable file in the CI glob): a publication guard (PreToolUse Bash
  forcing `gh pr/issue create` to `--body-file` with disclosure; scars #75,
  anthropics/skills#1414); `check-workflow.mjs` per-edit (scar #53); `check-restatement.mjs`
  per-edit (WARN-only, diff-scoped); a gate-has-test lint. The PR#134 pipe-mask scar got NO
  wave-1 remedy; wave-1 grants no pipe-guard authority (ADR 0091).
- **Rejected wave-1 items:** validate.py per-edit (already rung-4 CI, no scar); a three-dot-diff
  hook as deny (WARN + counted — two-dot intent is undecidable); mechanizing the Workflow-tool
  seam (named, not built — no scar).

## Justification
Splitting MUST-it-be-executable (decidable core) from WHICH-rung (scar + economics) lets the scar
bar self-enforce, as the validate.py and Workflow-seam rejections show.

## Assumptions
- [checkable] every wave-1 accept carries a cited scar, pr-create-guard doesn't false-deny a
  benign `gh pr create`, and the gate-has-test lint fails a gate missing its test — verified at
  build (9/9).
- [unverifiable] WEAKEST — a PostToolUse warn/exit actually redirects the agent instead of being rationalized past. REOPEN-IF a retro shows a shipped hook was ignored.

## Rejected alternatives
- Superseding `jit-documentation.md:23` — orphans cites and inverts altitude (ADR 0038).

## Revisit triggers
- A decidable requirement rests at prose despite an available surface, or a rung upgrade ships
  without a scar -> the rule isn't being applied.
- First model-inheritance miss via an ad-hoc Workflow script -> mechanize the seam.
- Three-dot counted log stays clean on DIFF fires -> promote to deny (only lines after ADR 0072's
  2026-07-17 narrowing count). First SKILL.md failing validate.py on main -> promote to rung 2.

## Act
- [outcome] verified — wave-1 shipped: `pr-create-guard.sh`, `check-workflow.mjs`,
  `check-restatement.mjs` run in `gates.yml`. The gate-has-test lint was deleted 2026-07-27
  (#311); wave-1's fourth item is unenforced.
