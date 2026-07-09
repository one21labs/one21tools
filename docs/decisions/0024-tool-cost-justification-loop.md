---
id: 0024
title: "Tool improvement loop: earn tokens better each iteration, cut only after benefit-per-token provably plateaus"
status: accepted
summary: "An artifact's PRIMARY obligation is to IMPROVE — raise benefit-per-token via a targeted edit informed by transcript-level diagnosis of the with-arm's weak cells — under a hermetic executor (ADR 0023) and the eval-clustered CI (ADR 0019). Cutting the artifact is the fallback, only after 3 valid improvement iterations provably plateau; a null under a confounded measurement doesn't count, and evals are never difficulty-raised to force a result."
---

# 0024 — tool improvement loop

- Date: 2026-07-08
- Owner: PM (owner-directed from the "do the repo's tools justify their cost" mission)
- Panel: owner-directed; grounded in the first hermetic ablation this session, which needed 3 iterations and surfaced the framing-sensitivity lesson. Check: the loop ran end-to-end and reached a verdict (KEEP on iteration 3).
- Context: char budgets enforce the COST side ("token efficiency enforced, not aspirational"); nothing enforced the BENEFIT side, so a skill/plugin/always-loaded section could sit in context on assertion alone, or get cut on one weak measurement instead of being IMPROVED. ADR 0023 made a treatment-free (hermetic) verdict possible; this ADR says the verdict's PRIMARY obligation is to raise benefit-per-token — cut is the fallback, not the goal.

## Decision
1. **Purpose: improve, not gatekeep.** An artifact's context cost is justified by actively maximizing benefit-per-token, not by clearing a bar once. Read the verdict off the eval-clustered CI (ADR 0019) under a hermetic executor (ADR 0023) — CI excludes zero and positive means it is MEASURABLY earning its cost — but a pass is not a stop condition: keep improving while a weak cell remains closeable.
2. **Improvement method, per iteration:**
   a. **Find weak cells** — losses and ties in the with-arm where the artifact should have helped (not evals it was never meant to move).
   b. **Diagnose at transcript level** — read the with-arm transcript for WHY it did not help: unclear, unactionable, not surfaced, buried past where the agent looked, or actively misleading.
   c. **Targeted edit** that closes the diagnosed gap AND/OR cuts the low-signal tokens the diagnosis exposed as dead weight — either move raises benefit-per-token (ADR 0019's honest denominator makes it a ratio, so a cut at unchanged benefit scores like an equal-cost benefit gain).
   d. **Re-measure hermetically** (ADR 0023); keep the edit only if benefit-per-token improved over the pre-edit baseline, else revert it.
3. **Never difficulty-raise evals to force a result.** A weak cell is closed by editing the ARTIFACT or fixing the DIAGNOSIS/measurement, never by rewriting an eval harder to manufacture a delta — a blind harder-pass regressed 6 cells to spurious negatives with only 1 clean fix (`benchmarks/2026-07-07-toolkit-grid/retune-results.md`); eval rewrites follow the DISCRIMINATE rule in `skills/building-skills/references/empirical-evals.md`, not this loop.
4. **Cut is the fallback.** Only after 3 VALID improvement iterations plateau (each re-measurement shows no benefit-per-token gain beyond noise) does the artifact fail: record the null (append-only, ADR 0019) and produce a plan for further empirical testing. An iteration may instead fix the MEASUREMENT (de-confound — e.g. hold the executor's base framing NEUTRAL: ablating always-loaded PROSE is framing-sensitive, one section measured +0.17 / 0.00 / +0.375 under tool-denied / implement-biased / neutral framings) rather than the artifact; a null under a confounded measurement does NOT count toward the 3. Never silently keep an unproven artifact, nor silently delete a cleanly-measured null.

## Justification
Forces every context-cost artifact toward its best benefit-per-token, not merely past a keep/cut line — stopping at a first pass leaves the same value on the table that an unmeasured artifact leaves cost unjustified. Bounded so it converges; record+plan preserves the finding instead of a silent keep/delete. Cost is low: reuses ADR 0023's executor and `eval_verdict.py`; the loop is protocol, not new machinery.

## Assumptions
- [verified] the loop is executable end-to-end — exercised on the CLAUDE.md-template "Feedback = PDCA trigger" section (KEEP on iter3, +0.375, 95% CI [+0.12, +0.64]) in `benchmarks/2026-07-08-claude-md-template-ablation-hermetic/`.
- [checkable] the hermetic executor + eval-clustered CI exist and are owned — ADR 0023 + `eval_verdict.py`/`eval_verdict_test.py` (gates); result: green.
- [unverifiable] 3 iterations distinguishes "artifact is weak" from "measurement is hard" — REOPEN-IF an artifact needs >3 VALID iterations to show a benefit that later replicates; then raise the cap or split measurement-fix vs artifact-fix budgets.

## Rejected alternatives
- Keep/cut as the loop's primary framing, improvement as an afterthought — leaves benefit-per-token gains on the table whenever an artifact clears the bar on iteration 1; the bar is a floor, not a ceiling.
- Delete any artifact that fails once — survivorship bias; a single confounded null is not evidence (iter1/iter2 here were confounded, iter3 was KEEP).
- Keep artifacts on assertion, no measurement — the unjustified-cost status quo this closes.
- Unbounded iteration — never converges; 3 + record/plan forces a decision.
- Raise eval difficulty to force a delta on a stuck cell — conflates measurement noise with artifact weakness; empirically regressed 6 cells (Decision 3).

## Revisit triggers
- An artifact needs >3 valid iterations for a benefit that later replicates -> raise the cap, or separate measurement-fix from artifact-fix iteration budgets.
- A recorded null is later shown beneficial under better testing -> the plan fired; re-measure and supersede the null.
