# Retrospect seeded-defect recall v2 — 2026-07-13 (issue #177; successor to ../2026-07-12-pdca-retrospect-recall/, frozen)

Same question as v1 — does the `retrospect` agent + skill beat bare Claude on seeded process
defects? — re-measured after v1's recorded diagnosis: (1) ceiling effect (v1 substrates'
CLAUDE.md restated every violated rule verbatim; bare arm recalled 0.83–1.0 by direct
rule-checking) and (2) metric–design mismatch (the agent triages to routed systemic
improvements by contract; exhaustive-recall scoring penalizes that). Methodology inherited:
ADR 0019/0023/0025/0026/0041/0052 as in v1's README (not restated). **This README + seeds.json
are the pre-registration — committed before substrate build and before any cell spend.**

**ADR 0024 guardrail, stated up front:** the goal of the harder substrates is RESTORING
DISCRIMINATING POWER, not forcing a win. A harder test may CONFIRM the negative direction
(C <= A); that verdict is recorded exactly like any other.

## Design deltas from v1 (everything else reuses v1's machinery verbatim)

1. **Discriminating rule surface.** The substrate CLAUDE.md carries only three generic lines
   (project one-liner, "run the gate before shipping", "keep docs truthful and minimal") —
   NO rule enumeration. The 8 defect classes' governing rules are distributed at realistic
   altitudes, each in exactly ONE home: partial statements for up to 6 classes spread across
   `docs/conventions.md`, a vendored ADR body, and script header comments — each statement
   names the norm but NOT the violation's tell (e.g. "preview branches with three-dot" without
   naming two-dot as the failure) — and for 2 classes per substrate the rule appears in NO
   doc at all, implied only by artifacts (e.g. `scripts/set-version.sh` existing + every prior
   version bump using it; every prior gate change carrying its test). Build-time leak check
   extends v1's: no manifest phrase AND no verbatim rule-restatement in CLAUDE.md.
2. **Harder, noisier substrates.** 20-30 commits (v1: 10-20); seeds buried in routine work
   (feature commits touching the seeded file alongside legitimate edits); subtler variants
   (e.g. backstory drift as one "previously" clause inside an otherwise-legitimate doc edit,
   not a History section); plus 3-4 distractor patterns per seeded substrate (innocuous but
   suspicious — legitimate revert, big single-concern commit, TODO comment) that punish spray.
3. **Triage-aware primary metric.** Per seed: **1.0 = found AND routed** (the finding names
   the remedy home — the file/mechanism to fix or the rule to enforce — per the class's
   `routing_key` in seeds.json), **0.5 = found only** (predicate match, no/wrong routing),
   0 otherwise. Substrate triage score = mean over its K=4 seeds.
   **Primary bar (`metadata.json:bar`): mean_delta(triage_C − triage_A) > 0**, clustered by
   substrate (6 seeded clusters), 95% t-CI as confidence signal (strong iff lower bound > 0).
   Secondary diagnostics (recorded, never the bar): v1's raw recall; per-class found rates.
   FP guard unchanged from v1 and still binds the claim: on the 2 clean substrates,
   mean_FP_C <= mean_FP_A + 1.0 prosecutor-confirmed non-real findings/cell; win + guard
   fail = INCONCLUSIVE-spray.
4. **Saturation pre-screen (mechanized, #178's rule applied regardless of its /decide).**
   BEFORE the grid: 1 bare-arm (A) rep on each of the 6 seeded substrates. Any substrate with
   raw recall >= **0.75** on that rep is hardened (documented edit to its rule surface or
   plant subtlety; re-screened) or dropped (assignment rebalanced, recorded). Pre-screen
   cells are recorded and excluded from the grid's counted cells.
5. **Judge policy (ADR 0057 decision 2 extended to this v2 grid):** the committed opus
   pipeline (predicate grade -> prosecutor -> min) is the bar's basis; a **grok-4.5 re-grade
   of every seeded cell's predicate + routing judgments** is the second headline. Both
   reported; if the judges disagree on the primary bar's pass/fail, the verdict records
   JUDGE-SPLIT (never averaged, never promoted to KEEP).

## Arms, cells, cost

Arms A and C exactly as v1 (same prompts, same sonnet tier, same allow list, same one-shot
discipline). **Counted cells: (6 seeded + 2 clean) x 2 arms x 3 reps = 48**, plus 6
pre-screen cells and a 2-cell pilot (1 A + 1 C on T1) to price the harder substrates.
Gate: `python3 ../../skill-bench/scripts/lib/cost_gate.py --cells 48 --pilot-cost-usd
<measured A> <measured C> --ceiling-usd 60` — v1 measured $26.28/48; the $60 ceiling is
~2.2x that for 2-3x-size substrates. Nonzero exit halts; runtime backstop resumable.

## Grading pipeline (v1's, blinding-audited there; routing added)

1. Normalize via `lib/blind.py` (findings as {claim, evidence-cite, proposed-remedy}).
2. Blind grader maps findings -> seed ids via found-iff predicates AND judges routing
   against the class `routing_key` (seeds.json). 3. Prosecutor re-judges every claimed match,
   every routing credit, and every non-seed finding (real/not-real -> FP guard);
   `met = min(grader, prosecutor)` per judgment. 4. Guess-the-arm audit, 8 cells, leak bar
   as v1. 5. Grok re-grade per Judge policy. 6. Aggregate: triage scores, raw recall,
   FP guard, dual-judge table, cluster CIs -> `results.json`.

## Threats to validity

v1's four carry over (author-written substrates with objective predicates; seeded-vs-wild
scope; 6 clusters wide CI; same-family grader — now mitigated by the dual-judge headline).
New: hardening-after-pre-screen is a pre-registered, documented edit path — it tunes
DIFFICULTY, never a specific arm's advantage (edits are arm-blind: both arms see the same
substrate). Routing credit adds grader judgment beyond v1's predicates — bounded by the
prosecutor min and the routing_key's concreteness.

## Run log (append-only)

- 2026-07-13 pilot: 1 A + 1 C on T1, $0.80 each ($1.60 total, cap $10) — gate projection
  48 x 0.80 = $38.4 within the $60 ceiling.
- 2026-07-13 saturation pre-screen (6 bare cells, $4.73; graded found-iff + prosecutor,
  `prescreen-graded/`): T1 0.75, T2 0.75, T3 0.75, T6 0.75 — SATURATED (>= 0.75 fires
  exactly at threshold); T4 0.50, T5 0.25 pass. Decision per pre-reg: HARDEN the four
  (plant-subtlety edits only, arm-blind, documented in the builder), re-screen before the
  grid. v1 comparison: bare-arm recall dropped from 0.83-1.0 to a 0.25-0.75 spread — the
  discriminating-surface redesign works; four substrates need one more notch.
- 2026-07-13 re-screen (round 2, hardened T1/T2/T3/T6, $2.89, graded 12/12 agents,
  `prescreen-graded-r2/`): T1 0.50, T2 0.50, T3 0.25, T6 0.25 — ALL PASS. Full bare-arm
  spread across the 6 seeded substrates now 0.25-0.50. Pre-screen discipline satisfied;
  counted grid proceeds behind the cost gate.
- 2026-07-13 grid: 48/48 cells, $30.83 (ceiling $60), zero errors; grading 152/152 agents;
  grok re-grade 36/36 seeded cells (one rate-limit retry, recorded).

## Results (verdict — 2026-07-13; `results.json`)

**Verdict: JUDGE-SPLIT on a ~zero effect — the pre-registered bar is NOT met under the
opus pipeline and the sign flips under grok; no KEEP claim, no CUT promotion.** Primary
(triage-aware, found+routed 1.0 / found 0.5): C−A = −0.028 [−0.208, +0.153] opus;
+0.014 [−0.118, +0.146] grok — both CIs straddle zero, the judges disagree only on the
sign of an effect indistinguishable from nothing. This null is the DECISIVE version of
v1's: the ceiling excuse is gone (bare-arm raw recall 0.25-0.58 post-hardening) and the
metric is the one the skill's own triage design favors.

**The reproducible edge is precision, not recall (both versions agree):** FP guard passes
with C at 1.33 vs A at 2.50 prosecutor-confirmed non-real findings per clean cell — the
skill asserts half the false positives. Per-class texture: C better on backstory-drift
(0.44 vs 0.22) and gate-piped-filter (1.0 vs 0.89); A better on missing-retrospective-line
(0.78 vs 0.22 — triage discards checklist-line pedantry by contract) and one-home-violation.
Audit 4/8 = chance — blinding held.

Reading for #172: across four instruments (I1, I2, arm-D, I1-v2) the pdca-workflow skills'
measured per-decision/per-review QUALITY edge is null or judge-dependent everywhere;
the measured, reproducible values are process guarantees, FP discipline (here), and the
panel's failure-anticipation edge over solo self-argument (I2/armd). Successor hypotheses
live in #184/#185/#186 (variance-as-metric, poker, DoD). This dir freezes per ADR 0041.
