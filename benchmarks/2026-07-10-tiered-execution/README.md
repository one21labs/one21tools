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
(`harness.workflow.js`'s `NEUTRAL_FRAME`) instructing them not to read files, search the repo, run
commands, or use any tools.

| Arm | Config |
|---|---|
| `sonnet-solo` | one agent call, model sonnet, answers directly from the prompt |
| `haiku-solo` | one agent call, model haiku, answers directly from the prompt |
| `tiered` | orchestrator (sonnet) writes a brief plan/spec -> worker (haiku) implements from the spec -> orchestrator (sonnet) validates against the ORIGINAL request -> may redispatch the worker ONCE with corrections (max 2 worker iterations). Final deliverable is always the worker's LAST output — the orchestrator never rewrites it, or the tier attribution would be contaminated. |

**Control (ADR 0023 scoping note, ADR 0027):** ADR 0023's hermeticity requirement binds the control
arm. The Workflow subagent may retain tool access, so hermeticity here is not tool-denial enforced by
the runner — it is ARM SYMMETRY: no skill content injected, an identical instruction not to use tools
in every prompt, and identical constraints across all 3 arms. `metadata.json:executor.arm_symmetry_control`
states this precisely.

## Implementation vehicle: harness.workflow.js

Issue #41's design needs the tiered arm's multi-step orchestrator/worker/validate control flow with a
conditional redispatch — that's a natural `pipeline()`/`agent()` shape, not a single `claude -p` call,
so (unlike prior benchmarks, which used `harness.sh` + `claude -p` for the executor) the EXECUTOR here
is `harness.workflow.js`, run by the Workflow tool. Every `agent()` call pins `model:` explicitly and
`effort:'medium'` (matching prior benchmarks' `CLAUDE_EFFORT=medium`) — `node scripts/check-workflow.mjs`
lints this.

`harness.workflow.js` takes `args = {arm, reps, evals}` and processes ONE arm's full grid
(24 evals x reps = 72 cells) per invocation — run it 3 times, once per arm.

## Cost/time capture (design compromise — read before trusting a cost number)

The Workflow runner has no `Date.now()` inside a workflow script, so wall-clock cannot be captured
per-cell, or even per-arm, from *inside* `harness.workflow.js`.

- **Tokens** ARE capturable in-workflow via `budget.spent()`, sampled once at the start and once at
  the end of each arm's whole pipeline run (`tokens_start`/`tokens_end` in the returned result). This
  is a **per-arm aggregate delta only** — `pipeline()` runs all 72 cells of an arm concurrently, so a
  per-cell token split is not attributable, and none is claimed. `budget.spent()`'s exact return shape
  is unverified in this repo (no prior `harness.workflow.js` used it); `costs.json:_shape` records
  what is actually observed on first use rather than assuming a shape in advance.
- **Wall-clock** is captured OUTSIDE the workflow: bracket each of the 3 per-arm Workflow invocations
  with a shell `date +%s.%N` immediately before and after, and record the difference in `timing.json`.

Both `costs.json` and `timing.json` ship as null-valued, operator-filled templates — not invented
numbers. `aggregate.py` reads them and leaves the cost/time verdict fields `null` if they are still
unfilled, rather than fabricating a ratio.

## Grading (blind + prosecutor, ADR 0019/0025)

Reuses the skills-hermetic grading pattern verbatim (adapted only in `meta.name`): `grade.workflow.js`
blind-grades each response against its eval's expectations (arm withheld) and runs an adversarial
prosecutor on every PASS; `prosecute_counts.workflow.js` runs a uniform adversarial re-count on EVERY
cell (ADR 0025 safeguard) so `met_final = min(grader_met, prosecutor_met)` for every cell, not just
binary passes. Grader is sonnet — the same tier as the sonnet-solo arm and the tiered orchestrator;
grader independence is unsolvable across only 2 model tiers (issue #41 owner call), accepted as the
same Claude-grades-Claude residual ADR 0019 already carries.

## Reproduce

```bash
python prep.py                                    # meta.json, cells.tsv, evals_args.json (24 evals, no treatment content)

# Executor: run harness.workflow.js once per arm via the Workflow tool. Bracket each invocation with
# `date +%s.%N` (before/after) and fill timing.json; fill costs.json from each result's tokens_start/
# tokens_end.
# Workflow harness.workflow.js {arm:"sonnet-solo", reps:3, evals:<evals_args.json>} -> outputs/sonnet-solo.json
# Workflow harness.workflow.js {arm:"haiku-solo",  reps:3, evals:<evals_args.json>} -> outputs/haiku-solo.json
# Workflow harness.workflow.js {arm:"tiered",      reps:3, evals:<evals_args.json>} -> outputs/tiered.json
#   (persist per benchmarks/lib/README.md: task .output "result" field)

python blind.py                                    # outputs/<arm>.json -> outputs/*.txt + graded/items/ (arm withheld) + arm_map.tsv

# Workflow grade.workflow.js            {itemsDir, bids} -> graded/verdicts.jsonl
# Workflow prosecute_counts.workflow.js {itemsDir, bids} -> graded/prosecute_counts.jsonl
#   (persist per benchmarks/lib/README.md: task .output "result" field; prosecutor evidence overrides)

python aggregate.py                                 # -> results.jsonl + the ADOPT/DO-NOT-ADOPT verdict
python archive_raw.py                               # once: outputs/all.tar.gz + the (skill,eval_id,arm) sample
```

## Validate before running for real

```
node scripts/check-workflow.mjs benchmarks/2026-07-10-tiered-execution   # syntax + model: on every agent() call
python -m py_compile prep.py blind.py aggregate.py archive_raw.py
python prep.py                                                            # offline; generates meta.json/cells.tsv/evals_args.json
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
