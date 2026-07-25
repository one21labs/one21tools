---
id: 0087
title: "adr-lint lite tier: Enforced line required; cited file tokens must resolve; free-form allowed"
status: accepted
tier: lite
summary: "#264: lite = settled = enforced, but adr-lint checked only disqualifiers. Now an Enforced: line is required and any file-like token it cites must resolve on disk (exact path or basename); token-free free-form stays legal (ADR 0075, ADR 0058) — the semantic bar stays with review."
---

# 0087 — lite ADRs: Enforced line required, cited files must resolve

- Decision: adr-lint gains a lite-tier positive check (#264): (1) an `Enforced:` line must be
  present in the body; (2) every file-like token it cites must resolve on disk — exact
  repo-relative path or basename match anywhere in the tree; (3) zero tokens = pass (free-form).
- Why: lite means settled, "enforced by a test/script/commit" (adr-template.md), yet the gate
  tested only disqualifiers — a lite record could cite nothing, or rot when a cited file is
  deleted or renamed (a basename-keeping move still resolves: grep-findable, so not rot).
  Measured on the 19-lite corpus first: strict (must cite a resolvable file) would fail the two
  legitimate free-form records (ADR 0075, ADR 0058); presence-only would never fire on rot. The
  hybrid fires on both mechanical defects at zero false positives; the semantic bar stays with
  advisory review.
- Enforced: `lint()` in `pdca-workflow/scripts/adr-lint.mjs` + paired cases in
  `adr-lint.test.mjs` (required CI).
