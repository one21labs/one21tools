# EP loophole out-of-sample hermetic retest — prep (2026-07-10)

Issue #31 item 5: does the `engineering-principles` loophole fix (PR #27) generalize to fresh
SSoT / waste scenarios, measured with a hermetic executor? **Supersedes**
`benchmarks/2026-07-08-ep-loophole-oos-retest` as the item-5 answer: that run recorded
`hermetic: false` / `result_status: CONFOUNDED NULL` (its `metadata.json` — control-arm executors
had repo/skill Read access and installed-plugin access and read the treatment). Per ADR 0023
decision 1, "a non-hermetic run is RECORDED (`hermetic: false`) as a confounded null and is never
a verdict" — that run's delta=0 is not evidence the fix has no effect, it is unmeasured. This
directory is PREP ONLY: no `claude` calls have been executed. Run parameters live in
`metadata.json`; per-eval numbers will live in `results.jsonl` once run.

## OOS eval set (3 tasks, extracted verbatim from the confounded run's harness)

Source: `benchmarks/2026-07-08-ep-loophole-oos-retest/harness.workflow.js`
(`ep-loophole-oos-retest-wf_394e9703-cf3.js`), `TASKS` array — identical prompts/assertions, only
the executor changes.

| id | area | gist |
|----|------|------|
| 1 | ssot | "Just set v4 in docs/config/route-prefix to match and ship" — must flag the 3-way duplication as the real problem (one home), not endorse copy-to-match. |
| 2 | sunk-cost | "Our custom cache is slower than stdlib but we already invested 2 sprints, keep it?" — must reject sunk cost, recommend the faster stdlib option on current merits. |
| 3 | premature-abstraction | "One exporter today, build a generic plugin framework now for the future" — must name this premature abstraction / speculative generality, not endorse building it now. |

## Method (hermetic executor, this machine's verified-today WSL recipe)

- **Executor:** `claude -p` (model sonnet, `CLAUDE_EFFORT=medium`), run inside **WSL Debian** with
  `CLAUDE_CONFIG_DIR=$HOME/issue30/claude-config` (a clean config dir holding credentials only —
  no project/skill state to leak into the control arm), from an **empty WSL-native scratch cwd
  outside any repo** (a Windows-side external cwd can still leak a project `CLAUDE.md` via cwd
  traversal up an ancestor path; a WSL scratch dir has no repo ancestor), `PATH` prepended with
  `$HOME/.local/bin`, and `Skill Task Read Grep Glob Bash Edit Write WebFetch WebSearch
  NotebookEdit` denied (`--disallowedTools`). Prompt via **stdin** (the variadic
  `--disallowedTools` is last, so it can't eat the prompt). This supersedes the git-bash /
  Windows-external-cwd recipe `2026-07-08-skills-hermetic` and `2026-07-09-ep-remeasure-hermetic`
  used — same tool-deny list and stdin-prompt discipline, tighter cwd/config isolation.
- **Only between-arm difference:** the `with` arm gets `--append-system-prompt` = the **current**
  `engineering-principles` SKILL.md body (frontmatter stripped) + `references/ssot-enforcement.md`
  + `references/waste-identification.md`, filename-headered — the two refs matching this eval
  set's loophole areas (the original confounded harness's `WITH_PREFIX` used the identical two
  refs). `without` gets only the neutral base framing. Construction pattern (body + named refs,
  filename-headered) follows `2026-07-09-ep-remeasure-hermetic/prep.py`'s `treatment()`.
- **Grid:** 3 evals x {with, without} x 3 reps = 18 cells, arms **interleaved per rep** in
  submission order (without-rep-N immediately followed by with-rep-N) rather than run as separate
  per-arm blocks, to pair each rep's arms against similar temporal/load conditions.
- **Grading:** `grade.workflow.js` + `prosecute_counts.workflow.js` in this dir — near-verbatim
  reuse of `2026-07-08-skills-hermetic`'s (generic over any blinded items dir; no arm-count
  dependence). Blind (arm withheld from the grader). `met_final = min(grader_met,
  prosecutor_met)` per cell (ADR 0025).
- **Aggregation:** per-eval delta = mean fraction-met WITH minus WITHOUT (one clustered
  observation per eval, ADR 0019); headline = mean delta + 95% CI across the 3 evals, verdict via
  the shared `benchmarks/lib/verdict.py:verdict_of` rule (ADR 0024/0026). **n=3 evals is smaller
  than the n=6 grid that rule was calibrated against** — a straddling CI here is an underpowered
  measurement, not a clean null; `aggregate.py` reports both the verdict and that caveat.

## Deviations from the ep-remeasure-hermetic template

- 2 arms (`without`/`with`), not 3 — this is a single-skill, single-version retest (does the
  MERGED fix generalize), not an old-vs-new improvement comparison.
- Executor moved from git-bash-on-Windows external cwd to WSL Debian with a dedicated
  `CLAUDE_CONFIG_DIR`, replacing the `~/.claude/CLAUDE.md` relocate-and-trap-restore dance (the
  clean config dir makes relocation unnecessary — there is nothing in it to leak).
  `harness.sh` therefore has no relocate/restore trap.
- `harness.sh` gained a `DRYRUN=1` mode (list cells + would-run commands, no `claude` calls) for
  validating the grid shape without spending a run — added because this prep must be validated
  without executing any `claude` calls.
- `metadata.json` carries an ADR 0023 `sample_rule` (schema per
  `skills/building-skills/scripts/eval_verdict.py --check-audit-sample`) with `population: []`
  pending the run — population is 18 deterministic filenames, appended post-run before commit.

## Reproduce (post-run steps; none of this has been executed yet)

```bash
# Prep already run (this session, no claude calls): treatments/, prompts/, cells.tsv, meta.json
python prep.py

# Inside WSL Debian, from this directory:
DRYRUN=1 bash harness.sh                          # validate: lists all 18 cells, no claude calls
CLAUDE_CONFIG_DIR=$HOME/issue30/claude-config bash harness.sh   # 18 cells -> outputs/

python blind.py                                   # outputs/ -> graded/items/ (arm withheld) + arm_map.tsv
# Workflow grade.workflow.js             {itemsDir, bids} -> graded/verdicts.jsonl
# Workflow prosecute_counts.workflow.js  {itemsDir, bids} -> graded/prosecute_counts.jsonl
python aggregate.py                                # -> results.jsonl + verdict

# Then: append sample_rule.population to metadata.json (18 {file,eval_id,arm} entries from
# outputs/*.txt) and commit outputs/*.txt as the on-main auditable raw sample (ADR 0023).
```

## Launch command (exact, for the WSL session)

```bash
cd <repo-checkout-in-WSL>/benchmarks/2026-07-10-ep-loophole-oos-hermetic
export CLAUDE_CONFIG_DIR="$HOME/issue30/claude-config"
export PATH="$HOME/.local/bin:$PATH"
bash harness.sh
```
