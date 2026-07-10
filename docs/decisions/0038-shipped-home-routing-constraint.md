---
id: 0038
title: "Operational rules live in shipped files, not repo-only surfaces"
status: accepted
summary: "The shipped-home routing constraint (owner-stated, #93): a rule a skill/plugin applies in operation lives in a file that ships and loads with it (SKILL.md, references/, plugin agents/hooks/scripts, validate.py, vendored adr-lint.mjs); repo-level surfaces (CLAUDE.md, docs/decisions/, .github/, gates.yml) are dogfood-instance config a consumer never loads — they may point at the shipped home, never solely house it. Operationalized as a shipping-boundary row in jit-documentation.md's Decision Test (#93 item 9d). Governs home-selection in ADRs 0039-0042."
---

# 0038 — Operational rules live in shipped files, not repo-only surfaces

- Date: 2026-07-10
- Owner: PM
- Panel: lean-process-engineer, process-economist, session-operator, plugin-adopter (unanimous accept as its own ADR).
- Context: `jit-documentation.md`'s Decision Test (jit-documentation.md:18-25) routes placement by SCOPE only (every-file / module / plan / reusable) — it has no row for the install-portability axis, so operational rules silently land in repo-only homes (earlier #93 drafts mis-routed items 2, 3, 4, 6, 8b). Owner stated the constraint 2026-07-10 (#93).

## Decision
Adopt the routing constraint as a reusable placement principle: an operational rule a skill/plugin enforces lives in a SHIPPED file (SKILL.md, `references/`, plugin `agents/`/`hooks/`/`scripts/`, `validate.py`, vendored `adr-lint.mjs`); repo-level surfaces MAY point at the shipped home, never solely house it. Operationalize it in its OWN shipped home: add a shipping-boundary row to `jit-documentation.md`'s Decision Test (#93 item 9d) — "Must the rule travel with the skill/plugin when installed elsewhere? → a shipped skill/plugin file; repo docs may point, never solely house." ADRs 0039/0040/0041/0042 cite this ID for their home-selection.

## Justification
Cost ~0 (one Decision-Test row). Risk low (additive; moves no existing rule). Value high: the constraint is invoked by 6+ countermeasures across this batch; housing it once (poka-yoke — the Decision Test now forces the portability question) prevents the recurring mis-route that needed owner correction. Self-consistent: the constraint's own home is the shipped `jit-documentation.md`, not this repo's CLAUDE.md.

## Assumptions
- [verified] jit-documentation.md:18-25 Decision Test routes by scope only, no portability row — read 2026-07-10 (rows: every-file / module / plan / reusable).
- [checkable] after the edit jit-documentation.md carries the shipping-boundary row and stays under the references cap (file is 3,771 chars; cap 12,000) — owner: verifier; result: ample headroom, falsifiable at build.
- [checkable-doc] no accepted ADR already houses this constraint — verified: grep of docs/decisions found none; 0015 is mirror-specific, not portability.

## Rejected alternatives
- House it in this repo's CLAUDE.md — violates the constraint itself (repo-only, doesn't ship); CLAUDE.md may carry a pointer.
- Leave it implicit in #93 — the mis-route already recurred; an unhoused principle re-fails.

## Revisit triggers
- A new operational rule lands in a repo-only home despite the Decision-Test row → the wording is insufficient; strengthen it or add a validate.py check.
