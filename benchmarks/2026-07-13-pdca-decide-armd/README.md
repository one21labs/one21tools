# /decide arm-D outcome benchmark — 2026-07-13 (issue #180; ADR 0057 routing, ADR 0024 loop)

Does the trimmed shape — one accountable decider + independent pointed probes (arm D) —
preserve the full panel's one measured edge (failure anticipation, exp-4) and clear the
shared assumption-surfacing headroom (exp-3) at a fraction of the panel's cost?
Pre-registered per ADR 0042; methodology inherited, not restated: ADR 0019 (eval-clustered
CI), 0023 (arm symmetry, recorded nulls), 0025 (fraction-met, `met_final = min(grader,
prosecutor)`), 0026 (artifact formats), 0041 (scaffold from the shared lib — now
`skill-bench/scripts/lib` per ADR 0055 M1), 0052 (cost-gate hard stop), **0057 decision 1
(all panel-composition change routes through THIS loop) and decision 2 (dual-judge
headline, never same-family-only)**. Predecessor evidence:
`../2026-07-12-pdca-decide-outcome/` (frozen; scenarios REUSED read-only from it).

**This README is the pre-registration — committed before any cell spend.**

## Arms (3), same 8 scenarios, 3 reps = 72 cells, all sonnet (I2 tier held)

| Arm | Config |
|---|---|
| A (bare floor) | I2's arm A verbatim: scenario context + decide-and-record suffix + authority line. |
| C (full /decide) | I2's arm C verbatim: plugin via `--plugin-dir`, panel + advisor agents, same allow list. Re-run fresh for a same-run comparison (never compared across runs). |
| D (decider + probes) | Two INDEPENDENT probes run first, in parallel, on the same scenario bundle — fresh, unprimed, neither sees the other or any draft decision (the exp-4 mechanism: independence, not simulated self-argument). Their verbatim reports are appended to the decider's context; the decider then gets arm A's exact decide-and-record suffix. |

**Arm D probe prompts (FROZEN — the decision #180 assigns to #179's routing; iterations may
edit them ONLY through the loop's recorded diagnose-then-edit step):**

- PREMORTEM probe = scenario context + suffix:
  "Do NOT decide this. Premortem only: assume a decision on this call shipped and FAILED
  six months later. Name the 2-3 most plausible failure classes that killed it — concrete
  mechanisms grounded in the materials here (cite the file or fact each rides on), not
  generic risks. One short paragraph each."
- ASSUMPTION-HUNT probe = scenario context + suffix:
  "Do NOT decide this. Assumption hunt only: list the realistic options for this call, and
  for EACH option name the single load-bearing dependency — the one premise that, if false,
  reverses the choice. State each as 'if X is false, option Y flips'. Ground each in the
  materials here; be terse."
- DECIDER = scenario context + probe block ("Before deciding, two independent probes
  examined the same materials without seeing each other or any draft decision. Weigh their
  reports:" + both verbatim) + arm A's exact suffix.

No advisor panel, no verifier stage inside the cell (process guarantees out of scope —
this measures decision quality only, I2's rubric unchanged). A probe-call error fails the
cell (recorded, resumable) — a D cell with fewer than 2 probe reports is not arm D.

## Pre-registered bars (ADOPT requires ALL FOUR; any miss -> improvement loop, not adoption)

Headline metric (the I2 metric fix): **fraction-met over expectations 3+4 only** ("hard
pair") — exp-3 assumption-surfacing / synthetic-key expectations, exp-4 failure-anticipation
/ trap-handling. Full 4-expectation fraction-met is SECONDARY (exps 1-2 measured ceilinged
for every arm in I2: 0.92 flat).

a. **exp-4 (backtests): mean_D >= mean_C − 0.05** — the edge survives the trim.
b. **exp-3 (backtests): mean_D > mean_C** — the new step pays where no arm cleared 0.33.
c. **Full fraction-met (all 8 scenarios): cluster mean_D >= mean_C − 0.05** (non-inferiority).
d. **Cost: mean per-cell cost_D <= 0.6 x cost_C**, same-run cells only (probe + decider
   costs summed per D cell).

Deltas reported with 95% cluster-t CIs (cluster = scenario, 8 clusters, df=7); directional
point-estimate bars per the ADR 0027 precedent, CI as confidence language (weak/strong).
D−A reported for context, never an adopt basis.

**Saturation pre-screen (#178's rule, applied regardless of its /decide):** satisfied by
construction and by measurement — the headline restricts to the two expectations where I2's
control arm did NOT ace (A = 0.33 exp-3, 0.25 exp-4, vs 0.92 on the excluded pair); no arm
approached ceiling on the hard pair. No new pre-screen spend needed; recorded here.

**Judge policy (ADR 0057 decision 2, binding):** dual-judge headline — the committed opus
pipeline (grade -> prosecutor -> `min`) AND a cross-family grok-4.5 re-grade of the same
blinded normalized cells (`skill-bench/scripts/bench_verdict.py --judge both`). Both
estimates reported side by side; divergence surfaced, never averaged. Bars are evaluated on
the opus pipeline (comparable to I2) with the grok read as the required second headline;
**if the two judges DISAGREE on any bar's pass/fail, the bar is scored NOT MET** (adoption
needs both judges' agreement — pre-registered strictness, the honest cost of judge
sensitivity).

## Cost (ADR 0052 decision 3 mechanism, hard stop)

Pilot: 3 arm-D cells on B1 (~$5 expected; the pilot cap stops the NEXT cell past $8).
Then `python3 ../../skill-bench/scripts/lib/cost_gate.py --cells 72 --pilot-cost-usd
<measured A> <measured C-est> <measured D>` (equal arm mix) vs **ceiling $150** — nonzero
exit halts the grid, recorded, fresh scope decision. Arm C's per-cell estimate for the gate
comes from I2's measured grid (same config, same scenarios): $95.50 total with A/B/C mix ->
C ~= $2.4/cell conservative $4; the pilot does NOT re-price C (identical config to I2's
counted run). Runtime backstop: cumulative spend > ceiling halts resumable (grid runner).

## Improvement loop (ADR 0024 — the point of #180)

On any missed bar: diagnose D's weak cells at transcript level (which probe failed, how),
make ONE targeted edit to the probe prompts/shape (recorded in this README's log below),
re-run D cells only (C/A cached from iteration 1), re-grade D cells, re-evaluate bars.
Up to 3 valid iterations; plateau -> record the null, keep the current panel (ADR 0057
revisit trigger governs the cut question), close honestly.

## Grading pipeline (I2's, validated + blinding-audited there)

1. `blind_cells_armd.py`: outputs/*.json -> `graded/items/` neutral records via `lib/blind.py`
   (arm-C artifacts folded into response text; pre-existing corpus files excluded), arm_map,
   keys from the frozen I2 `scenarios.json`, 9 audit bids (3/arm, rep-1).
2. Opus workflow: grade -> prosecutor -> `met_final = min` -> guess-the-arm audit (3-way;
   leak bar >= 7/9). 3. Grok re-grade per Judge policy. 4. `aggregate_armd.py`: per-expectation
   met rates, the four bars, cluster CIs, dual-judge table -> `results.json`.

## Threats to validity (pre-registered)

- C re-run variance: I2's C mean is not re-used for bars (fresh C cells are); only the cost
  gate borrows I2's C price. - Probe-to-decider leakage of arm identity into transcripts:
  normalization strips format; the audit re-checks with D in the mix. - n=3 reps / 8
  clusters: wide CIs, weak/strong language pre-committed. - Author-written probe prompts
  (the thing under test — frozen above; ADR 0052's [unverifiable] scenario-representativeness
  carries over). - Judge disagreement handling can only make adoption HARDER (conservative).

## Iteration log (append-only)

- (none yet — iteration 1 is the pre-registered grid above)
