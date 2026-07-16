# Description Ablation — measuring whether a description triggers

Read this when testing whether a skill's DESCRIPTION activates Claude to load it — out of scope
for [empirical-evals.md](empirical-evals.md) (see its "Scope and limits").

## The two surfaces

Complementary, not alternatives — a single run cannot answer both:

| Surface | Loaded | Question | Instrument |
|---|---|---|---|
| description (frontmatter) | always, every session | Does it trigger? | this reference |
| body + references | on-demand, once triggered | Does the content earn its cost? | [empirical-evals.md](empirical-evals.md) |

A description that never triggers makes the body's content moot; a body that never earns its
cost makes triggering moot. Measure separately.

## The instrument

The skill-bench plugin's `scripts/run_eval.py` (`/bench trigger`) — vendored from
anthropics/skills' skill-creator with 4 correctness fixes (3 stream patches + timeout-as-null)
plus a testability extraction (ADR 0033); `run_eval_test.py` guards the fixed detection and
aggregation logic. Linux/WSL-only (`select.select()` on a subprocess pipe fd).

## Validity: absolute rates are NEVER reportable

Only matched-protocol A/B deltas are. An absolute trigger rate is bound to its field and load:

- **Competitive field.** A nested `claude -p` session inherits the container's built-in skills
  (and any installed marketplace plugins) alongside the planted variant — an organic query can
  fire a REAL skill instead of, or as well as, the planted one. A live run had an installed
  dev-skills plugin shadow the planted variant and zero every cell, until `CLAUDE_CONFIG_DIR`
  was pinned clean (dated evidence:
  one21labs/one21tools:benchmarks/2026-07-07-toolkit-grid/trigger-kit/FINDINGS.md).
- **Worker-count collapse.** Concurrent workers plant same-description command files in the
  SHARED project root; the model sees N near-identical planted skills and invokes at most one,
  so rates collapse toward 1/N. `--num-workers 1` is therefore MANDATORY, not a tuning choice.
- **Timeout scoring.** Under load, a genuine trigger's stream event can arrive after the
  query's clock expires. The runner records a timeout as null — excluded from the rate's
  denominator and from pass/fail, surfaced as a `timeouts` count — never a False. Treat any
  run with `timeouts > 0` as SUSPECT (something contended for the machine); prefer re-running
  to reading around it.

A delta is readable only when control and variant are PAIRED under equal load — same eval
set, same serial protocol, same machine, no concurrent heavy benchmark load. Never report an
absolute rate, and never compare rates across different runs, fields, or environments.

## Run protocol

1. WSL only.
2. Pin `CLAUDE_CONFIG_DIR` to an empty dir seeded with only `.credentials.json` (auth, nothing
   else) — no installed plugins, no cached session state, so the run isn't shadowed. Same
   hermetic-executor requirement as empirical-evals.md:158; this is its trigger-runner instance.
3. A scratch project root with an empty `.claude/` — the runner writes its own command file
   under `.claude/commands/<clean-name>.md` per query; nothing pre-existing should compete.
4. Eval set: a flat JSON array, `{"query": str, "should_trigger": bool}` per item — not
   skill-creator's nested `should_fire`/`should_not_fire` authoring format; convert before
   feeding the runner.
5. Invocation:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/run_eval.py" --eval-set <path> --skill-path <skill-dir> \
     --model <pinned-model> --num-workers 1 --timeout 240 \
     [--description "<variant text>"]
   ```
   `--model` pinned — never the ambient default (deltas are model-relative). `--num-workers 1`
   is MANDATORY (worker-count collapse, above); `--timeout 240` absorbs serial-run latency.
   `--description` overrides the on-disk description to test a variant without editing SKILL.md.
6. Pair under equal load: run control and variant back-to-back, same serial protocol, same
   machine, no concurrent heavy load; a run with `timeouts > 0` is suspect (see Validity).

## Verdict rule

Keep the SHORTEST description that holds the true-positive rate without raising the
false-positive rate — a longer description that buys no additional trigger accuracy is pure
context cost (the same "every char earns its place" bar as the building-skills skill's
section-ablation.md, dev-skills plugin). Run 1 replicate per query first; escalate to 3
replicates ONLY for a query whose pass/fail flips between candidate descriptions — the
sequential-escalation discipline (ADR 0019), applied here to ambiguous flips instead of CI width.

## Result snapshots

Append a dated, machine-readable `.jsonl` under `benchmarks/<date>/` per run — one record per
(description variant, query): query, should_trigger, trigger_rate, timeouts, pass — plus a
`metadata.json` (skill, variant text, model, num-workers, timeout, `CLAUDE_CONFIG_DIR` pinned
y/n). Same append-only, never-edited convention as empirical-evals.md's snapshots (ADR 0019): a
run is a measurement record as of its date, not current truth.
