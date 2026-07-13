# skill-bench (DRAFT skeleton — ADR 0055 / #170)

The repo's unique asset — the only public hermetic skill-**measurement** pipeline — packaged so any
skill author can measure their own skill. This is a scaffold, not a wired plugin: it records the
target design from ADR 0055. Nothing here is on the marketplace or moved out of its current home yet.

## What this plugin is (and is not)

- **Is:** a causal + pre-registration measurement layer — arm design (bare / cost-matched / structured),
  blind normalization, an adversarial prosecutor, a **cross-family judge**, cost gates, and
  pre-registration discipline. No commercial eval tool (promptfoo, Inspect, Braintrust, LangSmith,
  OpenAI Evals, Anthropic Console) ships these; all of them report aggregate pass rates only.
- **Is not:** an execution/observability engine. That is *rented* — see Substrate below.

## Architecture: bespoke layer on a rented substrate

```
  /bench-skill  /trigger-test  /bench-verdict        <- explicit-invoke UX (cost-gated)
  ---------------------------------------------------
  arm design | blind.py | prosecutor | cost_gate      <- BESPOKE causal + pre-reg layer (the asset)
  cross-family judge (grok default) | verdict.py         keep in-repo; no vendor sells this
  ---------------------------------------------------
  hermetic_driver adapter interface                   <- swappable RUNNER
     -> promptfoo (default; npx, CI regression gating)
     -> inspect-ai (serious agent-eval; sandboxed)
     -> native claude -p / grok -p (fallback)         <- rent tracing/versioning/gating; don't rebuild it
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
so the judge is a first-class, reported variable — default `grok-4.5`, `--judge both` for the
divergence diagnostic. Seed implementation: `scripts/lib/crossfamily_judge.py` (from the prototype).

### grok CLI notes (installed build 0.2.99; docs lag the binary)
- Headless: `grok -p <prompt>` or `--prompt-file <path>`; `--output-format json`; `--json-schema <schema>`
  constrains structured output; response envelope carries `structuredOutput`, `usage`, `modelUsage`.
- Sandbox for pure-text grading: `--disallowed-tools "Bash,Read,Write,Edit,WebSearch,WebFetch"`.
  KNOWN QUIRK: longer deny lists or `--disable-web-search` can trip a `run_terminal_cmd`
  tool-config validation error — use the known-good set above.
- `--agents <JSON>` hosts a grok-native judge/prosecutor panel (candidate for a grok-side fan-out).
- Auth: grok.com subscription (zero marginal cost) or `XAI_API_KEY` for CI. Model `grok-4.5` = 500K ctx.
- These flags are NOT in the public docs (docs.x.ai) but are present in the binary; pin the version.

## Milestones (per #170, unchanged; substrate + judge added)
- **M0** `/decide` ADR 0055 (scope, judge default, substrate). Resolve #150/ADR 0050 dependency shape.
- **M1** Pure move: `benchmarks/lib/*` + tests -> `skill-bench/scripts/lib/`; update `gates.yml` + nav; gates stay green.
- **M2** Genericize: config layer + consumer-layout test.
- **M3** Skill surfaces: the three `/bench-*` wrappers, explicit-invoke, cost-gated.
- **M4** Substrate adapter: promptfoo behind `hermetic_driver`; inspect-ai option; native fallback.
- **M5** Cross-family judge wired into the grading template + `judge-divergence` diagnostic.
- **M6** Dogfood: reproduce one committed benchmark via the installed plugin; then one third-party skill.

## Status
Skeleton only: `plugin.json` + this README + `scripts/lib/crossfamily_judge.py` (prototype seed).
No marketplace entry, no code moved, no gates touched. See `docs/decisions/0055-*` for the decision draft.
