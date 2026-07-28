---
id: 0024
title: "Tool improvement loop: earn tokens better each iteration, cut only after benefit-per-token provably plateaus"
status: accepted
summary: "An artifact's PRIMARY obligation is to IMPROVE — raise benefit-per-token via a targeted edit informed by transcript-level diagnosis of weak cells — under a hermetic executor (ADR 0023) and the eval-clustered CI (ADR 0019). Cutting is the fallback, only after 3 valid iterations provably plateau; evals are never difficulty-raised to force a result."
---

# 0024 — tool improvement loop

- Date: 2026-07-08
- Owner: PM
- Context: char budgets enforce the COST side; nothing enforced the BENEFIT side, so an artifact could sit in context on assertion, or get cut on one weak measurement instead of being improved.

## Decision
1. **Purpose: improve, not gatekeep.** Read the verdict off the eval-clustered CI (ADR 0019) under a hermetic executor (ADR 0023) — CI excludes zero and positive means it is measurably earning its cost — but a pass is not a stop condition: keep improving while a weak cell remains closeable.
2. **Improvement method, per iteration:** (a) find weak cells in the with-arm; (b) diagnose at TRANSCRIPT level why it did not help; (c) a targeted edit closing the gap and/or cutting low-signal tokens; (d) re-measure hermetically, keep only if improved, else revert. The arm-construction script must derive the touched-file set from the draft's git diff (a treatment blind to the edits is a rigged null).
3. **Never difficulty-raise evals to force a result** — a weak cell is closed by editing the artifact or fixing the diagnosis/measurement, never by rewriting an eval harder.
4. **Cut is the fallback.** Only after 3 VALID iterations plateau does the artifact fail: record the null (append-only, ADR 0019) and produce a plan for further testing. A confounded measurement fix doesn't count toward the 3.

## Justification
Forces every context-cost artifact toward its best benefit-per-token, not merely past a keep/cut line. Bounded so it converges; record+plan preserves the finding instead of a silent keep/delete.

## Assumptions
- [verified] the loop is executable end-to-end — exercised on the CLAUDE.md-template ablation (`benchmarks/2026-07-08-claude-md-template-ablation-hermetic/`), KEEP on iteration 3, +0.375, 95% CI [+0.12, +0.64].
- [checkable] the hermetic executor (ADR 0023) + eval-clustered CI (ADR 0019) exist and are owned — `eval_verdict.py`/`eval_verdict_test.py` (gates). result: green.
- [unverifiable] 3 iterations distinguishes "artifact is weak" from "measurement is hard" — REOPEN-IF an artifact needs >3 VALID iterations to show a benefit that later replicates; raise the cap or split measurement-fix vs artifact-fix budgets.

## Rejected alternatives
- Keep/cut as the primary framing — leaves gains on the table on iteration 1; delete any artifact that fails once — a confounded null isn't evidence; unbounded iteration — never converges; raise eval difficulty — mistakes noise for weakness.

## Revisit triggers
- An artifact needs >3 valid iterations for a benefit that later replicates -> raise the cap, or separate measurement-fix from artifact-fix budgets.
- A recorded null is later shown beneficial under better testing -> re-measure and supersede it.

## Act (2026-07-27) — decision 1 restored in code, and extended
The shipped rule read the verdict off the point estimate, not the CI. Restored, plus an owner-set
practical bar tested on the interval's LOWER bound, a per-scenario win rate, and CUT only on an
equivalence result. Rule, rationale and sizing (`sd_between`/`clusters_for`) live at
`skill-bench/scripts/lib/benchstats.py:keep_verdict` — the one home (ADR 0092), which is why this
is an amendment, not a new record. `lib/verdict.py` is FROZEN for 11 append-only dated
aggregators (ADR 0041); the single recomputation of record is in #310.
