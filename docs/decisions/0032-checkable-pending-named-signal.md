---
id: 0032
title: "ADR-authoring: named-signal test for a [checkable] pending"
status: accepted
tier: lite
summary: "A [checkable] whose test the gate can run in-session ships verified/refuted, never pending; pending is reserved for a test awaiting a named future/external signal. Closes issue #36; no adr-lint rule — naming is substance a linter can't check. 0006/0007/0026/0027 comply."
---

# 0032 — checkable pending requires a named future/external signal

- Decision: adopt issue #36's clause verbatim into `adr-template.md`'s tag-routing paragraph, after
  "checkable (code) the gate verifies, unchecked = defect" — full rule text there (the named-signal
  test for a `[checkable]` pending). No adr-lint rule.
- Why: a runnable in-session check left `pending` is a defect, not a style choice (PRs #18/#19
  shipped that violation). ADR 0023:23's pending (gated on #31) is legitimate future-gating.
  Naming separates the classes with no linter (CLAUDE.md bars gating scripts for a 2-instance
  failure). 0026/0027's pendings resolve in place (runnable checks); 0006/0007's future-gated
  pendings name their signals.
- Enforced: `adr-template.md` tag-routing paragraph; `verifier.md:22-24`, unchanged.
