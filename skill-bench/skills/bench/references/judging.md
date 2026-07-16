# Judging

## Why a cross-family judge

When the model that produced an output also grades it, scores inflate — the self-preference effect.
This repo measured it on the #172 Instrument-2 evidence: re-scoring the same blinded cells with
grok-4.5 instead of opus lowered the overall met-rate from roughly three-quarters to just over half,
and the panel-vs-baseline contrast moved from near-zero to clearly positive. So the grading model is
a first-class variable, not a neutral instrument. Default to a different family from the generator.

Foundations for grading validity (blinding, planted-defect calibration, prosecutor discipline) are
owned by [empirical-evals.md](empirical-evals.md); this file covers only what
is specific to the pluggable judge.

## Selecting the judge

`--judge auto` (the default) prefers grok (cross-family) and falls back to claude when the grok CLI
is absent — not every machine has it. On fallback the run prints a caveat and records it in the
report: grading is now same-family, so the self-preference caveat is back in force (absolute rates
inflate, the verdict can shift). An explicit `--judge grok` on a machine without grok fails with a
remedy rather than silently substituting; use `auto` to degrade gracefully.

Resolution order for the grok binary: `--bin` arg, then `$GROK_BIN`, then `PATH`, then the default
installer location. The claude judge resolves `claude` on `PATH`.

## Grading pipeline

Each cell is graded then prosecuted: a first pass judges every pre-registered expectation, then an
adversarial pass re-judges each met call and defaults to not-met when the evidence is thin. The final
met is the AND of the two (the min rule) — leniency in either stage drops the score. Normalization to
a neutral schema (stripping format and role tells) happens once and is reused, so a judge swap
changes only the grader, keeping the comparison clean.

## `--judge both` and the divergence diagnostic

`both` runs the chosen judge and loads the committed baseline judge, then reports how far they agree:
per-cell-per-expectation agreement, Cohen's kappa, how many calls each judge is stricter on, and a
verdict-flip check (did KEEP/CUT direction change between judges). Divergence is surfaced, never
averaged away — the disagreement is itself the finding. `both` needs both CLIs present; with only one
it degrades to a single-judge verdict and says so.

Offline re-analysis (`--cache <prior.jsonl>`) reuses a prior judge run and needs no CLI at all — the
placeholder judge makes zero calls and reports zero cost.
