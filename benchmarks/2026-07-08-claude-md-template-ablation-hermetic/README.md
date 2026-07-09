# Hermetic ablation: CLAUDE.md-template "Feedback = PDCA trigger" section

The first **hermetic** with/without ablation in this repo (ADR 0023) — the re-run that turns the
earlier CONFOUNDED NULL (`../2026-07-08-claude-md-template-ablation/`) into a real verdict. Answers:
**does the `Feedback = PDCA trigger` section of `claude-md-template.md` earn its always-loaded cost?**

## Verdict: KEEP (+0.375, 95% CI [+0.12, +0.64])
Under a neutral executor framing the section improves judgment-call flagging from **0.33 -> 0.71**
(5 wins / 0 losses / 3 ties across 8 tasks). The CI excludes zero. The section earns its keep.

## What is measured
Each task is a realistic dev request with an embedded **judgment call** (a threshold/scope/policy
choice reasonable engineers decide differently). `treatment.txt` = the section verbatim; `tasks.json`
= the 8 requests (SSoT). Metric: **PASS** = the response surfaces the judgment call as a decision to
make; **FAIL** = it delivers a settled implementation of a self-chosen value. Graded blind (arm
withheld) by fresh subagents, each PASS re-checked by an adversarial prosecutor (`grade.workflow.js`).

## Hermetic executor (the fix, ADR 0023)
The in-harness POC leaked the treatment into the control arm on three vectors; each is closed here
(`harness.sh`): (1) **external cwd** so no project CLAUDE.md walks into context; (2) **Skill/Task +
Read/Grep/Glob/Bash/Edit/Write denied** so no plugin-skill fires and no repo file is read; (3) **user
`~/.claude/CLAUDE.md` relocated** for the run (it loads regardless of cwd/CONFIG_DIR/HOME) with a
trap-restore. The ONLY between-arm difference is `--append-system-prompt` with the section. A fresh
cloud instance needs only (1)+(2) — (3) is a no-op there.

## The finding: prose ablation is executor-framing-sensitive
It took 3 iterations, and the reason is the real lesson. The SAME section measured:

| iter | executor framing | mean delta | verdict |
|------|------------------|-----------|---------|
| 1 | tool-denied, no neutralizer | +0.167 (CI [-0.20,+0.53]) | INCONCLUSIVE — baseline saturated HIGH (executor fixated on missing tools, asked in both arms) |
| 2 | "give your best complete response, don't ask" | 0.000 (CI [-0.12,+0.12]) | CUT-CANDIDATE — baseline saturated LOW (framing over-corrected toward implementing) |
| 3 | neutral ("respond in plain text") | **+0.375 (CI [+0.12,+0.64])** | **KEEP** |

iter1 and iter2 were framing confounds pushing opposite directions; only the **neutral** framing
(iter3) isolates the treatment. Discipline for ablating any always-loaded prose: hold the executor's
base framing neutral, or it swamps the section. (Per-iteration data in `results_iter{1,2,3}.jsonl`;
grades + evidence quotes in `graded_iter{1,2,3}/verdicts.json`; iter3 raw outputs retained in
`outputs_iter3/` as the KEEP verdict's audit evidence.)

## Re-run
`bash harness.sh` (env: `HERMETIC_RELOCATE_USER_MEMORY=1`, `MODEL`, `REPS`, `MAXJ`) -> `python
blind.py` -> `Workflow(grade.workflow.js)` -> `python aggregate.py`. Append-only per ADR 0019.

## Reusable instrument
The hermetic-executor recipe is the novel, worth-owning slice; the verdict math duplicates
`skills/building-skills/scripts/eval_verdict.py` (consolidate, don't ship `aggregate.py` long-term).
Promoting this into `building-skills` vs. routing hermetic execution upstream to skill-creator is an
ADR-0013 (delegation) judgment call -> `/decide` before extraction.
