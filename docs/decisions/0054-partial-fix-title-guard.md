---
id: 0054
title: "Partial-fix title guard: deny only the title-closes / body-declares-partial mismatch"
status: accepted
tier: lite
summary: "A closing-keyword PR title becomes the squash subject and silently auto-closes an issue even when the PR is partial (scar: PR #166 closed #164 with 2 findings open, no red CI). CI extension of check-pr-body.mjs: a `Partial: #NNN` body line; DENY iff the title closes an issue the body declares partial; silent intent PASSes (owner ruling)."
---

# 0054 — partial-fix title guard

- Decision: CI guard extends `check-pr-body.mjs`, run on `pull_request` types
  `[opened, edited, synchronize, reopened]` (a title edited post-run must re-trigger). Adopt a
  body line `Partial: #NNN` = "this PR does NOT fully close issue #NNN". Predicate: extract
  closing-keyword refs from the title (`close(s|d)|fix(es|ed)|resolve(s|d)`, colon optional) into
  `titleCloses`; extract every `#NNN` following a `Partial:` line (fenced code/HTML comments
  stripped first) into `bodyPartials`; DENY iff the two sets intersect — a decidable contradiction.
  PASS otherwise: a title closing an issue the body is SILENT on is undecidable intent and is
  never denied (owner ruling — banning bare closing titles is too strict).
- Why: PR #166's title auto-closed #164 on merge with 2 findings open, no red CI (GitHub scans
  the squash subject for closing keywords) — worth gating on the one decidable signal.
- Rejected: blanket deny on any closing-keyword title (owner-rejected); a rung-5 prose title
  convention (a decidable requirement with an available CI surface is never homed in prose).
- Reopen-if: a partial-fix mis-close recurs with a prose-only "stays open" signal -> strengthen
  adoption (PR-template scaffolding). Residue: a hand-edited squash title post-CI; a single-commit
  PR whose lone commit message carries the closing keyword.
- Enforced: `scripts/check-pr-body.mjs` + `scripts/check-pr-body.test.mjs`; amended by ADR 0078.
