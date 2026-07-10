---
id: 0026
title: "Benchmark artifact format: measured-ratio convention + sampled-plus-gzip raw retention"
status: accepted
summary: "Measured token ratios (arm_map, 144 records; pretty-json 1.00x baseline) show flat records compress hard under CSV/TSV (0.45x) while text-heavy records (a prose evidence field) barely move by format (0.92x-0.98x) — evidence text dominates. Sets the benchmark-artifact-format convention (CSV for flat/scalar records with nested values flattened into columns, minified JSONL for text-heavy records, small JSON/YAML for human-read config, gitignore derivable intermediates) and amends ADR 0023's raw retention: the deterministic on-main sample stays plain text, everything else is gzip-archived into one file per benchmark instead of silently discarded. Governs stored/agent-read artifacts only; always-loaded context stays char-budget governed."
---

# 0026 — benchmark artifact format: measured-ratio convention + sampled-plus-gzip raw retention

- Date: 2026-07-09
- Owner: PM
- Panel: owner-directed; grounded in measured token ratios on the arm_map fixture (144 records) and the observed raw-output share of committed benchmark bytes.
- Context: ADR 0023 retains a bounded on-main TEXT sample of raw graded output but is silent on everything outside it, and on the format of the structured artifacts around it (arm maps, bid tables, per-cell scores). Measured ratios (arm_map, 144 records; pretty-json 1.00x baseline; min-json/csv re-measured 2026-07-09): min-json 0.86x, yaml-block 0.80x, tabular/TOON 0.54x, tsv/csv 0.46x. Text-heavy records (a prose evidence field, e.g. `graded/items/`) measure ~0.92x-0.98x regardless of format — evidence text dominates. Separately, raw model outputs are ~63% of a benchmark's committed bytes (irreducible audit text, scales with corpus size) — a record-format change doesn't touch that share.

## Decision
1. **Amend ADR 0023 raw retention: documented sample + one gzip archive.** The deterministic on-main sample (planted-defect set + boundary-straddling cells, `sample_rule` recorded in `metadata.json` per ADR 0023) stays plain text, readable without tooling. Everything outside the sample is no longer silently discarded — gzip-archived into a single `raw.tar.gz` per benchmark (stdlib `tarfile` + `gzip`, no per-file archives). Keeps the audit-critical subset eyeball-readable while bounding the raw text that dominates a benchmark's footprint.
2. **Benchmark-artifact-format convention** (the structured records around the sample, not the sample text):
   - FLAT/scalar record tables (arm maps, bid tables, per-cell scores — identically-shaped rows) -> **CSV** (measured 0.45x; == TSV in size for scalar records). Flatten nested values into columns (a CI list -> `ci_lo`/`ci_hi`) so no field ever needs quoting.
   - TEXT-heavy records (a prose `evidence` field, e.g. verdicts) -> **minified JSONL**, one record per line — NOT CSV. On the verdicts file CSV is only 0.95x of JSONL, but 144/144 rows need quoting and 3 carry embedded newlines that break naive parsers; the ~5% saving isn't worth the fragility. JSONL also wins on diffability and no-parser append.
   - Human-read config/metadata (small counts, must stay eyeball-editable — `metadata.json`, run config) -> small **JSON or YAML**; negligible byte cost at this size, readability wins.
   - Gitignore derivable intermediates: `prompts/`, `cells.tsv`, `meta.json` (when regenerable), `graded/items/`, `graded/bids.json`, `__pycache__`, `outputs/*.err` — regenerate, don't commit.
3. **Scope boundary.** Governs STORED and agent-read benchmark artifacts — files an aggregation script or auditing agent opens on demand. Does NOT touch always-loaded context (SKILL.md, CLAUDE.md, agent prompts) — stays char-budget governed (ADR 0008/0009), a different cost model: paid every invocation, not only when opened.

## Justification
No single format fits both record shapes: flat records span 2x+ (1.00x pretty-json to 0.45x CSV), but on prose records the cheaper CSV needs per-row quoting and breaks on embedded newlines for a mere ~5%. Raw retention is the dominant byte cost (~63%), format-agnostic free text — so there the fix is compression plus a bounded readable sample (ADR 0023), not a record-format change.

## Assumptions
- [checkable] the load-bearing ratios reproduce on the committed arm_map fixture (144 records) — owner: gate; result: verified, partial, 2026-07-09 (csv 0.46x, min-json 0.86x — basis holds; rejected formats not re-derived).
- [verified] raw model outputs are the majority (~63%) share of a benchmark's committed bytes, grounding gzip-the-rest over a record-format fix.
- [unverifiable] a cell ever needed for audit isn't stuck behind the gzip archive because `sample_rule` missed it — REOPEN-IF a needed cell must be pulled from `raw.tar.gz` rather than the plain-text sample; then widen `sample_rule` (ADR 0023) instead of decompressing ad hoc.

## Rejected alternatives
- **YAML for records** — measured 0.80x, roughly tied with min-json (0.82x); a second format to tool against for no real gain over one minified-JSONL convention.
- **One-format-fits-all** — ignores the spread: pretty JSON overpays 2x+ on flat records; CSV on text-heavy records buys ~5% while forcing per-row quoting and breaking on embedded newlines.
- **Full raw retention, no gzip** — the gap ADR 0023 left open; raw text is the dominant byte share, unbounded with corpus size.
- **Per-cell gzip instead of one archive** — many small archives add per-file overhead, complicate a single-pass completeness check; one `raw.tar.gz` per benchmark matches the one-`sample_rule`-per-benchmark grain.

## Revisit triggers
- The measured ratios shift materially on a differently-shaped benchmark (e.g. wide free-text columns in what were flat records) -> re-measure, adjust the format assignment.
- A needed audit cell isn't recoverable from `raw.tar.gz` -> reopen `sample_rule` (ADR 0023), don't hand-decompress as a workaround.
