---
id: 0023
title: "Benchmark verdict validity: hermetic executor + auditable raw sample"
status: accepted
summary: "Two conditions make a paired-benchmark verdict trustworthy, both surfaced this session. (1) HERMETIC EXECUTOR: a run counts toward a keep/cut verdict only if the control arm had zero installed plugins and zero repo/skill file access (cloud container, or a locked-down claude -p); a non-hermetic run is recorded but is a confounded null, never a verdict. (2) AUDITABLE RAW SAMPLE: retain the raw graded text for a bounded, deterministically-defined sample (planted-defect set + boundary-straddling cells) ON MAIN under benchmarks/<date>/audit/ — git self-verifies it, so no per-cell hash and no off-main bundle — and only once a live consumer (an eval_verdict.py completeness check) reads it. Extends ADR 0019; keep-raw-only-if-used."
---

# 0023 — benchmark verdict validity: hermetic executor + auditable raw sample

- Date: 2026-07-08
- Owner: PM
- Panel: two advisors unprimed (minimalist "hash-only" vs auditability "retain-a-sample"); red-team broke the first draft on three points (folded below); verifier reproduced every load-bearing claim; a /retrospect finding named the recurring confound. Check: gates + the completeness check's own test (`eval_verdict_test.py`).
- Context: two validity holes appeared in one session. (a) Two ablation snapshots came back CONFOUNDED NULL because control-arm executors inherited installed plugins / read repo skill files — the identical confound `benchmarks/2026-07-07-toolkit-grid/trigger-kit/FINDINGS.md` documented a day earlier but that the owning layer never absorbed. (b) Evidence-selection bias (silent-dropped or cherry-picked cells) is untestable and ADR 0019's own reopen CONDITIONS (re-grade a committed cell) are inoperable, because the raw graded text is discarded.

## Decision
1. **Hermetic executor is required for a verdict.** A paired run counts toward a keep/cut verdict only if the control arm had zero installed plugins AND zero repo/skill file read access — a cloud container (cleanest, treatment-free by construction), or a locked-down `claude -p` (`enabledPlugins: {}`, deny the `Skill`/`Agent`/`Read`/`Grep`/`Glob` tools, `CLAUDE_CONFIG_DIR` at an empty dir). A non-hermetic run is RECORDED (`hermetic: false`) as a confounded null and is never a verdict. `metadata.json` carries `hermetic (y/n)`.
2. **Auditable raw sample, on main, gated on a consumer.** Retain the raw graded TEXT for a bounded, DETERMINISTICALLY-defined sample — the planted-defect calibration set + every cell whose eval-clustered CI straddles the verdict boundary (both re-derivable from committed data) — ON main under `benchmarks/<date>/audit/`. Git content-addresses it (self-verifying, no dangling pointer), so NO per-cell hash and NO off-main bundle. `metadata.json` records the machine-readable `sample_rule`. The sample is load-bearing, not decorative: `eval_verdict.py` re-derives `sample_rule`, asserts every selected cell's transcript is present (the silent-drop tripwire) — and it is what the prosecutor / sampled-agreement / human-calibration passes and ADR 0019's re-grade reopen-conditions read. Retention turns ON only when that check ships (poka-yoke: no unused accumulation); until then, verdict lines + metadata only. Deferred work in #31.

## Justification
Item 1 fixes the recurring confound at the layer that owns it (ADR 0019: "fix the instrument, don't caveat it") instead of shipping a fourth confounded null. Item 2 makes ADR 0019's reopen conditions operable and its mitigation passes reproducible, at bounded git-scale — not the full raw run trees ADR 0019 rejected — and only if a consumer actually uses it (owner rule: keep raw only if used).

## Assumptions
- [checkable] the completeness check's decision logic is covered by `eval_verdict_test.py` — owner: gates; result: pending the check's implementation (#31).
- [verified] `eval_set_sha256` is committed precedent and eval INPUTS already live on-main in git, so on-main audit TEXT follows an established pattern — `benchmarks/2026-07-07-toolkit-grid/`.
- [unverifiable] a planted-defect + boundary sample is enough to catch evidence-selection — REOPEN-IF a silent-dropped cell is ever found outside the sample; then widen `sample_rule`.

## Rejected alternatives
- **Off-main bundle (release asset / data branch) + committed hash** — false durability: a hash detects modification, never deletion, and with no CI fetch it rots silently; a bounded sample is git-scale, so it belongs in git.
- **`raw_sha256` on every cell** — a false certificate: unretained cells' text is deleted, so the hash is non-recomputable yet reads like the verifiable `eval_set_sha256`; write nothing for unretained cells.
- **Seeded random tranche** — reintroduces the selection bias ADR 0019 closed and is re-rollable by the dogfooding party; deterministic sets only. REOPEN-IF a random audit draw is wanted: pre-register seed + RNG + ordered-population hash on-main BEFORE drawing.
- **Store nothing (status quo)** — leaves ADR 0019's reopen conditions inoperable and half its mitigation stack unreproducible.
- **A CI job that fetches + verifies bundles** — machinery ahead of demand; the local completeness check consumes the on-main sample every aggregation instead.

## Revisit triggers
- `audit/` outgrows git-scale -> it was not bounded; re-scope `sample_rule`, do not move off-main.
- A random audit draw is wanted -> pre-register seed / RNG / population hash on-main before drawing.
- A hermetic executor proves infeasible for a needed run -> reopen whether a recorded non-hermetic run may carry a directional (non-verdict) signal.
