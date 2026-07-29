# skill-bench

A public hermetic pipeline for measuring YOUR OWN skill's value — packaged so any skill author
can measure their own skill: `/plugin install skill-bench@one21tools`. Decision record:
ADR 0055 (scope) + ADR 0063 (completion set); plan: #170 — all in the source repo's decision log,
outside this plugin's shipped files, so no link survives an install.

Related work (surveyed 29-Jul-2026): bring-your-own-skill measurement is a crowded lane —
anthropics/skills' skill-creator is the reference design for paired with/without arms and blind
A/B comparison; adewale/skill-eval-harness reaches paired-arm rigor with an exact sign-flip
permutation test and judge-calibration tooling; aws-samples/sample-agent-skill-eval pairs arms
and prices runs. benchflow-ai's **SkillsBench** (arXiv:2602.12670) is a different thing: a
fixed-corpus leaderboard with deterministic verifiers, not a BYO harness. What this plugin adds
is the conjunction for JUDGED domains, plus three mechanisms that survey did not find shipped
elsewhere — each named with the path that implements it:

- a machine-checked **pre-registration guard** (`prereg_guard.py`, step 1 of
  `evaluating-your-own-work.md`'s procedure) — refuses a design with unstated power, an
  unreachable equivalence margin, or an author-written arm with no falsifier (methodology prior
  art: arXiv:2606.11217, arXiv:2605.27789; the enforcement-as-code we did not find);
- a cross-family judge **verified, not merely configured** — the copilot lane reads back which
  model actually answered and fails closed on a same-family landing (`judge.py`); routing alone
  ships in Inspect, Braintrust, and promptfoo;
- a **downgrade-only adversarial prosecutor** in a separate pass — on the `/bench verdict` path;
  `/bench skill` grades once, with no prosecutor today (arXiv:2603.12123 on separate-context
  second passes).

Blind grading here means schema normalization that strips format, role, and header tells before
the judge sees anything (arXiv:2604.23178 finds style/format bias dominates), not A/B labels alone.

## What this plugin is (and is not)

- **Is:** a causal + pre-registration measurement layer — paired hermetic arms, blind
  normalization, a prosecutor (verdict path), a **cross-family judge**, spend gates, and
  pre-registration discipline.
- **Is not:** an execution/observability engine (that is *rented* — see Substrate below), a
  leaderboard, or a SKILL.md linter.

**Honest limits.** The verdict interval is a one-sample t on eval-clustered deltas (ADR 0019,
the paired-and-clustered recipe of arXiv:2411.00640); sequential escalation and pilot stop rules
are uncorrected optional stopping, so an escalated run's nominal coverage is optimistic. The
prosecutor does not run on `/bench skill`. Cost gating is a pre-run estimate plus a spend
refusal, not a runtime ceiling — Inspect AI's native dollar limits are stronger on that axis.

## Architecture: bespoke layer on a rented substrate

```
  /bench (verdict | skill | trigger)                  <- one skill, three subcommands
  ---------------------------------------------------
  arm design | blind.py | prosecutor | cost_gate      <- BESPOKE causal + pre-reg layer (the asset)
  cross-family judge (pluggable) | benchstats.py         keep in-repo; the bespoke layer
  ---------------------------------------------------
  hermetic_driver adapter interface                   <- swappable RUNNER
     -> promptfoo (npx, version-pinned; CI regression gating)
     -> inspect-ai (PLANNED, not shipped; serious agent-eval; sandboxed)
     -> native claude -p / grok -p (default)          <- rent tracing/versioning/gating; don't rebuild it
```

## The cross-family judge (why it is default-on)

A 72-cell prototype (2026-07-13) re-graded #172's Instrument 2 with **grok-4.5** instead of opus,
holding normalization fixed so the judge family was the only changed variable. Findings:

| | opus (same-family) | grok-4.5 (cross-family) |
|---|---|---|
| overall met-rate | 0.747 | **0.552** (~20pp stricter) |
| C - B (panel vs cost-matched) | +0.010 | **+0.125** |
| disagreements | — | 57 stricter / 1 looser, kappa 0.575 |

The same-family judge was lenient **and** hid the panel's edge (the exp-2 "falsifiable criterion"
ceiling at 0.88-flat under opus broke to C 0.83 / B 0.54 under grok). The judge changed the verdict,
so the judge is a first-class, reported variable. `--judge both` gives the divergence diagnostic;
`skills/bench/references/judging.md` owns which backend `auto` resolves to and how to wire your own.

### grok CLI notes (installed build 0.2.99; docs lag the binary)
- Headless: `grok -p <prompt>` or `--prompt-file <path>`; `--output-format json`; `--json-schema <schema>`
  constrains structured output; response envelope carries `structuredOutput`, `usage`, `modelUsage`.
- Sandbox for pure-text grading: `--disallowed-tools "Bash,Read,Write,Edit,WebSearch,WebFetch"`.
  KNOWN QUIRK: longer deny lists or `--disable-web-search` can trip a `run_terminal_cmd`
  tool-config validation error — use the known-good set above.
- `--agents <JSON>` hosts a grok-native judge/prosecutor panel (candidate for a grok-side fan-out).
- Auth: grok.com subscription (zero marginal cost) or `XAI_API_KEY` for CI. Model `grok-4.5` = 500K ctx.
- These flags are NOT in the public docs (docs.x.ai) but are present in the binary; pin the version.

## Portability (installed elsewhere)

The pure layer (`costing`, `benchstats`, `rubric`, judge dispatch, the promptfoo config
gen/parse) is machine-independent — stdlib only, relative imports, `npx --yes` fetches the
version-pinned promptfoo on demand (pin + bump rule: `substrate.py:PromptfooSubstrate.PIN`,
ADR 0058). What a consumer must provide / knows:

- **CLIs on PATH, authenticated:** `claude` (generation, and the same-family fallback judge),
  `node`/`npx` (promptfoo substrate), plus one cross-family judge — any `BACKENDS` entry in
  `scripts/lib/judge.py`, currently `grok`, `copilot`, or a command of your own behind
  `$SKILL_BENCH_JUDGE_CMD`. Not bundled — documented requirements;
  `skills/bench/references/judging.md` owns the wiring. `copilot` is the weakest of the three: its
  `--model` is entitlement-gated here and rejects every id, so it runs `auto`, whose candidate set
  includes Claude models — `judge.py` reads back who answered and fails the grade on a same-family
  landing rather than reporting it as independent.
- **Invoke via `${CLAUDE_PLUGIN_ROOT}`:** the `/bench` subcommands call
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/..."` so they resolve from any working directory.
- **Hermetic generation config** (`hermetic_driver`, used only by the isolated-generation mode —
  NOT by `/bench verdict` or the native `/bench skill`): set `$SKILL_BENCH_CONFIG_DIR` to a clean
  credentials-only Claude config dir. The default is this repo's fallback and won't exist elsewhere.
- **Platform:** the hermetic CLAUDE.md-discovery behavior and `/bench trigger` are Linux/WSL-only
  (#170 hard-problem 4).
- **Method depth ships in-plugin** (ADR 0063 Call 2 as reworked): pre-registration,
  empirical-evals, and description-ablation live under the `/bench` skill's references —
  skill-bench is standalone.
- **Grading workflow:** `templates/grade.workflow.js` needs the Claude Code `Workflow` tool
  (#170 hard-problem 3); without it, grade serially via `claude -p` with the same prompts.

## Status
Runnable: `/bench` with `verdict` + `skill` + `trigger` subcommands (native substrate +
availability-aware pluggable cross-family judge + deterministic cost accounting),
config layer + consumer-layout test, canonical templates
(`templates/`), #191 infrastructure-vs-quality hardening (ERROR cells, capture symmetry,
per-cell attribution), registered in the marketplace.

Install-portability proven at two levels: `consumer-layout.test.mjs` reproduces a verdict from a
copied-out layout at an unrelated cwd with NO CLIs (offline plumbing + math — CI-runnable); and a
manual live run re-graded from a `/tmp` install driving grok end-to-end (4 calls, 0 errors — not
CI-runnable, needs authenticated grok). Promptfoo generation is wired into
`/bench skill` (`--substrate promptfoo`, proven live). Rationale lives in the source repo's
`docs/decisions/0055-*` and `0063-*`, which do not ship with the plugin.

## Provenance

Direction, principles, and requirements for this plugin originate with the repo owner; Claude
authors the implementation — harness code, rubric and doc mechanics, records — under that
direction (ADR 0085). Where a specific design call is the owner's, the file says so at the point
it applies: `scripts/lib/judge.py` carries the environment-general judge direction, for one.
