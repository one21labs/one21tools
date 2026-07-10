# 2026-07-10 description ablation — VERDICT: KEEP trims for code-standards (-67 chars), building-skills (-129), engineering-principles (-118); NULL for optimizing-context (keep current)

Issue #30: trim each skill's always-loaded frontmatter `description:` and verify with a trigger
A/B that the trim holds true-positives and does not raise false-positives. Query sets and
critical caveats: `../2026-07-07-toolkit-grid/trigger-kit/` (8 should-fire + 8 should-not-fire
per skill; FINDINGS.md). Net always-loaded saving measured here: 314 chars across 4 descriptions.

## Relation to the settled #30 — this run is a concurrent replication record only

While this run was in flight, #30 was independently completed and merged on main
(`../2026-07-09-description-ablation/`, ADR 0033 vendored the runner into building-skills,
PR #97 trimmed all four live descriptions). Main's decisions stand; this dir applies NO
SKILL.md, ADR, or reference changes — it is kept as an independent measurement record.
Two findings from it remain live:
- **Per-query durable-loss nuance:** both trims tested here for optimizing-context durably lost
  the "subagent vs plugin" should-fire query after dropping/shortening the mechanism-choice
  clause — consistent with main's kept trim, which preserves "choosing between skills, prompts,
  MCP, subagents, and hooks". Aggregate TP would have hidden the regression (v1 beat control
  4/8 vs 3/8 in aggregate while losing that query 3/3 -> 1/3).
- **Instrument defect, still present in the vendored runner:** the full-message fallback path
  ends on the first unrelated tool_use (`runner-companion-patch.diff` here; tracked as #104).

## Result (durable outcomes; TP over 8 should-fire, FP over 8 should-not-fire)

| Skill | Variant | Chars | TP | FP | Verdict |
|---|---|---|---|---|---|
| code-standards | control | 196 | 6/8 | 2/8 | |
| code-standards | v1 | 129 | 6/8 | 2/8 | **KEEP v1** |
| building-skills | control | 271 | 2/8 | 0/8 | |
| building-skills | v1 | 142 | 3/8 | 0/8 | **KEEP v1** |
| optimizing-context | control | 347 | 3/8 | 0/8 | **KEEP control (null)** |
| optimizing-context | v1 | 219 | 4/8 | 0/8 | rejected: durably loses q5 |
| optimizing-context | v2 | 272 | 3/8 | 0/8 | rejected: durably loses q5 |
| engineering-principles | control | 333 | 2/8 | 0/8 | |
| engineering-principles | v1 | 215 | 6/8 | 0/8 | **KEEP v1** |

- Decision rule (pre-registered, issue #30): keep the shortest variant with no should-fire query
  durably lost vs control and no FP raise. Aggregate TP alone does not decide — optimizing-context
  v1 beats control 4/8 vs 3/8 in aggregate yet durably loses "How do I decide between a subagent
  and a plugin for this task?" (control fired 3/3 escalation reps; v1 1/3, v2 1/3). Both trims
  dropped text apparently load-bearing for plugin-adjacent queries; 2-variant hard cap reached,
  null recorded, current description kept.
- **Rates are competitive, not isolated** (trigger-kit FINDINGS): nested `claude -p` inherits the
  container's built-in skills, so e.g. an organic "review this code" query can fire the real
  `code-review` skill over the planted one. Never read the absolute TP/FP as the description's
  quality; only the paired control-vs-variant delta is valid.
- engineering-principles v1's TP gain (2/8 -> 6/8) is directionally interesting (a shorter
  description out-competed the long one) but the 4 gained queries are single-rep, not
  escalation-confirmed; the keep decision needed only no-loss + no-FP-raise.
- Single-rep noise is real: optimizing-context q6 fired for control at the base rep but 0/3 under
  escalation. Durable outcome = majority of the 3 escalation reps where escalated, else the base rep.
- Description char counts are stripped (the pre-trim engineering-principles/optimizing-context
  lines carried a trailing space: 334/348 raw).

## Method

- **Runner: upstream-patched** (not the fallback). `git clone --depth 1 anthropics/skills`,
  then `skills/skill-creator/scripts/run_eval.py` + the kit's 3 local patches
  (`../2026-07-07-toolkit-grid/trigger-kit/runner-patches.diff`, applied clean) + one companion
  patch found this run (`runner-companion-patch.diff` here: the fallback detection path still
  hard-failed on an unrelated first tool call — same defect the kit's patch 1 fixed in the
  stream path). The FINDINGS hard-deny on executing the patched runner did not reproduce in
  this environment (cloud container, no auto-mode deny rules).
- The runner plants the description as a `.claude/commands/<skill>-skill-<uuid>.md` file in a
  clean project dir and detects whether the nested session's model invokes the planted skill
  (Skill tool, or Read of the planted file) before answering. Variants tested via
  `--description` override — SKILL.md untouched during measurement.
- **Model: sonnet** for the nested query sessions. The runner measures the session model's own
  trigger choice and defaults to the user's configured model; the kit/FINDINGS pinned none, so
  per issue #30's protocol the unspecified case uses sonnet.
- Reps: 1 per query x variant baseline; escalation to 3 reps per arm ONLY for decision-relevant
  flips vs control (a should-fire lost or a should-not-fire raised; favorable flips cannot
  invalidate a keep), majority of 3 decides. 219 total nested calls (`results.jsonl`: one record
  per query x variant x rep).
- 4 parallel workers, 180s timeout per query.

## Reproduce

```bash
git clone --depth 1 https://github.com/anthropics/skills /tmp/skills
patch /tmp/skills/skills/skill-creator/scripts/run_eval.py \
      ../2026-07-07-toolkit-grid/trigger-kit/runner-patches.diff
patch /tmp/skills/skills/skill-creator/scripts/run_eval.py runner-companion-patch.diff
mkdir -p /tmp/trigger-project/.claude
export RUNNER=/tmp/skills/skills/skill-creator/scripts/run_eval.py \
       RUNNER_PKG=/tmp/skills/skills/skill-creator PROJECT_ROOT=/tmp/trigger-project
python3 run_ablation.py --skill <skill> --variant <control|v1|v2>   # full 16-query pass
python3 run_ablation.py --skill <skill> --variant v1 --query-index 4,7 --reps 3 --rep-base 1  # escalation
```

`run_ablation.py` converts the trigger-kit query files to the runner's eval-set schema
(flat `{"query", "should_trigger"}` list), injects the variant text from `descriptions.json`,
and appends per-rep records to `results.jsonl`.
