---
id: 0101
title: "#317 expectation coupling: blind authoring by default, every batch reports a provenance split; no task-value instrument yet"
status: accepted
tier: lite
summary: "On 12-Oct data the skill effect is +0.31 on the original evals versus +0.04 on blind-authored ones, so the coupling is plausibly real. Decision: new evals are blind-authored, and each batch reports the delta split by provenance as a pre-registered secondary next to the overlap number. Executable task-value outcomes wait on the confirmatory split."
---

# 0101 — expectation coupling: measure the split, defer the rebuild

- Decision: (1) every new eval is authored blind, by a lane that sees only the skill's public
  description; (2) every batch reports the (with - without) delta split by eval provenance
  (original vs blind) as a pre-registered secondary, alongside overlap.json; (3) no
  executable task-value outcome is built yet. The 2026-10-12-g8-shortfall batch is the
  confirmatory test.
- Why: post hoc on the 12-Oct grid, original ids 1-6 gave a delta of +0.31 (bare 0.49, n=39
  eval-model pairs) and blind ids 7-10 gave +0.04 (bare 0.78, n=18). With the skill, both groups
  reached about 0.81. Normalized for headroom, that is 0.62 vs 0.17. Difficulty and provenance are
  confounded, so this is a lead, not a verdict.
- Rejected: building task-value outcomes now. That rewrites every eval and the judge before the
  split is confirmed. A gate on trigram overlap: that number is a floor, and a gate on it would
  certify paraphrase-coupled sets as clean.
- Reopen-if: in the confirmatory batch, the delta CI on the NEW blind ids (11+) excludes the
  original-id point estimate (ids 7-10 made the lead, so cannot confirm it). Then the
  original-eval KEEPs are suspect and task-value outcomes get decided next; #317 stays open.
- Enforced: `benchmarks/2026-10-12-g8-shortfall/metadata.json` (secondary metric)
