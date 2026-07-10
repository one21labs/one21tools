---
id: 0032
title: "ADR-authoring: named-signal test for a [checkable] pending"
status: accepted
tier: lite
summary: "A [checkable] whose test the gate can run in-session ships verified/refuted, never pending; pending is reserved for a test awaiting a named future/external signal. Closes issue #36; no adr-lint rule — naming is substance a linter can't check, and it already caught the ADR 0027 pending pre-merge."
---

# 0032 — checkable pending requires a named future/external signal

- Decision: adopt issue #36's clause verbatim into `adr-template.md`'s tag-routing paragraph,
  after "checkable (code) the gate verifies, unchecked = defect": a `[checkable]` whose test is a
  deterministic in-session check (command, file read, formula) ships verified/refuted, never
  pending — a runnable check left pending is the defect. pending is reserved for a test awaiting
  a future/external signal, which must be NAMED. No adr-lint rule.
- Why: PRs #18/#19 shipped pending on checks already runnable in-session; ADR 0023:23's pending
  (gated on #31) is legitimate future-gating; ADR 0026:28 is the violation class — its committed
  144-record fixture needs no future signal, so re-derive it now, in this PR, not an issue.
  Naming separates the classes with no linter (CLAUDE.md bars gating scripts for a 2-instance
  failure) — naming alone already caught and fixed the ADR 0027 pending pre-merge.
- Enforced: `adr-template.md` tag-routing paragraph; `verifier.md:22-24`, unchanged.
