# skill-measure/scripts/lib

Shared helpers for benchmark harnesses (ADR 0026; moved from `benchmarks/lib`, #170 M1).
Stdlib only. Run any module's tests from this dir: `python3 <module>_test.py`.

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


## benchstats.py — the verdict rule (use this)

- `keep_verdict(delta, practical=0.0)` — the verdict rule (table: `skills/bench/references/
  cost-and-verdict.md`; rationale: the docstring). Also returns `half_width`, `mde80`, `win_rate`.
- `sd_between(delta)` / `clusters_for(sd, target)` — recover the between-scenario spread from a
  completed run, and size the next one from it rather than from a guess. A pre-registration states
  both the practical bar and the resulting scenario count.

## verdict.py — FROZEN, historical

- `verdict_of(mean, lo, hi, n)` — the rule shipped before 2026-07-27, kept unchanged because
  append-only dated aggregators import it (ADR 0041) and a re-run must reproduce what was
  published. **Not for new work**: its `|mean| < 0.05` branch names a small effect on data that
  support no effect size. New harnesses call `benchstats.keep_verdict`.
- `merge_verdict(mean_diff, ci_lo, ci_hi, n, chars_delta)` — the shared with-new-vs-with-old MERGE
  rule (ADR 0027, amended, both prongs: issue #142): PRIMARY `mean_diff > 0` -> MERGE, else NO
  MERGE. CI excludes 0 -> "strong" confidence, merges regardless of cost. CI straddles 0 -> "weak"
  confidence, contingent on the cost prong (ADR 0024 step 2d): `chars_delta` (always-loaded/body
  chars only) `> 0` reverts a weak merge to NO MERGE. Returns `(merge: bool, confidence: "strong" |
  "weak" | None)`. Frozen with `verdict_of`: new version-vs-version work runs
  `benchstats.keep_verdict` on the delta.


## hermetic_driver.py

- The shared hermetic `claude -p` executor plumbing (ADR 0023, issue #110): `CLAUDE_DENY_TOOLS`
  (loaded from `deny_tools.txt` — the one deny-list home, newline-delimited so a bash harness
  reads it too: `mapfile -t DENY < lib/deny_tools.txt`, ADR 0041), `NEUTRAL_FRAME`,
  `build_env(effort)`, `neutral_cwd(outdir)`, `do_call(prompt, model, env, cwd)`
  (one retry on timeout/nonzero exit) and `summarize_call(call)` (envelope figures + wall-clock +
  start/end timestamps), plus the per-cell grid mechanics `fresh_copy(src)` and
  `capture_artifacts(workdir, src)` (#191: capture for EVERY arm, never pre-existing corpus
  files). New harnesses import this; never copy it — start from `skill-measure/templates/grid.py`.
  The two pre-#110 harnesses keep their copies as append-only snapshots.

## artifact_check.py / blind.py / benchstats.py (#191 hardening)

- `artifact_check.check_artifact/classify_cells` (ERROR-cell rule),
  `blind.capture_symmetry(records, response_fn, excluded_fn)` (per-arm exclusion sweep),
  `benchstats.top_cell_attribution(cells, x, y)` (leave-one-out contributors). When each applies:
  `skills/bench/references/pre-registration.md` (Infrastructure is never quality) and
  `cost-and-verdict.md` (Mechanism claims cite cells).

## Workflow-pipeline persist step

A harness's grading `Workflow` (e.g. `grade.workflow.js`) enriches each agent's raw return via
`pipeline()`'s `.then(...)` (attaching `bid`, folding in the prosecutor pass, etc.). That enriched
array is the workflow's own RETURN VALUE, which lands in the run's task `.output` JSON under its
`"result"` field — NOT in `journal.jsonl`, which records each step's raw pre-`.then()` return and
was never meant to carry the enrichment.

Persist convention: read `result` from the task's `.output` JSON — never reconstruct it from
`journal.jsonl`. The template returns `{frame, cells, errors, audit}`: write `result.cells` with
`bench_io.dump_records(result["cells"], "graded/verdicts.jsonl", fmt="jsonl")`; `result.errors`
are ungraded cells (regenerate, then re-run `blind_cells.py`, whose `blind_salt.txt` at the bench
root keeps bids stable); keep `frame` with the grades until a cross-family re-grade.

When a prosecutor stage overrides `pass`/`met`, also overwrite every first-grader field it
re-judged (`evidence` at minimum) — otherwise the persisted record cites reasoning for the
overturned verdict (the self-contradictory-verdicts defect issues #49/#50 repaired).
