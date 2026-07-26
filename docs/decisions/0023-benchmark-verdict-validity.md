---
id: 0023
title: "Benchmark verdict validity: hermetic executor + auditable raw sample"
status: accepted
summary: "Two conditions make a paired-benchmark verdict trustworthy: HERMETIC EXECUTOR (control arm must be treatment-free) and AUDITABLE RAW SAMPLE (a bounded, deterministic sample kept on main). Full protocol: skill-bench/skills/bench/references/empirical-evals.md. Extends ADR 0019; keep-raw-only-if-used."
---

# 0023 — benchmark verdict validity: hermetic executor + auditable raw sample

- Date: 2026-07-08
- Owner: PM
- Context: two validity holes surfaced in one session: (a) two ablation snapshots came back
  confounded-null because control-arm executors inherited installed plugins/skill files; (b)
  evidence-selection bias (silently dropped or cherry-picked cells) is untestable once raw
  graded text is discarded.

## Decision
1. **Hermetic executor is required for a verdict.** A non-hermetic run is recorded
   (`hermetic: false`) as a confounded null, never a verdict; `metadata.json` carries
   `hermetic (y/n)`. Full gating protocol:
   `skill-bench/skills/bench/references/empirical-evals.md` ("Hermetic executor gates a verdict").
2. **Auditable raw sample, on main, gated on a consumer.** Retention turns ON only when
   `eval_verdict.py`'s completeness check ships (poka-yoke: no unused accumulation); until then,
   verdict lines + metadata only. ADR 0026 amends the raw-retention half (everything outside the
   sample is gzip-archived, not discarded). Sample definition: `empirical-evals.md` ("Auditable
   raw sample").

## Justification
Item 1 fixes the recurring confound at the layer that owns it instead of shipping a fourth
confounded null. Item 2 makes the reopen conditions below operable and the mitigation stack
reproducible, at bounded git-scale, only if a consumer actually uses it.

## Assumptions
- [checkable] the completeness check's decision logic is covered by `eval_verdict_test.py` —
  owner: gates; result: pending the check's implementation (#31).
- [unverifiable] a planted-defect + boundary sample is enough to catch evidence-selection.
  REOPEN-IF a silent-dropped cell is ever found outside the sample -> widen `sample_rule`.

## Rejected alternatives
- Off-main bundle + committed hash — detects modification, never deletion, rots silently.
- `raw_sha256` on every cell — a false certificate: unretained cells' text is deleted.
- Seeded random tranche — reintroduces the selection bias this ADR closes.
- Store nothing (status quo) — leaves the reopen conditions below inoperable.

## Revisit triggers
- `audit/` outgrows git-scale -> re-scope `sample_rule`, do not move off-main.
- A hermetic executor proves infeasible for a needed run -> reopen whether a recorded non-hermetic
  run may carry a directional (non-verdict) signal.
