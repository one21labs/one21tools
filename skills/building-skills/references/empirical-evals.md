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
- **Keep cleanly-measured nulls.** A whole eval that ties across models — the skill genuinely
  does not help that task — is a valid measurement, not dead weight. Deleting nulls biases the
  set toward skill-favorable evals (survivorship) and the delta-per-1k verdict then overstates.
  Fix a non-discriminating eval by REWRITING it to a harder case after transcript-level
  diagnosis — never a blind "make it harder" pass (that regressed 6 cells; see
  benchmarks/2026-07-07-toolkit-grid/retune-results.md), never by deletion. (Distinct from a
  non-discriminating ASSERTION within an eval, which IS cut — see the DISCRIMINATE rule above.)

## Running the benchmark

Run skill-creator's benchmark mode over the eval set with **at least 3 runs per
configuration** (LLM sampling is noisy; single runs are anecdotes), then its aggregation.
Escalate sequentially (ADR 0019): after aggregating, add replicates or evals ONLY where the
eval-level CI straddles the verdict boundary (0.5 win rate / zero delta) — never spend runs
on an already-unambiguous cell.

```
python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
```

Grading disciplines:

- **Fresh grader, different model** (ADR 0013) — the bundled grader otherwise inherits the
  session model and its biases.
- **Blind the arm** (ADR 0019) — stage each run under a neutral label (`arm-A`/`arm-B`) and
  withhold the arm->config mapping from the grader; reveal it only at aggregation. A grader
  that sees `with_skill` in the path grades with an expectation; blinding removes that cue.
- Grade from the produced output/transcript, never from intent.

### Grading reliability under the Claude-only constraint (ADR 0019)

Only Claude can grade here — a fixed constraint, not a choice. The paired design already
cancels raw self-preference (both arms are Claude output); what survives is style-alignment
bias, family blind spots, and judge noise. Mitigation stack, in priority order:

1. **Mechanize first.** Any assertion that CAN execute MUST: run the produced script against
   the failure input, run a linter for dead code, grep for the banned pattern — grade from
   observed behavior. The model judges only what cannot execute. An executable check has no
   family bias at all; eval authors write assertions to be executable wherever possible.
2. **Planted-defect calibration.** Per benchmark cycle, grade a small known-truth set: real
   outputs with deliberately injected violations plus known-clean ones. The grader's
   false-pass / false-fail rate per assertion class is ground truth by construction — it
   MEASURES the family blind spot instead of guessing at it. Report it in the snapshot.
3. **Prosecutor pass.** Every PASS verdict is re-examined by a second, fresh grader
   instructed to refute it from the artifact; the pass stands only if the evidence survives.
   Attacks leniency and style halo.
4. **Human calibration sample.** Periodically, the owner blind-grades ~10 sampled
   (assertion, output) pairs; agreement bounds the residual empirically — the only external
   anchor available.

Residual after all of the above: family bias on genuinely judgment-only assertions. Named,
bounded by (2)/(4), not eliminated. Treat those verdict components as directional.

## The verdict

Post-process the harness's `benchmark.json` with the owned layer:

```
python skills/building-skills/scripts/eval_verdict.py <benchmark.json> --skill <skill-folder>
```

It pairs each eval's runs across configurations and reports:

- **Win rate with a Wilson 95% CI, eval-clustered** (ADR 0019): replicates of one eval are
  correlated, so each eval's mean delta becomes one win/loss/tie and the headline interval
  is over non-tied EVALS — trust the interval, not the point estimate; under 4 non-tied
  evals (the authoring floor) it prints a width warning. Pair-level W/L/T stays as detail.
- **Mean pass-rate delta** and the mean run-time token delta.
- **VERDICT — delta per 1k chars of loaded context**: the cost-per-benefit number. The
  denominator (ADR 0019) defaults to SKILL.md body (the always-on cost); `--include-references`
  charges body + all references/*.md (an upper bound — assumes every reference loaded), and
  `--loaded-chars N` takes an exact measured count. For a reference-heavy skill the two bounds
  diverge sharply (engineering-principles: +0.0235 body-only vs +0.0029 with references) — report
  BOTH; the truth is between them. A skill whose CI straddles zero delta is not yet shown to
  justify ANY chars; a positive verdict ranks skills by value density.

`--fail-under <delta>` exits nonzero below a floor — for local regression checks when
iterating on a skill. It is NOT a CI gate: benchmark runs are non-deterministic, so gates.yml
runs only `eval_verdict_test.py` (the deterministic decision logic), never the benchmark.

## Result snapshots

Benchmark verdicts are model- and eval-relative and the raw runs are ephemeral, so append a
dated machine-readable snapshot under `benchmarks/` after each run (ADR 0019) — a `.jsonl` of
per-cell verdict records plus a `metadata.json`: executor model, eval-set content hash,
protocol/ADR version, blinded (y/n), **hermetic (y/n)**, the denominator basis, and (when raw is
retained) the `sample_rule`. JSON/JSONL is the SSoT; any markdown view is rendered from it, never
hand-maintained. Append-only, never edited: a snapshot is a measurement record as of its date, not
current truth (so it is not a stale mirror). This is what makes `--fail-under` and
regression-vs-history possible — without a stored baseline there is nothing to regress against.

**Hermetic executor gates a verdict (ADR 0023).** A run counts toward a keep/cut verdict only if
the control arm had zero installed plugins and zero repo/skill file read access — a cloud container,
or a locked-down `claude -p` (`enabledPlugins: {}`; deny the `Skill`/`Agent`/`Read`/`Grep`/`Glob`
tools; `CLAUDE_CONFIG_DIR` at an empty dir). Otherwise the control arm inherits the treatment
and the baseline is not treatment-free — record it `hermetic: false` as a confounded null, never a
verdict.

**Auditable raw sample (ADR 0023).** Retain the raw graded text for a bounded, deterministically
defined sample — the planted-defect calibration set + every cell whose CI straddles the verdict
boundary — ON main under `benchmarks/<date>/audit/` (git self-verifies it: no per-cell hash, no
off-main bundle). It is what the prosecutor / sampled-agreement / human-calibration passes and ADR
0019's re-grade reopen-conditions read; `eval_verdict.py` re-derives `sample_rule` and fails if any
selected cell's transcript is missing (the silent-drop tripwire). Keep raw only if a consumer reads
it — retention turns on WITH that check, not before.

## Tier 2 — section ablation

For a skill that is always-in-context or near its char cap, measure WHICH content earns its
place, not just whether the whole does. Treat sections (or each references/*.md) as factors:
benchmark variants with one section removed per variant (one-factor-at-a-time), same eval
set, same replicates, and compare verdicts. A section whose removal moves the delta less
than the CI width is a cut candidate — the empirical form of "every char earns its place."
Full factorial designs over many sections multiply run cost fast; ablate the few sections
you actually doubt, and only for skills whose cost makes the answer worth buying.

The same method applies to **any always-loaded prose**, not just a SKILL.md — a repo `CLAUDE.md`
or the pdca-init `claude-md-template.md` it seeds. These pay their cost on EVERY request, so
ablation matters more; vary the prose per variant over a small task set the section targets.
**Hold the executor's base framing NEUTRAL** — prose ablation is framing-sensitive: a biased
framing swamps the treatment (one section measured +0.17/0.00/+0.375 across
tool-denied/implement-biased/neutral framings; ADR 0024). This is the VERIFY step of retrospect ->
PDCA: `/retrospect` proposes an always-loaded line, `/decide`'s verify runs the ablation, the same
bar decides — removal moving the delta less than the CI width means the line does not earn its cost
(cut or relocate to a gate/script); a line whose absence measurably drops the delta stays.
Add-what-recurs, cut-what-does-not: keep the always-loaded surface minimal.

## Scope and limits

- **Triggering is out of scope here** — the paired benchmark injects the skill, so it cannot
  measure whether the description ACTIVATES; use the triggering tests in
  [evaluation-patterns.md](evaluation-patterns.md) and skill-creator's trigger runner.
- **Deltas are model- and eval-relative** — re-benchmark before comparing verdicts across
  model generations; record the executor model (benchmark.json metadata carries it).
- Upstream gaps worth routing upstream, not forking (ADR 0013): an independent grader
  model flag, CI fail-under, regression-vs-history.
