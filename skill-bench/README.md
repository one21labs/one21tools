# skill-bench

The repo's unique asset — the only public hermetic skill-**measurement** pipeline — packaged so any
skill author can measure their own skill: `/plugin install skill-bench@one21tools`. Decision record:
ADR 0055 (scope) + ADR 0063 (completion set); plan: #170.

## What this plugin is (and is not)

- **Is:** a causal + pre-registration measurement layer — arm design (bare / cost-matched / structured),
  blind normalization, an adversarial prosecutor, a **cross-family judge**, cost gates, and
  pre-registration discipline. No commercial eval tool (promptfoo, Inspect, Braintrust, LangSmith,
  OpenAI Evals, Anthropic Console) ships these; all of them report aggregate pass rates only.
- **Is not:** an execution/observability engine. That is *rented* — see Substrate below.

## Architecture: bespoke layer on a rented substrate

```
  /bench (verdict | skill | trigger)                  <- one explicit-invoke skill, subcommands
  ---------------------------------------------------
  arm design | blind.py | prosecutor | cost_gate      <- BESPOKE causal + pre-reg layer (the asset)
  cross-family judge (grok default) | verdict.py         keep in-repo; no vendor sells this
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

## Milestones (per #170; substrate + judge added by ADR 0055)
- **M0** `/decide` ADR 0055 — accepted as amended by ADR 0063 (#150/ADR 0050: no dependency declared; its split is a separate PR). DONE
- **M1** Pure move: `benchmarks/lib/*` + tests -> `skill-bench/scripts/lib/`; `gates.yml` + nav updated. DONE
- **M2** Genericize: config layer + consumer-layout test. DONE
- **M3** Skill surface: one `/bench` skill (verdict + skill + trigger) + on-demand references + canonical `templates/` (grid runner, blinding, grading workflow). DONE
- **M4** Substrate adapter: promptfoo behind `hermetic_driver`; native fallback (inspect-ai stays planned). DONE
- **M5** Cross-family judge wired in + `judge-divergence` diagnostic. DONE
- **M6** Dogfood: `/plugin install` round-trip proven; the paid reproduce-a-committed-benchmark and third-party-skill runs are tracked as follow-up issues (spend-gated, ADR 0063 Call 4).

## Portability (installed elsewhere)

The pure layer (`costing`, `benchstats`, `rubric`, judge dispatch, the promptfoo config
gen/parse) is machine-independent — stdlib only, relative imports, `npx --yes` fetches the
version-pinned promptfoo on demand (pin + bump rule: `substrate.py:PromptfooSubstrate.PIN`,
ADR 0058). What a consumer must provide / knows:

- **CLIs on PATH, authenticated:** `grok` (grok judge/gen — resolved via `$GROK_BIN`, then PATH,
  then `~/.grok/bin/grok`), `claude` (claude judge/gen), `node`/`npx` (promptfoo substrate). Not
  bundled — documented requirements.
- **Invoke via `${CLAUDE_PLUGIN_ROOT}`:** the `/bench` subcommands call
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/..."` so they resolve from any working directory.
- **Hermetic generation config** (`hermetic_driver`, used only by the isolated-generation mode —
  NOT by `/bench verdict` or the native `/bench skill`): set `$SKILL_BENCH_CONFIG_DIR` to a clean
  credentials-only Claude config dir. The default is this repo's fallback and won't exist elsewhere.
- **Platform:** the hermetic CLAUDE.md-discovery behavior and `/bench trigger` are Linux/WSL-only
  (#170 hard-problem 4).
- **Method foundations** (pre-registration, empirical evals, description ablation) live in the
  **dev-skills plugin's** `building-skills` skill (ADR 0063 Call 2) — install dev-skills for the
  method depth; `/bench` itself runs without it.
- **Grading workflow:** `templates/grade.workflow.js` needs the Claude Code `Workflow` tool
  (#170 hard-problem 3); without it, grade serially via `claude -p` with the same prompts.

## Status
Runnable: `/bench` with `verdict` + `skill` + `trigger` subcommands (native substrate +
availability-aware cross-family judge with grok->claude fallback + deterministic cost accounting),
harness lib moved in (M1), config layer + consumer-layout test (M2), canonical templates
(`templates/`), #191 infrastructure-vs-quality hardening (ERROR cells, capture symmetry,
per-cell attribution), registered in the marketplace.

Install-portability proven at two levels: `consumer-layout.test.mjs` reproduces a verdict from a
copied-out layout at an unrelated cwd with NO CLIs (offline plumbing + math — CI-runnable); and a
manual live run re-graded from a `/tmp` install driving grok end-to-end (4 calls, 0 errors — not
CI-runnable, needs authenticated grok). Promptfoo generation is wired into
`/bench skill` (`--substrate promptfoo`, M4, proven live). See `docs/decisions/0055-*` and `0063-*`.
