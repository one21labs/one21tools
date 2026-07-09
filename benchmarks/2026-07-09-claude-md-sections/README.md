# CLAUDE.md sections ablation (hermetic)

Does each always-loaded CLAUDE.md **section** earn its context cost? Hermetic with-vs-without
(ADR 0023), 5 sections x 4 tasks x 3 reps. Each task graded against its SINGLE `pass_criterion`
(binary, ADR 0019) by a blind Sonnet grader + adversarial prosecutor on each PASS. Per-task
delta = mean(pass WITH) - mean(pass WITHOUT); per-section headline = mean per-task delta with a
95% CI clustered over the section's tasks (each task = one observation). KEEP if the CI excludes 0
and is positive (ADR 0024).

## Verdict

| Section | mean delta | 95% CI | W/L/T | Verdict |
|---|---|---|---|---|
| shipping | +0.833 | [+0.507, +1.160] | 4/0/0 | **KEEP** |
| review-panels | +0.167 | [-0.022, +0.355] | 2/0/2 | INCONCLUSIVE |
| conventions | +0.250 | [-0.240, +0.740] | 1/0/3 | INCONCLUSIVE |
| docs | -0.000 | [-0.706, +0.706] | 2/1/1 | CUT-CANDIDATE |
| never | +0.000 | [0, 0] | 0/0/4 | CUT-CANDIDATE |
| **OVERALL** | **+0.250** | **[+0.033, +0.467]** | | **KEEP** |

**Overall the sections beat their no-treatment baseline** (CI excludes 0); `shipping` carries it
cleanly. Per-section power is low (n=4 tasks -> wide CIs); only `shipping` clears the per-section
bar. The underpowered INCONCLUSIVE sections are a power limit, not evidence of no effect.

## Regrade overlay

`graded/verdicts-2026-07-09-regrade.jsonl` supersedes the original verdicts for the 30 `never.*` +
`docs.d3_restate_code` cells (recalibrated `never` criteria in `tasks.json`; final verdicts carry
the evidence of whichever judgment produced them); `aggregate.py` applies it append-only (ADR 0019).
Current state:

- **`never` is floored on 3 of 4 tasks** (n3_lint_rule at 0.33/0.33) with consistent evidence: the
  tasks under-elicit verification behavior in BOTH arms. Task redesign, not a further criterion
  edit, is the remaining lever — a 0/0 cell is a measurement limit, not a verdict on the section.
- **`docs` d3_restate_code is with=0.00 / without=1.00** under consistent grading: with-arm
  flag-then-comply-anyway responses fail the criterion's "instead of" condition. At n=3/arm on a
  binary metric this is indistinguishable from noise (docs CI [-0.706,+0.706]) — unresolved at
  this n, not evidence the section hurts.

## Files

Committed: the harness (`prep.py`, `blind.py`, `aggregate.py`, `archive_raw.py`, `harness.sh`,
`tasks.json`, `treatments/`), `graded/verdicts.jsonl` + `graded/arm_map.tsv` (the grades + mapping),
`results.jsonl` (aggregate), `outputs/all.tar.gz` (full raw audit archive) + a 2-per-(section,arm)
readable sample. Regenerable (gitignored): `prompts/`, `meta.json`, `cells.tsv`, `graded/items/`,
`graded/bids.json`, `outputs/*.err`.
