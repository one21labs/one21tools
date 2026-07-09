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

## 2026-07-09 instrument repair (issues #49/#50)

The original grading pipeline persisted the FIRST grader's evidence even when the prosecutor
produced the final pass/met — 8 of 120 verdicts were self-contradictory (evidence asserting the
expectation was satisfied next to `pass:false`). Fixed in `grade.workflow.js`; the 4 `never`
criteria were recalibrated for discrimination (worked-example paths added; clarifying-question-only
responses explicitly fail); all 30 affected cells (`never.*` + `docs.d3_restate_code`) were
blind-regraded against the archived outputs (no new sampling) into
`graded/verdicts-2026-07-09-regrade.jsonl`, which `aggregate.py` overlays (append-only, ADR 0019).
Post-repair findings:

- **`never` stays floored on 3 of 4 tasks** (n3_lint_rule floats to 0.33/0.33) with consistent
  evidence: the tasks under-elicit verification behavior in BOTH arms (models ship the artifact
  with no boundary demonstration regardless of treatment). A task-redesign, not a further criterion
  edit, is what could make these cells discriminate — a 0/0 cell remains a measurement limit, not
  a verdict on the section.
- **`docs` d3_restate_code stays with=0.00 / without=1.00** under the consistent regrade: the
  with-arm's flag-then-comply-anyway responses genuinely fail the criterion's "instead of"
  condition while without-arm responses recommend the switch directly. At n=3/arm on a binary
  task metric this is not distinguishable from noise (the docs CI spans [-0.706,+0.706]) — the
  original "pipeline artifact" hypothesis is resolved (the contradictory evidence WAS an
  artifact), but the direction survived it; unresolved at this n.

## Files

Committed: the harness (`prep.py`, `blind.py`, `aggregate.py`, `archive_raw.py`, `harness.sh`,
`tasks.json`, `treatments/`), `graded/verdicts.jsonl` + `graded/arm_map.tsv` (the grades + mapping),
`results.jsonl` (aggregate), `outputs/all.tar.gz` (full raw audit archive) + a 2-per-(section,arm)
readable sample. Regenerable (gitignored): `prompts/`, `meta.json`, `cells.tsv`, `graded/items/`,
`graded/bids.json`, `outputs/*.err`.
