---
id: 0027
title: "EP re-measure: reference-inclusive symmetric arms, in-run baseline"
status: accepted
tier: lite
summary: "Issue #52 re-measure of engineering-principles-improve: same-run 3-arm (without / with-old / with-new), appending the 3 touched reference files to both with-arms. Rejects body-only: 6 of 9 edits live in references, repeating EP's ~8x cost confound. Merge bar: directional mean(diff)>0, CI reported not gating. Flat/negative escalates to Option E as a diagnostic."
---

# 0027 — EP re-measure: arm construction, merge bar

- Decision: same-run 3-arm design (`without` / `with-old` / `with-new`), appending the 3 touched
  reference files to BOTH with-arms — extends ADR 0019's `--include-references` to the benefit
  side. Merge bar: `diff = d_new - d_old` (each vs `without`); `mean(diff) > 0` merges,
  directional — per-eval CI is reported, never gating (n=6 evals makes CI-exclusion
  unsatisfiable). `d_new <= 1e-9` on ANY of evals {1,2,5,6} escalates to Option E as a diagnostic.
- Why: body-only repeats, on the benefit side, the ~8x cost confound ADR 0019 fixed on cost — 6
  of 9 edits live in 3 touched references, so body-only is blind to most of the change. Strict
  CI-excludes-0 would veto nearly every real improvement at this eval count.
- Rejected: body-only rerun (blind to 6/9 edits) — Option E immediately (worth it only once evals
  come back flat) — strict CI-excludes-0 on `diff` (rejects real improvement by construction).
- Reopen-if: `d_new<=1e-9` fires on any of evals 1/2/5/6 -> run Option E before writing off the
  reference edits.
- Enforced: `benchmarks/2026-07-09-ep-remeasure-hermetic/metadata.json` (arm + bar
  pre-registration), `results.jsonl` (the numbers), `aggregate.py`/`blind.py` (3-arm adaptation).
