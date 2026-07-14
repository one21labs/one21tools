# /decide poker-round benchmark — 2026-07-14 (issue #185; ADR 0061 operationalization)

Does a planning-poker/Delphi round — independent numeric estimation, mechanical reveal, a
convergence round fired only on divergence — change panel decision quality, cost, and
consistency in the pre-registered directions, against the full panel run fresh in the same
run? It may equally degrade quality (structured scoring flattening the argued dialectic),
save nothing (round 2 firing often), or add variance (round-2 anchoring) — a null on any bar
is a recorded, fully acceptable outcome. Methodology inherited, not restated: ADR 0019
(cluster CI), 0023 (arm symmetry, recorded nulls), 0025 (fraction-met, min(grader,
prosecutor)), 0026 (artifacts), 0052 (cost-gate hard stop), 0057 d2 (dual-judge headline),
0059 (neutral framing), 0061 (every call below). Scenarios REUSED read-only a third time
from the frozen `../2026-07-12-pdca-decide-outcome/` (staleness owner-named, unmeasured —
threat, not blocker, ADR 0061 2g).

**This README is the pre-registration — committed before any cell spend. Exact prompts are
FROZEN as the constants in `grid_poker.py` at this commit; edits land only through a
recorded pre-verdict amendment, never mid-grid.**

## Arms (3), same 8 scenarios, 3 reps = 72 cells, all sonnet (I2 tier held; ADR 0061 2g)

| Arm | Config |
|---|---|
| A (bare floor) | I2's arm A verbatim; fresh re-run (same-run rule, ADR 0061 2c). |
| C (full /decide) | I2's arm C verbatim: plugin via `--plugin-dir`, panel agents, fresh re-run. |
| P (poker) | Steps below; every call sonnet; every sub-call in its OWN fresh bundle copy (advisor independence is the property under test — a shared workdir with Write allowed could leak one advisor's artifacts to another). |

**Arm P per cell (issue #185 protocol + ADR 0061):**
0. FRAMER — one call per SCENARIO (not per rep, ADR 0061 2a), enumerates 2-4 options,
   neutral labels + summaries only, no evaluation/ranking; cached in `framers.json` and
   shared by all P cells of that scenario.
1. Three ADVISORS — fresh, unprimed, parallel, each in its own bundle copy: per option
   {score 1-5, one-line crux, THE reversing dependency}, strict JSON, one full retry on
   parse failure; fewer than 2 usable advisors = ERROR cell (not arm P; armd probe-floor
   precedent).
2. Mechanical REVEAL — per-option REVEAL SPREAD = max−min of round-1 scores (P-internal
   only; never a P-vs-C metric, ADR 0061 2f).
3. ROUND 2 — only for options with reveal spread >= 2: each usable advisor sees its own
   round-1 estimates + the anonymized all-advisor table + cruxes for the divergent options
   and re-estimates ONLY those, once. No anti-herding coaching in the prompt — the audit
   measures herding, coaching would mask it. Round-2 parse failure keeps that advisor's
   round-1 scores (recorded).
4. DECIDER — receives the final anonymized table (final scores, cruxes, dependencies;
   round-2 options marked) + arm A's exact decide-and-record suffix. No DoD check in step 4
   (#186 has not survived its own test; the issues gate that composition on both surviving
   independently).

## Pre-registered bars (issue #185: ALL FOUR must hold or H1 is falsified; any miss ->
recorded null, no adoption)

a. **Hard pair (exps 3+4), cluster mean over all 8 scenarios: mean_P >= mean_C − 0.05.**
b. **Cost: mean per-cell cost_P <= 0.7 x mean per-cell cost_C** (same-run; P cell cost =
   advisors + round-2 + decider + framer/3 amortized across the scenario's reps).
c. **Consistency (OUTCOME SPREAD, ADR 0061 2f): per-scenario max−min of the 3 reps' full
   fraction-met, averaged over 8 scenarios; P <= C.**
d. **Full fraction-met, cluster mean: mean_P >= mean_C − 0.05.**

Deltas with 95% cluster-t CIs (8 clusters, df=7); directional point-estimate bars, CI as
confidence language. P−A context only. **MDE stated (ADR 0061 2b): at 3 reps the measured
cluster-CI half-widths are ~0.09 (full) and ~0.17 (hard pair) — bars a/d's 0.05 margin is
INSIDE the noise band; 8 clusters cannot resolve a 0.05 miss with confidence, so bar
outcomes carry weak/strong language, never false precision.** REOPEN-IF (ADR 0061): pilot P
variance exceeds C's — recompute MDE before the grid.

**Judge policy (ADR 0057 d2, binding):** dual-judge headline — the committed opus pipeline
(grade -> prosecutor -> min) AND a grok-4.5 re-grade of the same blinded cells
(`skill-bench/scripts/bench_verdict.py --judge both`). Bars evaluated on opus; judge
DISAGREEMENT on any bar's pass/fail = bar NOT MET. Never averaged.

**Herding audit (pre-registered, ADR 0061 2e):** mechanical — per-advisor round-1 -> round-2
deltas from the cell records; report the round-2 fire rate, the fraction of re-estimates
moving TOWARD the round-1 mean, and per-advisor convergence asymmetry. Plus transcript
sampling focused on hard-pair scenarios. Round-2 anchoring is the owner-named Delphi failure
mode; the audit turns it into evidence, not narrative.

## Cost (ADR 0052 hard stop; ADR 0061 2d)

Pilot: 3 arm-P cells on B1 (framer + 3 reps), cap **$10** — stops the NEXT cell past cap.
Then `cost_gate.py --cells 72 --pilot-cost-usd <A> <C> <P-pilot-mean> --ceiling-usd 150`
with A $0.564 / C $4.052 (armd MEASURED means, `../2026-07-13-pdca-decide-armd/results.json`;
same config + scenarios — the pilot does not re-price them). Nonzero exit halts, recorded,
fresh scope decision (ADR 0061 revisit trigger: also fires if the pilot's round-2 rate
threatens bar b). Runtime backstop: cumulative spend > ceiling halts resumable.

## Grading pipeline (I2's, blinding-audited there; A/C/P enum)

1. `blind_cells_poker.py` -> `graded/items/` neutral records (framer/advisor/round-2
   artifacts are cell INPUTS, never included; cell-written .md captured for every arm),
   arm_map, keys from frozen I2 `scenarios.json`, 9 audit bids (3/arm, rep-1).
2. Opus workflow `grade_poker.workflow.js`: grade -> prosecutor -> min -> 3-way
   guess-the-arm audit (leak bar >= 7/9). 3. Grok re-grade per judge policy.
4. `aggregate_poker.py`: four bars, cluster CIs, spreads, herding metrics -> `results.json`.

## Results (verdict — 2026-07-14; `results.json`, `grok-regrade.json`)

**Verdict: H1 FALSIFIED, judge-ROBUST — no adoption; the panel stays (ADR 0057 d1).**
Three of four bars miss under BOTH judges (judge split empty): (a) hard pair P−C −0.104
[−0.411, +0.202]; (c) OUTCOME SPREAD P 0.281 vs C 0.063 — the consistency claim inverted:
numeric scoring ADDED rep-to-rep variance; (d) full P−C −0.125 [−0.366, +0.116] opus /
−0.135 [−0.331, +0.060] grok. CIs straddle zero (the stated MDE said they would); the bar
set decides on agreed directional misses, reported weak. (b) cost passes decisively:
P $0.920 vs C $3.211 = 0.29x. Judge agreement 0.819, kappa 0.593.

- Texture: P ~ C on backtests (exp-4 0.417 vs 0.333; B2 +0.25) and collapses on the
  synthetic traps (S1 −0.75 — P anchored on the sunk-cost bait C refused; P synthetic
  per-exp 0.67-0.75, BELOW bare A's 0.83-1.0, C at 1.0). H1's own named alternative —
  structured scoring flattens the argued dialectic — is the observed mechanism.
- Herding audit: round 2 fired 4/24 (conditional as designed); toward-mean share 0.41
  (7 toward / 4 away / 6 kept) — no strong anchoring. The economics held; quality did not.
- Audit 4/9 = chance, blinding held. Cost ledger: grid $111.21 + pilot $3.61 executor;
  grading 225 opus-workflow agents (~4.7M tokens) + grok re-grade 144 calls ($8.52 notional).
- EXPLORATORY (`exploratory-crossrun.json`, post-hoc): three same-config runs per arm now
  exist. C's cross-run scenario spread 0.187 ~ A's 0.167 — the panel does NOT damp
  run-to-run variance; C's synthetics ran 0.834 -> 1.0 -> 1.0 (I2's all-traps loss is the
  outlier of three). Bare-arm means flat across the three scenario reuses — the staleness
  threat did not materialize (one note: B1's bare arm drifted 0.417 -> 0.583 -> 0.833).

## Threats to validity (pre-registered)

- Author-written poker prompts (the thing under test; frozen at this commit — same residual
  as #180). - Third scenario reuse (owner-named; backtest ground truth is the offsetting
  asset). - Round-2 anchoring (audited mechanically, above). - n=3 reps / 8 clusters: wide
  CIs, weak/strong language pre-committed. - Framer as shared context: options-only, no
  evaluation; advisors stay independent GIVEN the option set (the Delphi questionnaire
  shape) — framer text sampled in the audit for evaluative leakage. - Judge disagreement
  can only make bars HARDER (conservative).
