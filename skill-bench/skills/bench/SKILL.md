---
name: bench
description: Use when measuring whether a Claude Code skill earns its context cost, or re-judging existing benchmark evidence with a cross-family judge and no generation spend. Two subcommands — `verdict` (recompute a verdict from already-graded results, pluggable judge, zero generation cost) and `skill` (paired with/without value benchmark of a skill). Explicit-invoke; cross-family grok judge by default with a claude fallback; deterministic notional cost accounting.
disable-model-invocation: true
---

# /bench

Measure a skill's value, or re-judge existing evidence — honestly. The deterministic parts (arms,
grading rubric, prosecutor, verdict math, cost) are tested scripts; your job is to choose what to
measure and interpret the KEEP/CUT verdict. Invoke a subcommand explicitly.

## `verdict` — re-judge existing results (no generation spend)

Recompute a decision-outcome verdict from an already-graded, blinded benchmark dir, swapping only
the judge. The only cost is judge calls (grok is subscription-billed; `--cache` needs no CLI at all).

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bench_verdict.py" --dir <benchmark-dir> \
  --judge auto|grok|claude|both [--cache <prior.jsonl>] [--cells-out <cells.jsonl>] \
  [--out report.json]
```

- `--dir` must hold `graded/{verdicts.jsonl,arm_map.tsv,keys.json}` (ADR 0025/0026 layout).
- `--judge auto` (default) uses grok if available else claude; `both` adds the judge-divergence
  diagnostic (agreement, kappa, verdict flip). See [judging.md](references/judging.md).
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

## Guardrails (both subcommands)

- Cross-family grok judge is the default because same-family grading (Claude grades Claude) is a
  measured confound; on grok's absence it falls back to claude with a printed caveat.
- Cost is priced notionally at published rates (deterministic) even when marginally free.
- Small n (scenario-clustered): CIs are wide, verdicts are exploratory — a judge flip is a signal to
  re-measure, not a settled result.
- **No primed conclusions (ADR 0059):** every pre-registration, experiment issue, and eval title
  states a FALSIFIABLE hypothesis neutrally — kill conditions and bars up front, motivation labeled
  as grounding (never evidence), a null recorded as an equally valid outcome. Titles pose the
  question, never the answer. Advocacy wording is itself a contamination channel: agents read it.
- Never edits a frozen dated benchmark dir (append-only, ADR 0026).

Method foundations (pre-registration, empirical evals) live in the `building-skills` skill; this
skill references them rather than restating.
