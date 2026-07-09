# benchmarks/lib

Shared helpers for benchmark harnesses (ADR 0026). Stdlib only.

## bench_io.py

- `dump_records`/`load_records(path, fmt="csv"|"tsv"|"jsonl")` — the record-format convention:
  flat/scalar records (arm maps, bid tables, per-cell scores) as CSV/TSV, nested list/dict values
  flattened into columns (a `ci` list -> `ci_lo`/`ci_hi`); text-heavy records (a prose `evidence`
  field) as minified JSONL.
- `sample_and_archive_raw(outputs_dir, keep_per_group, group_fn)` — keep a deterministic
  sorted-order sample of raw output files per group in place, gzip-archive the rest into one
  `all.tar.gz` (ADR 0023's sample rule + ADR 0026's raw-retention amendment).

Test: `cd benchmarks/lib && python -m unittest bench_io_test`

## verdict.py

- `verdict_of(mean, lo, hi, n)` — the shared KEEP/HARMFUL/CUT-CANDIDATE/INCONCLUSIVE rule (ADR
  0024): CI excludes 0 and positive -> KEEP, excludes 0 and negative -> HARMFUL, straddles 0 with
  |mean| < 0.05 -> CUT-CANDIDATE, else INCONCLUSIVE. One home instead of copy-pasted into each
  harness's `aggregate.py`.

Test: `cd benchmarks/lib && python -m unittest verdict_test`

## Workflow-pipeline persist step

A harness's grading `Workflow` (e.g. `grade.workflow.js`) enriches each agent's raw return via
`pipeline()`'s `.then(...)` (attaching `bid`, folding in the prosecutor pass, etc.). That enriched
array is the workflow's own RETURN VALUE, which lands in the run's task `.output` JSON under its
`"result"` field — NOT in `journal.jsonl`, which records each step's raw pre-`.then()` return and
was never meant to carry the enrichment.

Persist convention: read `result` from the task's `.output` JSON and write it straight to the
benchmark's `graded/*.jsonl` with `bench_io.dump_records(result, "graded/verdicts.jsonl",
fmt="jsonl")` — never reconstruct it from `journal.jsonl`.
