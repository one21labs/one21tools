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
cleanly. Two per-section flags are diagnosis targets for the improvement loop, NOT clean cuts:

- **`never` scores 0.00 in both arms on all 4 tasks** - nobody passes with or without. That points
  at **mis-calibrated evals** (pass_criterion too strict), not a dead section. Measurement-fix
  candidate before any cut.
- **`docs` d3_restate_code** is with=0.00 / without=1.00 - the section arm did *worse* on one task.
  Possible spurious negative (cf. #27); read the transcripts before concluding.

Per-section power is low (n=4 tasks -> wide CIs); only `shipping` clears the per-section bar. The
underpowered INCONCLUSIVE sections are a power limit, not evidence of no effect.

## Files

Committed: the harness (`prep.py`, `blind.py`, `aggregate.py`, `archive_raw.py`, `harness.sh`,
`tasks.json`, `treatments/`), `graded/verdicts.jsonl` + `graded/arm_map.tsv` (the grades + mapping),
`results.jsonl` (aggregate), `outputs/all.tar.gz` (full raw audit archive) + a 2-per-(section,arm)
readable sample. Regenerable (gitignored): `prompts/`, `meta.json`, `cells.tsv`, `graded/items/`,
`graded/bids.json`, `outputs/*.err`.
