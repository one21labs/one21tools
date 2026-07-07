# Toolkit benchmark grid — verdicts (v2 eval sets)

432 executor runs (4 skills x 3 executor models x 6 evals x 2 configs x 3 replicates),
144 independent grading cells, 0 agent errors. Executors: haiku / sonnet / opus; graders:
session model (fresh, different from every executor). Paired per (eval, replicate).
Verdicts computed with the PR #24 (non-tied-pairs warning) version of eval_verdict.py.

## Verdict matrix — mean pass-rate delta per 1k chars of SKILL.md body

| Skill (body chars) | haiku | sonnet | opus |
|---|---|---|---|
| code-standards (5,890) | +0.0341 (8W-2L-8T) | +0.0597 (12W-0L-6T) | +0.0451 (13W-0L-5T) |
| engineering-principles (5,464) | +0.0263 (11W-4L-3T) | +0.0358 (10W-2L-6T) | +0.0235 (9W-0L-9T) |
| building-skills (5,597) | **+0.0853** (16W-0L-0T) | +0.0686 (14W-0L-4T) | +0.0768 (17W-0L-1T) |
| optimizing-context (5,243) | +0.0286 (11W-0L-7T) | +0.0148 (8W-1L-9T) | +0.0197 (6W-1L-11T) [WARN small-n: 7 non-ties] |

Totals across 214 pairs: **135 wins, 10 losses, 69 ties.** All 12 cells positive.

## Headlines

1. **Every skill now measurably earns its context cost on every model.** The v1 pilot's
   negative code-standards verdict (-0.0035) was an eval artifact, not a skill property:
   with discriminating tests the same skill scores +0.034..+0.060.
2. **building-skills is the highest value-density skill** (47W-0L-5T across models) —
   its content (trigger-first descriptions, conciseness discipline, frontmatter rules)
   is exactly what no model does by default.
3. **Value is model-dependent in the expected direction for optimizing-context**: opus
   ties 11/18 (it already routes context reasonably); haiku gains most. code-standards
   inverts: pressure cases (e4-e6) are where sonnet/opus gain — under pressure even strong
   models drop the checks unless the skill holds them.
4. **Pressure cases carry the signal**: across skills, the pressure evals (cs e4/e5,
   ep e5/e6, bs e4/e6) show the largest deltas — the skills' real value is resisting
   rationalization, which is what v1 could not see.

## Iteration flags (per-eval deltas)

- code-standards e2 (review) & e3 (logging): near-zero on sonnet/opus — still too easy
  for strong models; harden or accept as haiku-only signal.
- engineering-principles e2 (docs SSoT) & e4 (sunk cost): NEGATIVE/zero on haiku — the
  skill sometimes pushes haiku to over-cut / misapply; loophole-close in skill text or
  simplify the principle statement.
- optimizing-context e3 (fact routing): zero discrimination on all three models — rewrite.

## Caveats (stated so the numbers stay honest)

- Replicates within an eval are correlated; the Wilson CIs treat 18 pairs as independent,
  so intervals are modestly optimistic. Eval-level sign tests still favor the skill in
  every cell with >=4 winning evals (e.g. code-standards/sonnet: 4 evals win, 2 tie, 0 lose).
- Run-time token cost was not captured in the grid (executor tokens unavailable inside the
  workflow); the pilot measured +2,930 tokens/run on sonnet for code-standards.
- 2 of 432 runs (building-skills/haiku) produced no outputs and were dropped from pairing.
- Both arms carried the repo's ambient CLAUDE.md (equal exposure; paired design cancels it).
- Grader model != executor models everywhere (fresh grader discipline), but grader bias
  is shared across arms within each pair.

## Raw data

Session workspace: grid/<skill>/<model>/benchmark.{json,md} + per-run grading.json,
outputs, timing. 18.2M subagent tokens total.
