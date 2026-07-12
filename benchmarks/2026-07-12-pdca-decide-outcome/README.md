# /decide three-arm outcome benchmark — 2026-07-12 (issue #172, Instrument 2; ADR 0052)

Does the full `/decide` panel produce better decisions than the same model given the same
token budget WITHOUT structure? Pre-registered per ADR 0042 / `pre-registration.md`;
methodology inherited: ADR 0019 (eval-clustered CI), 0023 (hermetic control + recorded
nulls), 0025 (fraction-met, `met_final = min(grader, prosecutor)`), 0026 (artifact formats),
0041 (scaffold from `benchmarks/lib`; dated dirs append-only, `empirical-evals.md:159`).
**This directory is a pre-registration only — no run executed.** Order per ADR 0052
decision 2: plumbing pilot -> Instrument 1 grid -> this cost-pilot -> this grid.

## Prior art (ADR 0042 prior-art rule; survey: `prior-art.md`)

Compute-matched comparisons on verifiable tasks predict structure ~ budget (MAD fails to
beat self-consistency at matched compute: arXiv:2311.17371, 2502.08788, 2406.06461). The
open-ended-judgment regime is unpublished — this benchmark tests the open regime, and a
C~B result REPLICATES prior art (routed to its own `/decide` per ADR 0052), not a failure.

## Question and pre-registered bar

**KEEP condition (`metadata.json:bar`): mean_delta(fraction_met_C - fraction_met_B) > 0**,
clustered by scenario (8 clusters), 95% CI reported as confidence signal (strong if lower
bound > 0, weak otherwise) — directional bar per the ADR 0027 / tiered-fullgrid precedent.
C vs A is reported for context, never the KEEP basis: **C > A with C ~ B means the plugin
buys tokens, not structure** — recorded honestly. Verdict via `lib/verdict.py:verdict_of`.

Cost (ADR 0052 decision 3, HARD stop): cost-pilot = 2-3 arm-C cells on scenario B1
(pilot cap ~$6); then `python3 ../lib/cost_gate.py --cells 72 --pilot-cost-usd <measured...>
--ceiling-usd 40` — nonzero exit halts the grid, the pilot is recorded, scope goes to a
fresh `/decide`. The pilot must also show the deny-list carve-out HIT and RESOLVED with
isolation preserved (ADR 0052's weakest assumption; `hermetic_driver.py:31-32`).

## Arms (3), same scenarios, same model tier

| Arm | Config |
|---|---|
| A (bare) | scenario + "Decide this and record your decision with rationale." |
| B (cost-matched unstructured) | A's prompt + "Deliberate thoroughly: consider multiple perspectives, argue against yourself, then decide and record rationale." Token budget set to arm C's median observed spend from the cost-pilot (recorded in `metadata.json` before the grid). No roles, no structure. |
| C (full /decide) | pdca-workflow plugin loaded, panel runs per `decide/SKILL.md`; subagent spawning allowed for this arm only — the pre-registered hermetic deviation, pilot-gated (ADR 0052 decision 2). |

Arm symmetry otherwise (ADR 0023): same scenario context files, same cwd, same base model.
**Cells: 8 scenarios x 3 arms x 3 reps = 72** (the issue's "~10 scenarios / ~90 cells"
resolved down: the repo's squashed root left only 4 uncontaminated backtests — see
Scenarios — and padding the corpus with weaker ones was rejected).

## Scenarios (8; specs in `scenarios.json`, reconstruction at build)

**Backtests (B1-B4)** — real past judgment calls with known outcomes; context = the repo
snapshot at the pre-decision parent commit + the outcome-free issue/memo text; per-scenario
deny list keeps `docs/decisions/` and every outcome artifact out. All post-date the model
cutoff (contamination note per scenario in `scenarios.json`):

- **B1** tiered-execution adoption (issue #41 at `f6b9b38`): outcome DO-NOT-ADOPT, 2.94x
  tokens. Broken assumption: plan+validate overhead < cheap-worker savings.
- **B2** full-grid vs pilot-and-stop (same reconstruction point): outcome ~90% wasted spend
  past a decidable gate. Broken assumption: full-grid needed for a valid verdict.
- **B3** prose-vs-mechanize sync rule (issue #106 memo at `405be20`): outcome: a sibling
  coordination class (merge-skew) broke main ~18h later. Assumption tested: prose is the
  right surface now.
- **B4** haiku routing-escalation adoption (issue #109 at `3ae165c`): outcome DO-NOT-ADOPT,
  1.04-1.33x cost, ~75% escalation. Broken assumption: enough haiku-shippable tasks.

**Synthetic consumer-shaped (S1-S4)** — each with one planted trap and pre-registered
expectations (ADR 0049's representativeness concern):

- **S1** free-tier pricing threshold; trap: sunk-cost bait (metering already built for the
  higher limit).
- **S2** monolith-to-services migration scope; trap: unverifiable premise ("users demand
  microservices", no evidence in context).
- **S3** workflow-engine adoption for one cron job; trap: gold-plating bait.
- **S4** API-version sunset timing; trap: loud-minority anecdote vs 0.4% usage metrics.

Rejected scenario: the #41 metric-choice call (binary vs fraction-met) — MEDIUM
contamination (squashed-root ordering ambiguity); recorded here, not padded in.

## Rubric (per cell, fraction-met; grader then prosecutor, ADR 0025)

1. Enumerates >=2 real options incl. a rejected alternative with a reason.
2. States a falsifiable acceptance/reopen criterion.
3. Surfaces the load-bearing assumption — objective key for backtests: THE assumption that
   actually broke (or held), per `scenarios.json`.
4. Synthetic only: handles the planted trap (doesn't anchor on sunk cost / adopt the
   unverifiable premise / gold-plate / cave to anecdote).
5. Backtest only: anticipates the failure class that actually occurred (strongest signal).

So every cell has 4 scorable expectations. Circularity guard: the real ADRs were
plugin-produced, so rubric keys are OUTCOME FACTS (what broke/held), never similarity to
the shipped ADR text.

## Grading pipeline

1. Normalize every artifact through `lib/blind.py`'s neutral schema (decision / options /
   criterion / risks / assumptions) — ADR-formatted output is an arm-tell (ADR 0052
   decision 4: lib home, imported, not copy #10).
2. Blind grade against the rubric; prosecutor re-judges every met claim;
   `met_final = min(grader, prosecutor)`.
3. Guess-the-arm audit on 9 sampled normalized cells (`2026-07-08-grading-bias-audit/`
   precedent); accuracy significantly above 0.5 -> ADR 0052 revisit trigger (schema-rewrite
   blinding is itself unvalidated in prior art — named residual).
4. Aggregate per ADR 0019 (cluster = scenario); raw sampled + archived per
   `lib/bench_io.py:sample_and_archive_raw`.

## Cost-pilot result (run 2026-07-12 — GRID HALTED by the gate; outputs deleted as contaminated, see `DELETED-CONTAMINATED.md`; numeric costs in `metadata.json`)

Three arm-C cells on B1, $10.10 total (overshot the ~$6 cap by one cell — a cell's cost is
unknowable until it completes; the runner stops the NEXT cell, recorded honestly):

- **r1/r2 ($0.62, $0.41): stalled on two plumbing defects, both fixed for the record.**
  (1) `build_b1.py` deleted `docs/decisions` from the working tree only — the nested
  `/decide`'s Inherit step saw 34 deleted-in-worktree files and asked permission to
  `git restore` them: the deny was a LEAK, not a guard. Fix: the removal is now committed in
  the snapshot. (2) Nested `-p` sessions deny file writes by default — the panel could not
  write its ADR. Fix: `--permission-mode acceptEdits` (bypassPermissions is refused under
  root; the deny-list binds regardless of permission mode).
- **r3 ($9.07): the full panel RAN under the hermetic driver** — plugin loaded via
  `--plugin-dir`, advisors + pm spawned, a decision produced (it chose pilot-first sequencing
  and flagged its inability to write files — consistent with defect 2).
- **Gate verdict: OVER, decisively.** `cost_gate --cells 72 --pilot-cost-usd 9.0739
  --ceiling-usd 40` -> projected **$653** (faithful cell) or **$242** (all-three mean) vs
  **$40** — exit 1, grid halted per ADR 0052's revisit trigger. The trigger routes to a
  fresh `/decide`; at ~6x the ceiling this is an owner spend/scope call, not a parameter
  fix. Options recorded on issue #172. No grid cell has run; the pre-registered design
  stays frozen pending that decision.

## Threats to validity (pre-registered)

- Blinding leakage (audited, above); arm C's multi-agent transcript length may leak through
  content richness even post-normalization — audit specifically checks this.
- Backtest circularity (outcome-keyed rubric, above); hindsight leakage guarded by
  parent-commit snapshots + per-scenario deny lists (recipe: arXiv:2402.18563).
- n=3 reps, 8 clusters: CI will be wide; confidence language pre-committed.
- Author-written scenarios (ADR 0052 [unverifiable]; REOPEN-IF a consumer diverges).
- B's budget match is median-based; arm C's spend variance is a pilot output, recorded
  before the grid.
