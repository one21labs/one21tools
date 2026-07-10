---
id: 0031
title: "Split empirical-evals.md's Tier 2 section; house two homeless rules"
status: accepted
summary: "Extract Tier 2 (section ablation) from empirical-evals.md into a new reference file, freeing headroom for a 0/0-cell measurement-failure rule there, and a worktree-verification rule beside subagents.md's git-worktree advice (which gains a TOC, not a cap raise)."
---

# 0031 — Split empirical-evals.md's Tier 2 section; house two homeless rules

- Date: 2026-07-09
- Owner: PM
- Panel: process-economist, plugin-adopter (both converge on the split; unanimity examined below)
- Context: issue #56 measured both reference caps as "saturated": `empirical-evals.md` 11,993/12,000 chars (skills/building-skills/references/empirical-evals.md, REFERENCE_MAX_CHARS, validate.py:32) and `subagents.md` 5,978/6,000 (skills/optimizing-context/references/subagents.md). Only the first is a real ceiling: 6,000 for a reference is REFERENCE_TOC_THRESHOLD (validate.py:33) — the point a TOC becomes mandatory — not REFERENCE_MAX_CHARS; subagents.md's actual ceiling is 12,000, with ~6,000 chars of headroom once it carries a `## Table of Contents` (validate.py:262-263 gates TOC presence past 6,000, not size). Two rules are homeless: "a 0/0 cell is a measurement failure, fix the eval not the artifact" (issue #49) and a multi-worktree verification note (a failed `cd` masks a wrong checkout; `git worktree add <branch>` checks out the stale local branch).

## Decision
1. Extract empirical-evals.md's self-named "Tier 2 — section ablation" (lines 168-187, 1,574 chars) into a new reference file `skills/building-skills/references/section-ablation.md`; leave a short cross-link stub where the section was.
2. Add the 0/0-cell rule to empirical-evals.md's `## The verdict` section (after the win-rate/CI bullet, ~line 128) — its natural home once the split frees room.
3. Add the worktree-verification rule to subagents.md's Parallelism subsection, beside "give each worker its own git worktree" (line 79) — the home the issue itself names. subagents.md crosses 6,000 chars as a result; add its `## Table of Contents` in the same edit (mechanical, not a judgment call).
4. Reject raising REFERENCE_MAX_CHARS or adding a per-file exception: only one file was ever actually blocked; loosening the cap or branching the validator to fix a one-file problem outlives the problem.

## Justification
Relocation-not-grandfather is the standing pattern, not a new call: ADR 0009 brought optimizing-context's own SKILL.md under cap by "relocating depth into a new reference" — subagents.md IS that relocation's product. Splitting Tier 2 the same way follows precedent rather than setting one. The section is self-labeled "Tier 2" (an explicitly optional advanced tier), so the split boundary is the file's own framing, not judgment invented for this ADR. Rejected the muda-pass (trim/cut) the panel converged toward without examining: Tier 2's framing-sensitivity finding is restated in ADR 0024 item 4, and the section is the VERIFY step of the retrospect->PDCA loop (empirical-evals.md:183-184), and is not duplicated or dead anywhere else in the corpus — cutting active, cited methodology to free space is a content loss dressed as a muda cut. Relocating it to its lower home (the progressive-disclosure reference tier, confirmed lazy-loaded per SKILL.md:62,121) costs a reader nothing until they need Tier 2 — the split, not the cut, is the true zero-added-cost option.

## Assumptions
- [verified] The split frees enough room for both rules — simulated the full edit this session: empirical-evals.md lands at 10,871 chars (1,129 under the 12,000 cap) after removing Tier 2, adding the cross-link stub, and adding the 0/0 rule.
- [verified] subagents.md post-edit (worktree rule + TOC) lands at 6,973 chars — inside 12,000, and correctly carries a TOC since it now exceeds the 6,000 TOC threshold. Simulated this session against the live file.
- [verified] References load lazily, per-file, so the split's read cost is paid only on demand — skills/building-skills/SKILL.md:62 ("Everything else loads on-demand"), :121 ("progressive disclosure ... details in references").
- [checkable] Both edited files + the new `section-ablation.md` (1,847 chars) pass `validate.py` (no emoji, caps, TOC gate) and every cross-link resolves. TEST: `python skills/building-skills/scripts/validate.py skills/optimizing-context` and the equivalent for building-skills — validate.py's reference walk is per-skill-folder, independent of which skill authored validate.py. — owner: verifier.

## Rejected alternatives
- Raise REFERENCE_MAX_CHARS — loosens a guardrail every plugin consumer inherits, to fix one file's 7-char overage; both advisors reject it, consistent with ADR 0009's no-exemptions precedent.
- Per-file exception in validate.py — adds branching to a zero-exception validator; the precedent compounds past this one case.
- "Fix" subagents.md's cap — it was never blocked (6,000 is its TOC threshold, not its ceiling); nothing to fix beyond the TOC its new content triggers.
- Cut Tier 2 outright (muda pass, zero new files) — the unanimity flag's candidate; rejected because the content is cited (ADR 0024), load-bearing for the retrospect->PDCA VERIFY step, and not duplicated elsewhere — misfiled, not muda.

## Revisit triggers
- A future reference legitimately cannot fit 12,000 after relocation -> revisit ADR 0009's cap tier, not this file split.
- subagents.md crosses 12,000 after further additions -> its own split becomes due.
