# 2026-07-17 cross-judge re-grade of the July 8-10 house-skill battery (#224 Stage 1)

ADR 0055 follow-up (iii), executed as issue #224 Stage 1: re-derive the body-effect verdicts of
the four house skills (code-standards, engineering-principles, building-skills,
optimizing-context) from the COMMITTED raw outputs of the July 8-10 battery, swapping only the
judge — original same-family sonnet -> cross-family grok-4.5 — and classify each recorded
verdict judge-robust or judge-fragile. No new generation; judge calls only.

## Pre-registration (written before any judge call)

**Neutral hypothesis (ADR 0059):** the cross-family judge may or may not reproduce the recorded
verdicts. Direction unstated; every outcome (all-robust, all-fragile, mixed) is a valid recorded
result. Nothing is re-run or re-decided here — fragile verdicts become Stage 2 candidates only.

**Frozen inputs (ADR 0026 — read-only, nothing in them is edited):**

| source dir | cells | recorded primary verdict(s) |
|---|---|---|
| `2026-07-08-skills-hermetic` | 144 | OVERALL KEEP; per-skill bs/cs/oc INCONCLUSIVE, ep CUT-CANDIDATE |
| `2026-07-09-three-skills-remeasure` | 162 | MERGE x3 (weak) for cs, bs, oc drafts |
| `2026-07-09-bs-iter2-remeasure` | 54 | NO MERGE (null; cost prong) |
| `2026-07-09-ep-remeasure-hermetic` | 54 | MERGE (weak) for ep draft |

Cells are rebuilt from each dir's committed `outputs/` (loose `*.txt` + `all.tar.gz`) joined with
its committed `meta.json` (prompt + expectations), bid = sha256(filename)[:12] exactly as each
dir's `blind.py` defines it; the rebuilt set is asserted bid-for-bid against the committed arm
map before any grading. The judge sees prompt + expectations + response only (arm withheld —
same blinding as the original).

**Method — the ONLY intended change is the judge:**
- Judge: grok-4.5 via `skill-bench/scripts/lib/judge.py` (tool-denied, hermetic pure-text).
- Prompts: the original `grade.workflow.js` grader wording and the original
  `prosecute_counts.workflow.js` uniform-prosecutor wording, verbatim except that the cell JSON
  is inlined in the prompt (grok is tool-denied and cannot read files).
- Metric: fraction-met with `met_final = min(grader_met, prosecutor_met)` per cell (ADR 0025),
  prosecutor applied uniformly to every cell.
- Aggregation: identical math to each source dir's committed `aggregate.py` (per-eval arm means,
  per-skill mean + 95% CI clustered over evals), via the shared
  `skill-bench/scripts/lib/verdict.py` (`verdict_of`, `merge_verdict`).

**Pre-registered deviations (deterministic, judge-independent):**
1. Denominator = `len(expectations)` from `meta.json` (not the judge's self-reported `total`);
   judge totals are recorded and mismatches warned. Removes a judge-miscount corruption channel.
2. Binary pass (secondary diagnostic only in every source dir) is derived as
   `met_final == total`, not the original two-step pass->prosecute-on-PASS pipeline.
3. Merge-bar comparisons use the CURRENT shared `merge_verdict` (ADR 0027 as amended with the
   #142 cost prong) applied to BOTH sides — recorded stats and grok stats — so the judge is the
   only variable. Where the historical committed label predates the amendment (three-skills
   building-skills "MERGE (weak)" at +139 chars; bs-iter2's `merge:true` row), the
   current-bar recorded label is used and the historical label noted.

**Classification rule (pre-registered):** for each verdict pair (recorded vs grok-derived, same
statistic, same bar):
- Decision classes — keep-verdicts: positive-shown (KEEP) / negative-shown (HARMFUL) /
  not-shown (INCONCLUSIVE or CUT-CANDIDATE); merge-verdicts: MERGE / NO MERGE.
- **judge-fragile** = the decision class flips, OR a recorded CI-excludes-0 result becomes
  CI-straddling under grok (strong -> weak).
- **judge-robust** = otherwise (label shifts within a class, and weak -> strong, are recorded
  but not fragile).
Secondary rows (reported, same rule, feed Stage 2 as context not gates): per-remeasure-dir
`d_old` / `d_new` keep-verdicts.

**Known caveat (pre-registered):** judge FAMILY and judge CAPABILITY change together
(sonnet -> grok-4.5); a divergence shows judge-dependence, not which judge is right, and cannot
be attributed to family alone.

**Cost (ADR 0066/0073):** 414 cells x 2 calls = 828 grok calls, $0 marginal (subscription).
Initial notional estimate $8. **Pre-grid revision (recorded before the main run, PR #219
precedent):** the 2-cell pilot measured ~$0.065/cell steady-state (grok envelope reports far more
input tokens per call than estimated — CLI context + the inlined cell payload), projecting ~$27
notional. Revised estimate $27; `ceiling_usd` = 2x = $54 as a runaway backstop only — ADR 0066
explicitly declines a hard stop on subscription-billed notional judge spend (this run has NO
generation, so ADR 0073's mechanical generation gate has nothing to gate). The initial $8
estimate and this >2x revision are recorded here per ADR 0066's record-the-gap rule.

## Result (run 2026-07-17; all 414 cells, 0 judge errors, 0 total-mismatch warnings)

**9 of 10 primary verdicts are judge-robust; 1 is judge-fragile. 8 of 10 secondary rows
robust; 2 fragile.** Full pairs in `results.jsonl`; headline rows:

| verdict (primary) | recorded (sonnet) | grok | class |
|---|---|---|---|
| 07-08 battery OVERALL | KEEP +0.088 [+0.019,+0.156] | KEEP +0.077 [+0.006,+0.149] | robust |
| 07-08 per-skill x4 | INCONCLUSIVE x3, CUT-CANDIDATE (ep) | same labels | robust |
| three-skills merge x3 (cs/bs/oc) | MERGE-weak, NO-MERGE*, MERGE-weak | same labels | robust |
| ep-remeasure merge | MERGE-weak +0.174 | MERGE-weak +0.087 | robust |
| **bs-iter2 merge** | **NO-MERGE +0.002 [-0.137,+0.140]** | **MERGE-strong +0.119 [+0.074,+0.163]** | **FRAGILE** |

\* three-skills building-skills recorded label is NO-MERGE under the current amended bar
(historically "MERGE (weak)" pre-#142; both sides compared on the current bar per deviation 3).

Fragile secondary rows: three-skills code-standards `d_new` KEEP -> INCONCLUSIVE (grok CI
[-0.001,+0.253] — misses by a hair; this is exactly the cell #214's checkpointed L2 re-run
re-measures); ep-remeasure `d_old` CUT-CANDIDATE -> KEEP (historical old-draft arm only — the
shipped new draft's d_new is robust KEEP under both judges).

Cell-level agreement: grok-vs-sonnet mean per-cell fraction delta -0.012 to +0.068 by dir,
mean |delta| 0.036-0.096 — no systematic family-level leniency shift; the bs-iter2 dir shows
the largest (+0.068, grok more generous to that dir's with-new arm).

**Stage 2 gate output (re-run ONLY judge-fragile verdicts):** (1) bs-iter2 building-skills
iter-2 draft — the sole primary fragile: the reverted 187-char trigger-openers clause reads as a
real improvement under grok (strong CI) where sonnet read null; a paid re-run would arbitrate.
(2) code-standards d_new — already covered by resuming #214's checkpointed run (no separate run
needed). ep d_old is historical (superseded arm) — no re-run value.

Notional judge cost: $27.97 main run + $0.26 pilot = **$28.23** vs revised estimate $27
(initial $8 — the >2x gap recorded above per ADR 0066). Marginal $0 (subscription).
Aggregation self-check: feeding the committed sonnet gradings through this dir's aggregate
pipeline reproduces all 20 recorded statistics exactly (0 mismatches, all classified robust).

## Reproduce

```bash
python3 regrade.py            # frozen inputs -> graded/<source>.grok.jsonl  (resumable)
python3 aggregate.py          # -> results.jsonl + the classification table
```
