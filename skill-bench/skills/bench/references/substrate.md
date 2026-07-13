# Substrate — the generation runner

The `skill` subcommand generates each eval task under two arms (skill-loaded, bare). That generation
is a commodity, so it is rented; the causal + grading layer on top is what the plugin owns. Pick the
runner with `--substrate`.

## native (default)

A zero-dependency thread pool that shells each arm command per task, passing the task as the final
CLI argument. It unwraps a CLI JSON envelope (claude `result`, grok `text`, schema `structuredOutput`)
to the produced text. Use it when you want the fewest moving parts and no external tooling.

## promptfoo

Wraps the promptfoo matrix runner (fetched via `npx` on demand, or `$SKILL_BENCH_PROMPTFOO_BIN`).
promptfoo is a declarative harness: it takes prompts, providers, and test rows, runs the product,
and reports per-cell results with caching, a web viewer, and CI gating. Here it is used ONLY for the
execution matrix — each arm becomes an `exec` provider driving the same grok/claude CLI. Its own
assertion graders are bypassed, because this plugin's cross-family judge, prosecutor, and verdict
math replace them. So promptfoo buys observability, dataset/config versioning, and CI regression
gating — not the grading. Reach for it when a consumer already runs promptfoo or wants those.

Version note: promptfoo's `exec` provider passes the rendered prompt as the first argument and a
context object as the second, so each arm is fronted by a generated shim that forwards only the
prompt. This is handled in the adapter; a promptfoo version bump surfaces as a failing adapter test,
not silent drift.

## Arm symmetry (both runners)

The with-arm and without-arm commands must differ ONLY in whether the skill is loaded — same model,
same flags, same everything else. Otherwise the with-without delta measures the wrong thing. Both
runners execute the two arms under identical conditions.

## Portability

Scripts are invoked via `${CLAUDE_PLUGIN_ROOT}` so they resolve from any working directory when the
plugin is installed elsewhere. The consumer supplies the CLIs (grok/claude and, for promptfoo,
node/npx), authenticated. The hermetic isolated-generation mode honors `$SKILL_BENCH_CONFIG_DIR` for
a clean credentials-only config, and its CLAUDE.md-discovery behavior is Linux/WSL-only.
