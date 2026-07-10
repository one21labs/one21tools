# Tiered-agent execution benchmark — 2026-07-10 (issue #41)

Does a tiered configuration (sonnet plans + validates, haiku implements, <=2 worker iterations)
match sonnet-solo quality at materially lower cost or time? Pre-registered per ADR 0024 (do not
adopt on assertion); methodology: ADR 0019 (eval-clustered CI), ADR 0023 (hermetic control-arm
scoping), ADR 0025 (fraction-met headline metric), ADR 0027 (directional adoption bar precedent).
**This directory is a pre-registration + harness only — no run has been executed.**

## Question and pre-registered adoption bar

Adopt the tiered configuration only if BOTH clear, pre-registered before any run
(`metadata.json:adoption_bar`):

1. **Quality non-inferior:** `mean_delta(tiered - sonnet-solo) > -0.05` on fraction-met, eval-clustered
   (point estimate over the 24 evals). The 95% CI on the delta is reported as a secondary confidence
   signal (strong if its lower bound also clears -0.05, weak otherwise) — **not a gate**. A CI-exclusion
   bar is not reliably achievable at n=24 clustered evals for a -0.05 margin (ADR-0027-style rationale:
   the EP re-measure used the same directional-not-CI-exclusion reasoning at n=6).
2. **Materially cheaper:** `tokens_tiered <= 0.6 * tokens_sonnet-solo` OR `time_tiered <= 0.6 *
   time_sonnet-solo`.

`haiku-solo` vs `sonnet-solo` is measured and reported for context (the cost/quality floor) but does
not gate the tiered adoption decision. The result is recorded either way (ADR 0024, append-only) —
not fabricated, not withheld on a null.

## Arms (3), same 24-eval battery, no treatment content

Reuses the 24-eval battery (4 skills x 6 evals: code-standards, engineering-principles,
building-skills, optimizing-context) via `prep.py`, exactly as
`benchmarks/2026-07-08-skills-hermetic/prep.py` does. **No skill content is injected in any arm** —
the 3 arms differ only by EXECUTOR CONFIGURATION, all get the identical neutral framing
(`harness.py`'s `NEUTRAL_FRAME`) instructing them not to read files, search the repo, run commands,
or use any tools.

| Arm | Config |
|---|---|
| `sonnet-solo` | one agent call, model sonnet, answers directly from the prompt |
| `haiku-solo` | one agent call, model haiku, answers directly from the prompt |
| `tiered` | orchestrator (sonnet) writes a brief plan/spec -> worker (haiku) implements from the spec -> orchestrator (sonnet) validates against the ORIGINAL request -> may redispatch the worker ONCE with corrections (max 2 worker iterations). Final deliverable is always the worker's LAST output — the orchestrator never rewrites it, or the tier attribution would be contaminated. |

**Control (ADR 0023, ADR 0027):** ADR 0023's hermeticity requirement binds the control arm.
`harness.py`'s executor enforces this two ways at once, unlike the original Workflow-subagent
design: (1) real tool denial — `--disallowedTools` on every `claude -p` call, not a convention the
runner merely trusts; and (2) ARM SYMMETRY — no skill content injected, an identical
not-to-use-tools instruction in every prompt, and identical constraints across all 3 arms
(`metadata.json:executor.arm_symmetry_control` states this precisely). Both apply identically to
every arm.

## Executor: harness.py (claude -p driver) — why this replaced harness.workflow.js

The executor was originally authored as `harness.workflow.js` (run by the Workflow tool), because
the tiered arm's orchestrator/worker/validate control flow with conditional redispatch is a natural
`pipeline()`/`agent()` shape. That executor is **superseded and deleted**: the Workflow runner could
only capture per-ARM aggregate tokens (`budget.spent()`, sampled at pipeline start/end — no per-cell
split, since `pipeline()` runs all 72 cells concurrently) and had no `Date.now()` inside a workflow
script at all, so wall-clock had to be bracketed OUTSIDE the workflow and hand-copied into a
`timing.json` template. Both `costs.json` and `timing.json` shipped as null-valued, never-filled
templates. Returning 72 full response texts through the session to persist them also risked context
flooding.

The executor is now **`harness.py`** (Python stdlib only), a hermetic `claude -p` driver in the
`benchmarks/2026-07-08-skills-hermetic/harness.sh` lineage (ADR 0023) rather than the Workflow
runner: it writes each cell's output directly to disk, and `claude -p --output-format json`'s result
envelope (`duration_ms`, `duration_api_ms`, `total_cost_usd`, `usage`) gives REAL per-cell tokens and
duration — not a per-arm aggregate. `--disallowedTools` gives true tool denial (the Workflow
subagent could only be tool-denied by convention, not enforced — see the ADR 0023 scoping note
below, now superseded by this executor for the tiered arm; `grade.workflow.js` /
`prosecute_counts.workflow.js` still run via the Workflow tool because their verdict records are
small and don't need per-cell wall-clock).

`grade.workflow.js` and `prosecute_counts.workflow.js` are unchanged — they only ever handled small
verdict records, not full response text or per-cell timing, so the Workflow-runner limitations above
never applied to them.

`harness.py` is designed to run **inside WSL Debian** (invoked from Windows as
`wsl -d Debian -- python3 /mnt/c/.../harness.py --arm <arm>`), because the pre-provisioned hermetic
`CLAUDE_CONFIG_DIR` (`$HOME/issue30/claude-config` — clean config, no plugins, credentials only)
already exists there. It processes ONE arm's full grid (24 evals x reps = 72 cells by default) per
invocation — run it 3 times, once per arm.

## Cost/time capture — real per-cell numbers, not an estimate

Because the executor is now a plain subprocess call per cell (not a Workflow pipeline), `harness.py`
measures wall-clock directly (`time.monotonic()` around each `claude -p` call) and parses the real
`usage`/`total_cost_usd`/`duration_ms`/`duration_api_ms` fields from `claude -p --output-format
json`'s result envelope for every call — no aggregate-only compromise, no operator-filled template.
Each cell's full breakdown (per-call usage, cost, durations; for `tiered`, `plan`/`worker1`/
`validate1`/`worker2` individually) is written to `<outdir>/cells/<arm>.<skill>.<eval_id>.r<rep>.json`;
each arm's totals are written to `<outdir>/<arm>.summary.json`
(`{arm, cells, failures, total_tokens_in, total_tokens_out, total_cost_usd, wall_clock_s,
per_call_parallelism}`). `aggregate.py` reads the three `<arm>.summary.json` files for the cost/time
gate — `costs.json` and `timing.json` are deleted, along with their operator-filled-template
convention.

**Hermeticity note (found while building the driver, not assumed):** `CLAUDE_CONFIG_DIR` only
redirects Claude Code's *global* config/plugin discovery — it does not stop project-level `CLAUDE.md`
auto-discovery by `cwd` traversal. A `claude -p` call issued from this repo's checkout pulled in this
repo's `CLAUDE.md` and opened every response with unsolicited "I've reviewed the project
instructions..." narration (~17K extra cached tokens, ~6x the wall-clock of the same call from a
neutral directory). `harness.py` therefore runs every `claude -p` call from an empty scratch
directory (`<outdir>/cwd`, outside the repo checkout) — the same purpose `harness.sh`'s `$EMPTY`
served for the skills-hermetic benchmark, just via a plain subprocess `cwd=` instead of `cd`.

## Grading (blind + prosecutor, ADR 0019/0025)

Reuses the skills-hermetic grading pattern verbatim (adapted only in `meta.name`): `grade.workflow.js`
blind-grades each response against its eval's expectations (arm withheld) and runs an adversarial
prosecutor on every PASS; `prosecute_counts.workflow.js` runs a uniform adversarial re-count on EVERY
cell (ADR 0025 safeguard) so `met_final = min(grader_met, prosecutor_met)` for every cell, not just
binary passes. Grader is sonnet — the same tier as the sonnet-solo arm and the tiered orchestrator;
grader independence is unsolvable across only 2 model tiers (issue #41 owner call), accepted as the
same Claude-grades-Claude residual ADR 0019 already carries.

## Reproduce

Pipeline: `prep.py` -> `harness.py` per arm (inside WSL) -> `blind.py` -> `grade.workflow.js` ->
`prosecute_counts.workflow.js` -> `aggregate.py` -> `archive_raw.py`. Separately,
`run_mechanized.py` regenerates `graded/mechanized.csv` (the structural-check column) from
`outputs/cells/` via `benchmarks/lib/mechanized_checks.py` (tested: `mechanized_checks_test.py`).

```bash
python prep.py                                    # meta.json, cells.tsv, evals_args.json (24 evals, no treatment content)

# Executor: run harness.py once per arm, inside WSL Debian, from Windows. Each invocation writes
# <outdir>/cells/<arm>.<skill>.<eval_id>.r<rep>.json (72 files) and <outdir>/<arm>.summary.json.
# --outdir defaults to ~/tiered-run (WSL-native, fast I/O); override to a /mnt/c/... path if you'd
# rather have the driver write directly into this benchmark directory.
wsl -d Debian -- python3 /mnt/c/Users/ajmcc/projects/one21tools/benchmarks/2026-07-10-tiered-execution-fullgrid/harness.py --arm sonnet-solo
wsl -d Debian -- python3 /mnt/c/Users/ajmcc/projects/one21tools/benchmarks/2026-07-10-tiered-execution-fullgrid/harness.py --arm haiku-solo
wsl -d Debian -- python3 /mnt/c/Users/ajmcc/projects/one21tools/benchmarks/2026-07-10-tiered-execution-fullgrid/harness.py --arm tiered

# Copy each arm's cells/ and its <arm>.summary.json from the WSL outdir into this benchmark
# directory (WSL is reachable from Windows at \\wsl.localhost\Debian\home\<user>\tiered-run\...).
# Example, from PowerShell, for each arm:
#   robocopy \\wsl.localhost\Debian\home\<user>\tiered-run\cells outputs\cells /XF *.err
#   copy \\wsl.localhost\Debian\home\<user>\tiered-run\<arm>.summary.json .

python blind.py                                    # outputs/cells/*.json -> outputs/*.txt + graded/items/ (arm withheld) + arm_map.tsv

# Workflow grade.workflow.js            {itemsDir, bids} -> graded/verdicts.jsonl
# Workflow prosecute_counts.workflow.js {itemsDir, bids} -> graded/prosecute_counts.jsonl
#   (persist per benchmarks/lib/README.md: task .output "result" field; prosecutor evidence overrides)

python aggregate.py                                 # reads the three <arm>.summary.json -> results.jsonl + the ADOPT/DO-NOT-ADOPT verdict
python archive_raw.py                               # once: outputs/all.tar.gz + the (skill,eval_id,arm) sample
```

## Validate before running for real

```
node scripts/check-workflow.mjs benchmarks/2026-07-10-tiered-execution   # syntax + model: on grade/prosecute_counts (2 workflow files)
python -m py_compile harness.py prep.py blind.py aggregate.py archive_raw.py
python prep.py                                                            # offline; generates meta.json/cells.tsv/evals_args.json
python harness.py --help
python harness.py --arm tiered --dry-run                                  # lists the 72 cells for an arm, no claude calls
wsl -d Debian -- python3 /mnt/c/Users/ajmcc/projects/one21tools/benchmarks/2026-07-10-tiered-execution-fullgrid/harness.py --arm sonnet-solo --dry-run
```

## Design decisions carried over from precedent

- **24-eval battery reused exactly, no new evals authored** — same skills, same expectations, only
  the executor configuration is under test (per the accepted scoping for this run).
- **Fraction-met, not binary pass, is the headline metric** (ADR 0025) — the binary metric floors on
  hard multi-expectation evals in this same battery (`benchmarks/2026-07-08-skills-hermetic/README.md`).
- **CSV/TSV for flat records, minified JSONL for prose-bearing records** (ADR 0026) —
  `graded/arm_map.tsv` vs `graded/verdicts.jsonl`/`prosecute_counts.jsonl`.
- **`benchmarks/lib` reused, not reimplemented** — `verdict.py`'s shared `verdict_of` is not used here
  (the adoption bar is a directional margin + cost gate, not the KEEP/HARMFUL/CUT-CANDIDATE rule) but
  `bench_io.sample_and_archive_raw` is (`archive_raw.py`).
