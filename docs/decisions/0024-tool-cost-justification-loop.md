---
id: 0024
title: "Tool cost-justification loop: hermetic with-vs-without, iterate 3x, else record + plan"
status: accepted
summary: "Char budgets enforce an artifact's COST; nothing enforced its BENEFIT, so skills/plugins/always-loaded doc sections were kept on assertion. This closes the loop: an artifact justifies its context cost only if it MEASURABLY beats its no-treatment baseline (with > without) under a hermetic executor (ADR 0023), verdict via the eval-clustered CI (ADR 0019). If not, iterate up to 3x (an iteration may fix the MEASUREMENT — e.g. hold the executor framing neutral — or the artifact); a null under a confounded measurement does not count. After 3 valid iterations with no benefit, record the null (append-only) and plan further testing — never silently keep an unproven artifact nor silently delete a cleanly-measured null."
---

# 0024 — tool cost-justification loop

- Date: 2026-07-08
- Owner: PM (owner-directed from the "do the repo's tools justify their cost" mission)
- Panel: owner-directed; grounded in the first hermetic ablation this session, which needed 3 iterations and surfaced the framing-sensitivity lesson. Check: the loop ran end-to-end and reached a verdict (KEEP on iteration 3).
- Context: char budgets enforce the COST side ("token efficiency enforced, not aspirational"); nothing enforced the BENEFIT side, so a skill/plugin/always-loaded section could sit in context on assertion alone. ADR 0023 made a treatment-free (hermetic) verdict possible; this ADR says what the verdict obligates.

## Decision
1. **Justification bar.** A skill, plugin, or always-loaded doc section justifies its context cost only if it MEASURABLY beats its no-treatment baseline (with > without) under a hermetic executor (ADR 0023), read off the eval-clustered CI (ADR 0019) — CI excludes zero and positive.
2. **Iterate up to 3x.** If it does not clear the bar, iterate and re-measure. An iteration may fix the MEASUREMENT (de-confound — e.g. hold the executor's base framing NEUTRAL: ablating always-loaded PROSE is framing-sensitive, one section measured +0.17 / 0.00 / +0.375 under tool-denied / implement-biased / neutral framings) OR the artifact text. A null under a confounded measurement does NOT count toward the 3.
3. **Record + plan fallback.** After 3 VALID iterations with no benefit beyond noise, record the null (append-only snapshot, ADR 0019) and produce a plan for further empirical testing (e.g. a multi-turn/contextual eval). Never silently keep an unproven artifact, nor silently delete a cleanly-measured null — the first is unjustified cost, the second is survivorship bias.

## Justification
Forces every context-cost artifact to earn its keep empirically, bounded so the loop converges, with the record+plan preserving the finding instead of a silent keep/delete. Cost is low: reuses ADR 0023's executor and `eval_verdict.py`; the loop is protocol, not new machinery.

## Assumptions
- [verified] the loop is executable end-to-end — exercised on the CLAUDE.md-template "Feedback = PDCA trigger" section (KEEP on iter3, +0.375, 95% CI [+0.12, +0.64]) in `benchmarks/2026-07-08-claude-md-template-ablation-hermetic/`.
- [checkable] the hermetic executor + eval-clustered CI exist and are owned — ADR 0023 + `eval_verdict.py`/`eval_verdict_test.py` (gates); result: green.
- [unverifiable] 3 iterations distinguishes "artifact is weak" from "measurement is hard" — REOPEN-IF an artifact needs >3 VALID iterations to show a benefit that later replicates; then raise the cap or split measurement-fix vs artifact-fix budgets.

## Rejected alternatives
- Delete any artifact that fails once — survivorship bias; a single confounded null is not evidence (iter1/iter2 here were confounded, iter3 was KEEP).
- Keep artifacts on assertion, no measurement — the unjustified-cost status quo this closes.
- Unbounded iteration — never converges; 3 + record/plan forces a decision.

## Revisit triggers
- An artifact needs >3 valid iterations for a benefit that later replicates -> raise the cap, or separate measurement-fix from artifact-fix iteration budgets.
- A recorded null is later shown beneficial under better testing -> the plan fired; re-measure and supersede the null.
