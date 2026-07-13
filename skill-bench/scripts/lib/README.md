# benchmarks/lib

Shared helpers for benchmark harnesses (ADR 0026). Stdlib only.

Convention: a derived/regenerable intermediate (a prep script's output that duplicates committed
substrate data) gets a `.gitignore` entry in its benchmark dir BEFORE first commit (ADR 0026) —
its home is the script that regenerates it, not git.

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
- `merge_verdict(mean_diff, ci_lo, ci_hi, n, chars_delta)` — the shared with-new-vs-with-old MERGE
  rule (ADR 0027, amended, both prongs: issue #142): PRIMARY `mean_diff > 0` -> MERGE, else NO
  MERGE. CI excludes 0 -> "strong" confidence, merges regardless of cost. CI straddles 0 -> "weak"
  confidence, contingent on the cost prong (ADR 0024 step 2d): `chars_delta` (always-loaded/body
  chars only) `> 0` reverts a weak merge to NO MERGE. Returns `(merge: bool, confidence: "strong" |
  "weak" | None)`. A new `aggregate.py` computing a merge verdict imports this instead of
  restating the bar — the bs-iter2 discrepancy (`aggregate.py` printed "MERGE (weak)" where the
  cost prong says NO MERGE, `benchmarks/2026-07-09-bs-iter2-remeasure/README.md`) was exactly this
  class of drift.

Test: `cd benchmarks/lib && python -m unittest verdict_test`

## hermetic_driver.py

- The shared hermetic `claude -p` executor plumbing (ADR 0023, issue #110): `CLAUDE_DENY_TOOLS`
  (loaded from `deny_tools.txt` — the one deny-list home, newline-delimited so a bash harness
  reads it too: `mapfile -t DENY < lib/deny_tools.txt`, ADR 0041), `NEUTRAL_FRAME`,
  `build_env(effort)`, `neutral_cwd(outdir)`, `do_call(prompt, model, env, cwd)`
  (one retry on timeout/nonzero exit) and `summarize_call(call)` (envelope figures + wall-clock +
  start/end timestamps). New harnesses import this; never copy it. The two pre-#110 harnesses keep
  their copies as append-only snapshots.

Test: `cd benchmarks/lib && python -m unittest hermetic_driver_test`

## Workflow-pipeline persist step

A harness's grading `Workflow` (e.g. `grade.workflow.js`) enriches each agent's raw return via
`pipeline()`'s `.then(...)` (attaching `bid`, folding in the prosecutor pass, etc.). That enriched
array is the workflow's own RETURN VALUE, which lands in the run's task `.output` JSON under its
`"result"` field — NOT in `journal.jsonl`, which records each step's raw pre-`.then()` return and
was never meant to carry the enrichment.

Persist convention: read `result` from the task's `.output` JSON and write it straight to the
benchmark's `graded/*.jsonl` with `bench_io.dump_records(result, "graded/verdicts.jsonl",
fmt="jsonl")` — never reconstruct it from `journal.jsonl`.

When a prosecutor stage overrides `pass`/`met`, also overwrite every first-grader field it
re-judged (`evidence` at minimum) — otherwise the persisted record cites reasoning for the
overturned verdict (the self-contradictory-verdicts defect issues #49/#50 repaired).
