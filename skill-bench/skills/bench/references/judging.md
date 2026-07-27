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

## Wiring a judge for YOUR machine

The judge is whichever cross-family model you can already reach. This plugin does not assume the
CLIs its authors happened to have, so setting it up is a short walk rather than an install list.
Take the first step below that fits.

**1. See what you already have.**

```
python3 -c 'import os, sys; sys.path.insert(0, os.environ["CLAUDE_PLUGIN_ROOT"] + "/scripts/lib"); import judge; \
print([n for n in judge.BACKENDS if judge.cli_available(n)])'
```

Anything besides `claude` alone means you already have a cross-family judge and `--judge auto`
will pick it. Preference order is `command`, `grok`, `copilot`, then `claude` — a judge you
configured on purpose outranks one merely found on PATH.

**2. A shipped backend installed off PATH.** Point its variable at the binary — `$GROK_BIN`,
`$COPILOT_BIN`. This is the common case, not the exception: editors and extensions routinely
bundle a CLI somewhere PATH never sees.

**3. Any other model — the general case.** Set two variables and you are done, no code change:

```
export SKILL_BENCH_JUDGE_CMD='ollama run mistral'   # reads the prompt on stdin, answers on stdout
export SKILL_BENCH_JUDGE_MODEL='mistral-7b'         # what it actually calls
```

A local model server, a vendor CLI with no backend here, or an in-house wrapper all qualify. The
model id is required rather than decorative: the report has to state whose judgement it carries,
and a judge that cannot name itself cannot evidence independence. An unset or same-family id fails
at construction with that reason, instead of producing a confounded number.

**4. Nothing cross-family reachable.** `auto` falls back to claude, prints the caveat, and records
it in the report. Matched-protocol A/B deltas remain usable; absolute rates inflate.

To add a named backend permanently, add one entry to `BACKENDS` in `scripts/lib/judge.py` — the
resolver is data-driven, so no branch anywhere needs editing.

## Knowing the grade really left the family

A cross-family judge is only cross-family if you know which model answered, and a router that
picks per call may pick the generator's own family. GitHub Copilot's `auto` mode was measured
listing `claude-haiku-4.5` among its candidates for a single request (26-Jul-2026), so a backend
that cannot pin a model reads the answering model back from each response and raises rather than
returning a grade whose independence was assumed. `CommandJudge` gets the same treatment through
its declared model id.

Copilot specifically cannot be pinned on every plan: `--model <id>` is entitlement-gated and on a
restricted plan rejects every id the CLI itself lists — including the one `auto` then selects. That
is why the backend runs `auto` and verifies afterwards instead of asking for a model up front. If
your plan does grant explicit selection, `--model` on a pinned foreign id is the stronger setup.

Resolution order for a shipped backend's binary: the library-only `bin=` constructor arg (no CLI
flag), then its `$*_BIN` variable, then `PATH`, then the vendor's default installer location.

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
averaged away — the disagreement is itself the finding. `both` needs ONE reachable cross-family
judge: the baseline half is read off the committed cells, never re-graded, so no second CLI is
involved. With no cross-family lane reachable it degrades to a single-judge verdict and says so.

Offline re-analysis (`--cache <prior.jsonl>`) reuses a prior judge run and needs no CLI at all — the
placeholder judge makes zero calls and reports zero cost.
