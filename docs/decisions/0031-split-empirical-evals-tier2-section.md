---
id: 0031
title: "Split empirical-evals.md's Tier 2 section; house two homeless rules"
status: accepted
tier: lite
summary: "Extract Tier 2 (section ablation) from empirical-evals.md into a new reference file, freeing headroom for a 0/0-cell measurement-failure rule there, and a worktree-verification rule beside subagents.md's git-worktree advice (which gains a TOC, not a cap raise)."
---

# 0031 — split empirical-evals.md's Tier 2 section

- Decision: extract empirical-evals.md's "Tier 2 — section ablation" into
  `skill-bench/skills/bench/references/section-ablation.md`, leaving a cross-link stub. Add the
  0/0-cell rule ("a 0/0 cell is a measurement failure, fix the eval not the artifact") to
  empirical-evals.md's `## The verdict` section. Add the worktree-verification rule (a failed
  `cd` masks a wrong checkout; `git worktree add <branch>` checks out the stale local branch) to
  subagents.md's Parallelism subsection, which gains a `## Table of Contents` as a mechanical
  consequence of crossing 6,000 chars.
- Why: relocation-not-grandfather is the standing pattern (ADR 0009 did the same for
  optimizing-context's SKILL.md). Tier 2 is cited (ADR 0024) and is the VERIFY step of the
  retrospect->PDCA loop — cutting it would be a content loss dressed as a muda cut; the
  lazy-loaded reference tier costs a reader nothing until they need it.
- Rejected: raising REFERENCE_MAX_CHARS (loosens a guardrail to fix a 7-char overage); a
  per-file exception in validate.py (branches a zero-exception validator); cutting Tier 2
  outright (misfiled, not muda — it's cited and load-bearing).
- Reopen-if: a future reference cannot fit 12,000 after relocation -> revisit ADR 0009's cap.
- Enforced: `skill-bench/skills/bench/references/section-ablation.md`; subagents.md's
  `## Table of Contents`; validate.py's per-skill reference-cap walk.
