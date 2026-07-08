# CLAUDE.md-template ablation harness

Ablation-tests an **always-loaded doc** the way ADR 0019's Tier 2 ablates a SKILL.md section —
applied here to `pdca-workflow/skills/pdca-init/references/claude-md-template.md` (and, by the same
method, any repo `CLAUDE.md`). Answers: **does an always-loaded section earn its per-request cost?**

## Method (OFAT)
1. Two variants of the doc, identical except the one section under test (with / without).
2. N tasks the section is meant to influence (here: judgment-call requests the `Feedback = PDCA
   trigger` section should make the agent flag/plan rather than fix directly).
3. Paired executors per (task x arm x replicate); a fresh grader scores each output **blind to the
   arm** against the task's assertion; aggregate with the eval-clustered Wilson CI (`eval_verdict`).
4. **Keep/cut bar** (same as Tier 2): a section whose removal moves the delta **less than the CI
   width** does not earn its always-loaded cost -> cut, or relocate to a cheaper enforcing layer
   (a gate/script). A section whose absence measurably drops the delta stays.

This is the **verify step of the retrospect -> PDCA loop**: `/retrospect` proposes adding or cutting
an always-loaded line; `/decide`'s verify runs this ablation; the bar decides. Add-what-recurs
(retrospect) / cut-what-doesn't (ablation).

## HERMETIC EXECUTOR — required, and the reason this POC's result is not a verdict
The control ("without") arm must be unable to reach the treatment. **This POC failed that**, run via
in-harness subagents in this repo's own environment:
- `2026-07-08-ep-loophole-oos-retest`: **6/9** control executors read `skills/engineering-principles/`
  or invoked the installed `engineering-skills:engineering-principles` skill.
- `2026-07-08-claude-md-template-ablation`: control executors invoked `pdca-workflow:advise` / read
  repo files.

The baseline was therefore not treatment-free, so **both runs returned delta 0 (CONFOUNDED NULL) —
that is a harness-environment artifact, NOT evidence the content is valueless.** Same confound class
as `benchmarks/2026-07-07-toolkit-grid/trigger-kit/FINDINGS.md` (nested sessions inherit installed
skills), now confirmed for the benefit-benchmark, not just triggering.

A valid run needs an executor with **no repo/skill file access and no installed plugins** — only the
injected doc text in the with arm. Until then, the mechanics are proven (fan-out + blind grade +
eval-clustered CI ran with 0 agent errors) but no keep/cut verdict can be trusted.

## Re-run
`Workflow({ scriptPath: "harness.workflow.js" })` after making the executor hermetic (fresh env /
plugins disabled). Snapshots are append-only JSONL per ADR 0019.
