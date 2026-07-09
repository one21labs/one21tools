# 2026-07-09 three-skills re-measure — VERDICT: MERGE x3 (all weak-confidence)

Issue #55: hermetic re-measure of the `skills-improve-55` draft (76a67bf) vs main for
code-standards, building-skills, optimizing-context — ADR 0024 improvement-loop iteration 1 for
each. Arm design, merge bar, and cost accounting follow **ADR 0027** (generalized per skill; the
touched-reference set is derived and asserted from the draft's diff per issue #63). Run parameters:
`metadata.json`; per-eval numbers: `results.jsonl`.

## Result (fraction-met, met_final = min(grader, prosecutor), ADR 0025)

| Skill | d_old | d_new | diff (new-old) | body chars | Verdict |
|---|---|---|---|---|---|
| optimizing-context | +0.128 [+0.051,+0.204] | +0.269 [+0.123,+0.414] | +0.141 [-0.047,+0.328] | 5405 -> 5101 | **MERGE** (weak) |
| code-standards | +0.113 [-0.027,+0.253] | +0.163 [+0.044,+0.282] | +0.050 [-0.138,+0.238] | 5890 -> 5877 | **MERGE** (weak) |
| building-skills | +0.204 [+0.104,+0.304] | +0.213 [+0.068,+0.357] | +0.009 [-0.056,+0.075] | 5597 -> 5736 | **MERGE** (weak, marginal) |

- **optimizing-context** is the clean win: eval 6 moved 0.17 -> 0.78 exactly as diagnosed (the
  "keep everything" reorganization cell); d_new's CI excludes 0; always-loaded body -304 chars.
- **code-standards**: eval 5 floated 0.00 -> 0.40 and eval 3's loss flipped (+0.28), both as
  targeted; d_new's CI excludes 0 (d_old's did not). **Iteration-2 flag:** eval 1's advantage
  shrank (diff -0.33) — plausibly the File Headers examples cut; watch that cell before any
  further trim there.
- **building-skills**: eval 4 improved as targeted (diff +0.17) but the skill-level diff (+0.009)
  is indistinguishable from zero and the body GREW 139 chars. Merged strictly because the
  pre-registered bar is directional (`mean(diff) > 0`); recorded as marginal — iteration 2 should
  either land a larger effect or revert the paragraph.
- Validity: both previously-INCONCLUSIVE old skills now clear KEEP in-run (d_old CIs exclude 0 for
  building-skills and optimizing-context) — the instrument reproduces and sharpens with 3 arms.

## Reproduce

```bash
python prep.py                                   # treatments (old=checkout, new=git show 76a67bf), prompts, cells, meta; asserts touched sets
HERMETIC_RELOCATE_USER_MEMORY=1 bash harness.sh  # 162 cells -> outputs/   (verify ~/.claude/CLAUDE.md symlink after)
python blind.py                                  # outputs/ -> graded/items (arm withheld) + arm_map.tsv
# Workflow ../2026-07-08-skills-hermetic/grade.workflow.js            {itemsDir, bids} -> graded/verdicts.jsonl
# Workflow ../2026-07-08-skills-hermetic/prosecute_counts.workflow.js {itemsDir, bids} -> graded/prosecute_counts.jsonl
#   (persist per benchmarks/lib/README.md: task .output "result" field; prosecutor evidence overrides)
python aggregate.py                              # -> results.jsonl + per-skill verdicts
python archive_raw.py                            # once: outputs/all.tar.gz + per-(skill,arm) sample
```
