# Empirical Evals — measure that a skill earns its context cost

Read this when a skill needs empirical evidence, not authoring guidance (that is
[evaluation-patterns.md](evaluation-patterns.md)). The repo's claim is "token efficiency
enforced, not aspirational" — char budgets enforce the COST side; this protocol measures the
BENEFIT side. Together: a skill is justified when its measured effect is worth its chars.

## Table of Contents

1. [The three layers](#the-three-layers)
2. [Setup](#setup)
3. [Authoring evals](#authoring-evals)
4. [Running the benchmark](#running-the-benchmark)
5. [The verdict](#the-verdict)
6. [Tier 2 — section ablation](#tier-2--section-ablation)
7. [Scope and limits](#scope-and-limits)

---

## The three layers

Complementary, not alternatives:

| Layer | Owner | Answers |
|-------|-------|---------|
| Pressure testing | eval authoring (below; method from obra/superpowers) | Can the agent rationalize its way around the skill under pressure? |
| Paired benchmark | Anthropic skill-creator harness (delegated — ADR 0013) | Does the skill measurably beat the no-skill baseline? |
| Cost verdict | `scripts/eval_verdict.py` (owned) | Does the delta justify the skill's chars? |

Execution is DELEGATED: skill-creator's benchmark mode already runs paired
with_skill/without_skill configurations with graded assertions and token/time stats. This repo
owns only what upstream lacks: the schema gate (validate.py R7) and the cost-per-benefit
verdict with a confidence interval.

## Setup

Install skill-creator from Anthropic's agent-skills marketplace (`anthropics/skills` on
GitHub; it is NOT bundled with Claude Code and NOT shipped by this marketplace). No
skill-creator available = fall back to the manual baseline steps in
[evaluation-patterns.md](evaluation-patterns.md); the protocol below assumes the harness.

## Authoring evals

Write `evals/evals.json` in the skill folder, in **skill-creator's schema** — its
`references/schemas.md` is the schema SSoT; `skills/code-standards/evals/evals.json` is this
repo's live example. `validate.py` gates the shape (skill_name matches the folder, unique
integer ids, non-empty prompt/expected_output/expectations).

Disciplines:

- **4+ cases**: normal, edge, and at least one pressure case. Expectations must
  DISCRIMINATE — an assertion that passes with and without the skill measures nothing
  (skill-creator's analyzer flags these; cut them).
- **Pressure cases** (method from obra/superpowers' skill-testing): phrase the prompt to
  invite the failure the skill exists to prevent — time pressure ("just a quick script"),
  sunk cost, authority ("my lead said skip the checks"). If the agent complies with the
  pressure and still meets the expectations, the skill held. Keep a rationalization table
  while iterating: each excuse an agent used to dodge the skill becomes a loophole to close
  in the skill text.
- **Author-separation** (ADR 0013): a fresh Claude B writes the expectations, not the
  skill's author — an author grades their own intent; a fresh instance grades the artifact.

## Running the benchmark

Run skill-creator's benchmark mode over the eval set with **at least 3 runs per
configuration** (LLM sampling is noisy; single runs are anecdotes), then its aggregation:

```
python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
```

Grading disciplines (both from ADR 0013):

- **Fresh grader, different model** — the bundled grader otherwise inherits the session
  model and its biases.
- Grade from the produced output/transcript, never from intent.

## The verdict

Post-process the harness's `benchmark.json` with the owned layer:

```
python skills/building-skills/scripts/eval_verdict.py <benchmark.json> --skill <skill-folder>
```

It pairs each eval's runs across configurations and reports:

- **Win rate with a Wilson 95% CI** over non-tied pairs — trust the interval, not the point
  estimate; under ~9 non-tied pairs it prints a width warning (add evals or replicates).
- **Mean pass-rate delta** and the mean run-time token delta.
- **VERDICT — delta per 1k chars** of SKILL.md body: the cost-per-benefit number. A skill
  whose CI straddles zero delta is not yet shown to justify ANY chars; a positive verdict
  ranks skills by value density and tells you which near-cap skill deserves its budget.

`--fail-under <delta>` exits nonzero below a floor — for local regression checks when
iterating on a skill. It is NOT a CI gate: benchmark runs are non-deterministic, so gates.yml
runs only `eval_verdict_test.py` (the deterministic decision logic), never the benchmark.

## Tier 2 — section ablation

For a skill that is always-in-context or near its char cap, measure WHICH content earns its
place, not just whether the whole does. Treat sections (or each references/*.md) as factors:
benchmark variants with one section removed per variant (one-factor-at-a-time), same eval
set, same replicates, and compare verdicts. A section whose removal moves the delta less
than the CI width is a cut candidate — the empirical form of "every char earns its place."
Full factorial designs over many sections multiply run cost fast; ablate the few sections
you actually doubt, and only for skills whose cost makes the answer worth buying.

## Scope and limits

- **Triggering is out of scope here** — the paired benchmark injects the skill, so it cannot
  measure whether the description ACTIVATES; use the triggering tests in
  [evaluation-patterns.md](evaluation-patterns.md) and skill-creator's trigger runner.
- **Deltas are model- and eval-relative** — re-benchmark before comparing verdicts across
  model generations; record the executor model (benchmark.json metadata carries it).
- Upstream gaps worth routing upstream, not forking (ADR 0013): an independent grader
  model flag, CI fail-under, regression-vs-history.
