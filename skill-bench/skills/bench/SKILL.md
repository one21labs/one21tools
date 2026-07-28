---
name: bench
description: Use when deciding whether a Claude Code skill earns its context cost, when re-scoring benchmark evidence you already have, or when testing whether a skill's description actually fires.
---

# /bench

Measure a skill's value, or re-judge existing evidence. The deterministic parts (arms,
grading rubric, prosecutor, verdict math, cost) are tested scripts; your job is to choose what to
measure and interpret the KEEP/CUT verdict. Invoke a subcommand explicitly.

## `verdict` — re-judge existing results (no generation spend)

Recompute a decision-outcome verdict from an already-graded, blinded benchmark dir, swapping only
the judge. The only cost is judge calls (`--cache` needs no CLI at all).

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bench_verdict.py" --dir <benchmark-dir> \
  --judge auto|<backend>|both [--cache <prior.jsonl>] [--cells-out <cells.jsonl>] \
  [--out report.json]
```

- `--dir` must hold `graded/{verdicts.jsonl,arm_map.tsv,keys.json}` (ADR 0025/0026 layout).
- `--judge auto` (default) resolves a backend per [judging.md](references/judging.md); `both` adds
  the judge-divergence diagnostic (agreement, kappa, verdict flip).
- Emits arm means, clustered C-B with 95% CI, KEEP/CUT, per-expectation, and `notional_cost_usd`.
  See [cost-and-verdict.md](references/cost-and-verdict.md).
- `--cells-out` also writes per-cell re-graded verdicts (jsonl) — the substrate for computing a
  pre-registered bar set on the second judge's basis so a judge-disagreement rule (disagree =>
  bar NOT MET) is mechanical, never a manual comparison.

## `skill` — with/without value benchmark (paid generation)

Does a skill improve output, or just cost context? Generate each eval task with the skill loaded and
bare, grade both against pre-registered expectations, report the with-without delta.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bench_skill.py" --evals <evals.json> \
  --with-cmd '<json argv, skill loaded>' --without-cmd '<json argv, bare>' \
  [--judge auto] [--substrate native|promptfoo] [--reps 3] --yes
```

- `--evals`: JSON list of `{id, task, expectations:[...]}`. Arms differ ONLY in skill loading (arm
  symmetry) — the task is appended as the final CLI arg.
- Prints a cost estimate and **refuses to spend without `--yes`** (spend guard).
- `--substrate` selects the generation runner; see [substrate.md](references/substrate.md).
- `--reps` (default 3): generations per task x arm — a single pass cannot separate reliably-good
  from lucky (ADR 0058); use 1 only for a smoke run.

## `trigger` — description ablation (paid trigger runs)

Does the description fire on should-trigger queries and stay quiet on should-not? Runs the
vendored trigger runner (ADR 0033) on a flat eval set of `{query, should_trigger}` items.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/run_eval.py" --eval-set <path> --skill-path <dir> \
  --model <pinned-model> --num-workers 1 --timeout 240 --yes \
  [--description "<variant text>"]
```

- Prints the run count and **refuses to spend without `--yes`** (spend guard), as `skill` does.
- Linux/WSL-only (#170 hard problem 4) — document, don't silently degrade.
- `--num-workers 1` is MANDATORY (concurrent workers collapse rates toward 1/N); a timeout is a
  null measurement, never a False. Report only matched-protocol A/B deltas, never absolute rates.

## Guardrails (all subcommands)

- A cross-family judge is the default because same-family grading (Claude grades Claude) is a
  measured confound. `auto` prefers your configured judge, then grok, copilot, then claude with a
  caveat. Wire what you have via [judging.md](references/judging.md); a judge that cannot name its
  model is refused, not counted as independent.
- Cost is priced notionally at published rates even when marginally free.
- Small n (scenario-clustered): CIs are wide, verdicts are exploratory — a judge flip is a signal to
  re-measure, not a settled result.
- Never edits a frozen dated benchmark dir (append-only, ADR 0041).
- **Design-time rules live one tier down — read them BEFORE a grid, not during.** Wording a
  pre-registration neutrally, arm output contracts and the ERROR-cell rule, and the saturation
  pre-screen: [pre-registration.md](references/pre-registration.md). What a verdict README may
  claim: [cost-and-verdict.md](references/cost-and-verdict.md).

New benchmark dirs start from the canonical templates in `templates/` (grid runner, blinding,
grading workflow) — copy and adapt; never clone a sibling dated dir. The grading workflow needs
the Claude Code `Workflow` tool (#170 hard problem 3); without it, grade serially via `claude -p`.

Method foundations ship WITH this skill (ADR 0063):
[pre-registration.md](references/pre-registration.md),
[empirical-evals.md](references/empirical-evals.md),
[description-ablation.md](references/description-ablation.md),
[evaluating-your-own-work.md](references/evaluating-your-own-work.md) — read before you design a
run against a skill you wrote. skill-bench installs standalone.
