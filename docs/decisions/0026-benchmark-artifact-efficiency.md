---
id: 0026
title: "Benchmark artifact format: measured-ratio convention + sampled-plus-gzip raw retention"
status: accepted
tier: lite
summary: "Measured ratios (144 records; pretty-json baseline) show flat records compress hard under CSV (0.45x) while text-heavy records barely move (0.92x-0.98x). Sets the artifact-format convention (CSV for flat records, minified JSONL for text-heavy, small JSON/YAML for config) and amends ADR 0023's raw retention: the on-main sample stays plain text, everything else gzip-archived per benchmark. Governs stored/agent-read artifacts only."
---

# 0026 — benchmark artifact format: measured-ratio convention + sampled-plus-gzip raw retention

- Decision: amends ADR 0023's raw retention — the on-main sample stays plain text; everything
  outside it is gzip-archived into one `raw.tar.gz` per benchmark, not discarded. Format
  convention: flat/scalar record tables -> CSV, nested values flattened into columns; text-heavy
  records -> minified JSONL, one per line, never CSV (newline fragility); config/metadata -> small
  JSON/YAML; derivable intermediates -> gitignored. Scope: stored/agent-read artifacts only —
  always-loaded context stays char-budget governed (ADR 0008/0009).
- Why: measured ratios on a 144-record fixture show flat records compress hard by format (1.00x
  pretty-json -> 0.45x CSV) while text-heavy records barely move (0.92x-0.98x) — no single format
  fits both. Raw output is ~63% of committed bytes — compression + a bounded sample fixes that.
- Rejected: YAML for records (no gain over JSONL); one-format-fits-all (overpays on flat records,
  or breaks on text newlines); full raw retention with no gzip; per-cell gzip instead of one file.
- Reopen-if: ratios shift materially on a differently-shaped benchmark -> re-measure.
- Enforced: `benchmarks/README.md`; `sample_rule` in each benchmark's `metadata.json` —
  reviewer-checked, no gate script.
