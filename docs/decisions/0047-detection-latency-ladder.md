---
id: 0047
title: "Executable-home rule + detection-latency ladder as named policy; wave-1 build scope"
status: accepted
summary: "A decidable requirement is never homed in prose — its core needs an executable home (rung 1-4) where a surface binds it (owner rule); the ladder (1 prevent > 5 prose) ranks WHICH rung, upgrades need cited scar. Homed at engineering-principles in general form; jit-documentation.md:23 keeps its 9a anchor + a pointer (not superseded). Wave-1 build scope: publication guard, check-workflow + check-restatement (WARN) per-edit, a gate-has-test lint. Reject validate.py (no scar); three-dot warn+counted log; name the Workflow seam."
---

# 0047 — Executable-home rule + detection-latency ladder

- Date: 2026-07-10
- Owner: PM
- Context: poka-yoke was doctrine but never ranked into rungs, and decidable requirements kept
  shipping as prose (the PR#134 pipe-mask scar, #75) while ADR 0038/0039/0040 decided rung
  ordering ad hoc.

## Decision
- **Rule:** a DECIDABLE requirement is never homed in prose — its CORE needs an executable home
  (rung 1-4) at authoring time where an AVAILABLE SURFACE binds it. No surface yet (sync-before-
  spend) => interim prose deferring to ADR 0043's trigger. Judgment shells stay rung-5.
- **Ladder:** 1 prevent (deny) > 2 detect-at-creation (PostToolUse) > 3 commit > 4 CI > 5 prose.
  Executable home is mandatory; the rung, or any rung upgrade, needs a cited scar + economics. A
  full-coverage mechanism deletes its rung-5 prose mirror (check-restatement.mjs); a CI backstop
  stays.
- **Preconditions:** (i) a partial predicate ships with its residue recorded (ADR 0030); (ii)
  undecidable-intent rules WARN, never deny (cry-wolf risk); (iii) surface-bound.
- **One home** — engineering-principles carries the ladder in GENERAL form; repo scars stay
  here, never the shipped file (ADR 0038 inversion guard). `jit-documentation.md:23` stays
  (its own 9a anchor, cited by ADR 0039/0040) + gains a pointer — not superseded.
- **Wave-1 build scope** (each ships as a testable file in the CI glob): a publication guard
  (PreToolUse Bash forcing `gh pr/issue create` to `--body-file` with disclosure, scars #75 and
  anthropics/skills#1414); `check-workflow.mjs` per-edit (scar #53); `check-restatement.mjs`
  per-edit (WARN-only, undecidable heuristic, diff-scoped); a gate-has-test lint.
- **Rejected wave-1 items:** validate.py per-edit (already rung-4 CI, no scar for a rung-2
  upgrade); a three-dot-diff hook as deny (WARN + counted instead — two-dot intent is
  undecidable, deny false-blocks); mechanizing the Workflow-tool seam (named, not built — no
  scar yet).
- **NOTE (2026-07-26):** the PR#134 pipe-mask scar named above got NO wave-1 remedy — the list
  is four items and a pipe guard is not among them. A `gate-pipe-guard.sh` was nonetheless built
  citing "ADR 0047 wave-1" authority this record never granted, and was deleted 2026-07-26 as
  undecided (ADR 0091). The scar remains unremedied here; do not read wave-1 as covering it.

## Justification
Splits MUST-it-be-executable (decidable core) from WHICH-rung (scar + economics); the scar bar
self-enforces (refutes the validate.py and Workflow-seam rejections); wave-1 predicates ship
testable, dogfooding the gate-has-test lint itself.

## Assumptions
- [checkable] every wave-1 accept carries a cited scar, pr-create-guard doesn't false-deny a
  benign `gh pr create`, and the gate-has-test lint fails a gate missing its test — all verified
  at build (9/9 test pass).
- [unverifiable] WEAKEST — a PostToolUse warn/exit actually redirects the agent instead of being rationalized past. REOPEN-IF a retro shows a shipped hook was ignored.

## Rejected alternatives
- Superseding `jit-documentation.md:23` in place — orphans existing cites and inverts altitude
  (ADR 0038); it stays and points instead.

## Revisit triggers
- A decidable requirement rests at prose despite an available surface, or a rung upgrade ships
  without a scar -> the rule isn't being applied.
- First model-inheritance miss via an ad-hoc Workflow script -> mechanize the seam.
- Three-dot counted log stays clean on DIFF fires -> promote to deny (ADR 0072 narrowed the
  predicate; pre-2026-07-26 lines are log/rev-list noise and do not count). First SKILL.md
  failing validate.py on main -> promote validate.py to rung 2.

## Act
- [outcome] verified — wave-1 shipped: `pr-create-guard.sh`, `check-workflow.mjs`,
  `check-restatement.mjs`, `check-gate-tests.mjs` all exist and run in `gates.yml`.
