# Skills hermetic benefit-benchmark — 2026-07-08

Does each toolkit SKILL.md measurably beat its no-skill baseline, measured hermetically (control arm
cannot leak the treatment)? Verdict methodology: ADR 0019 (clustered CI), ADR 0023 (hermetic executor
+ auditable raw), ADR 0024 (cost-justification loop), ADR 0025 (fraction-met headline metric).

## Verdict

**OVERALL: KEEP.** The four skills collectively beat their no-skill baseline: mean per-eval delta
**+0.088, 95% CI [+0.019, +0.156]** (excludes 0) on the fraction-met metric. The skills justify their
cost in aggregate.

**Per-skill: none individually clears the bar at n=6 evals** — a statistical-power limit (wide CIs),
not a clean null. Ranked by marginal benefit:

| Skill | mean delta (frac-met) | 95% CI | verdict | binary (secondary) |
|---|---|---|---|---|
| building-skills | +0.156 | [-0.007, +0.318] | INCONCLUSIVE (edge touches 0) | +0.056 |
| optimizing-context | +0.107 | [-0.038, +0.253] | INCONCLUSIVE | +0.222 |
| code-standards | +0.067 | [-0.084, +0.217] | INCONCLUSIVE | -0.056 |
| engineering-principles | +0.020 | [-0.066, +0.107] | CUT-CANDIDATE (flat) | -0.056 |
| **OVERALL** | **+0.088** | **[+0.019, +0.156]** | **KEEP** | +0.042 |

## Why fraction-met, not binary pass (ADR 0025)

The binary "all expectations met + survive a prosecutor" metric **floored**: only 21/144 cells passed;
most evals scored 0/0 in BOTH arms, so they carried no discriminating signal, and every skill fired the
<4-non-tied width warning. That is the underpowered-measurement case ADR 0024 says does not count as a
valid iteration. The continuous fraction-met (met/total of each eval's expectations) is the powered
measure: it sees a skill move a cell 2/5 -> 4/5 that the binary metric cannot. On fraction-met the
overall effect is significant and positive. Floor evidence: without-arm mean fraction 0.544 (12% all-met)
vs with-arm 0.619 (17% all-met); complete failures drop 7% -> 3% with the skill.

The prosecutor safeguard (ADR 0025) was applied UNIFORMLY to every cell's met-count, not just to the 21
binary passes; met_final = min(grader_met, prosecutor_met). It reduced credit on 13 cells and **raised**
the overall delta (+0.075 -> +0.088) by shaving the baseline's inflated partial credit hardest — the
result is robust to adversarial scrutiny, not an artifact of a lenient grader.

## Method (hermetic executor — the control arm cannot leak the treatment)

- **Executor:** `claude -p` (model sonnet, CLAUDE_EFFORT=medium), run from an EXTERNAL empty cwd (no
  project CLAUDE.md), with Skill/Task/Read/Grep/Glob/Bash/Edit/Write/WebFetch/WebSearch/NotebookEdit
  denied (no plugin-skill invocation, no repo access), and the user `~/.claude/CLAUDE.md` relocated for
  the run (trap-restore). NEUTRAL base framing (ADR 0024: prose ablation is framing-sensitive).
- **Only between-arm difference:** the `with` arm gets `--append-system-prompt` = the SKILL.md BODY
  (`treatments/<skill>.txt`, frontmatter stripped); `without` gets only the neutral framing.
- **Grid:** 4 skills x 6 evals x {with, without} x 3 reps = 144 cells. Prompts are each skill's live
  `evals/evals.json`, verbatim.
- **Grading:** blind (arm withheld from the grader; `graded/items/<bid>.json` = prompt + expectations +
  response only). Each expectation judged MET/NOT-MET; then a uniform adversarial prosecutor re-count.
- **Aggregation:** per (skill, eval, arm) mean fraction-met; per-eval delta with-without; per-skill mean
  + 95% CI clustered over the skill's 6 evals (ADR 0019). KEEP if CI excludes 0 and is positive.

## Reproduce / audit

```
python prep.py                                   # treatments/, prompts/, cells.tsv, meta.json from live skills
HERMETIC_RELOCATE_USER_MEMORY=1 bash harness.sh  # 144 cells -> outputs/
python blind.py                                  # outputs/ -> graded/items/ (arm withheld) + arm_map.json
# Workflow grade.workflow.js  {itemsDir, bids}   -> graded/verdicts.json (blind grade + prosecute passes)
# Workflow prosecute_counts.workflow.js {...}     -> uniform adversarial met-counts (ADR 0025 safeguard)
python aggregate.py                              # -> results.jsonl + the tables above
```

`outputs/*.txt` are the raw model responses (the on-main auditable sample, ADR 0023 — git self-verifies).
`graded/verdicts.json` holds the (non-derivable) LLM judgments; everything else regenerates from the
scripts. `graded/items/`, `graded/bids.json`, `outputs/*.err` are regenerable and git-ignored.

## Next (per-skill power — the plan, per ADR 0024)

Per-skill significance is blocked by **too few discriminating evals** (n=6 -> CIs ~±0.15 wide). The
binding lever is eval COUNT, not reps (between-eval variance dominates the clustered CI). To prove any
single skill: expand its discriminating eval set (raises clustering n -> tighter CI). engineering-principles
is the one to scrutinize first — flat (+0.020) with 3 of 6 evals tied and one loss; either its evals are
non-discriminating or its single-shot marginal value is genuinely low. Framing must stay NEUTRAL.
