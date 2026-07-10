# 2026-07-09 description ablation (issue #30)

A/B trigger test of each skill's always-loaded frontmatter description: current text (control)
vs a trimmed variant, 16 queries per skill (8 should-fire + 8 adjacent should-not-fire) from
`benchmarks/2026-07-07-toolkit-grid/trigger-kit/`, run serially on the patched skill-creator
runner (protocol + validity rules: `skills/building-skills/references/description-ablation.md`,
ADR 0033; run parameters: `metadata.json`).

Result: all four trims hold or improve TP at 0 FP (`results.jsonl`); the four flipped queries,
escalated to 3 reps, all resolved in the variant's favor or as ties. Verdict: adopt — landed in
`skills/*/SKILL.md` in this PR. Raw per-query records: `results/*.json` (complete, unsampled).

Character savings (always-loaded bytes): building-skills 271 -> 121, code-standards 196 -> 146,
engineering-principles 334 -> 264, optimizing-context 348 -> 161 — 457 chars (~40%) off every
request's context.
