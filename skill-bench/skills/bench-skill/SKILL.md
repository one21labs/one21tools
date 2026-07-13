---
name: bench-skill
description: Use when measuring whether a Claude Code skill earns its context cost — a paired with-skill vs bare (without) value benchmark over an eval set, generation run through a rented substrate (promptfoo/native) and graded by a default cross-family (grok) judge, reporting the with-without fraction-met delta and a KEEP/CUT verdict. Explicit-invoke; requires --yes before any paid generation.
disable-model-invocation: true
---

# /bench-skill

Does a skill actually improve output, or just cost context? This runs each eval task twice — once
with the skill loaded, once bare — generates via a rented substrate, grades both outputs against
pre-registered expectations with a cross-family judge, and reports the value delta.

## Usage

```
python3 scripts/bench_skill.py \
  --evals <evals.json> \
  --with-cmd '<json argv, skill loaded>' \
  --without-cmd '<json argv, bare>' \
  --judge grok|claude --substrate native|promptfoo --yes
```

- `--evals`: JSON list of `{id, task, expectations:[...]}` — the task text is the prompt; expectations
  are the binary checks the output must meet.
- `--with-cmd` / `--without-cmd`: argv arrays for the two arms (the task is appended as the final
  arg). The only difference should be skill-loaded vs bare — everything else matched (arm symmetry).
- Prints a cost estimate; **refuses to spend without `--yes`** (spend guard, #170 hard-problem 1).

## Output

Arm means (with / without), the clustered with-without delta with 95% CI, per-task deltas, and a
KEEP/CUT verdict (ADR 0025 fraction-met, ADR 0019 clustered CI). A positive, CI-clearing delta means
the skill earns its cost; a null or negative delta is a CUT-candidate routed to `/decide`.

## Guardrails

- Generation is the only paid step; the judge is grok (subscription = zero marginal cost) by default.
- Arm symmetry: with/without commands must differ ONLY in skill loading, or the delta measures the
  wrong thing. The substrate runs both hermetically.
- Small n: task-clustered CIs are wide — verdicts are exploratory, a flip is a signal to re-measure.
- Cross-family judge default because same-family grading is a measured confound (see /bench-verdict).
