# Retrospect seeded-defect recall — 2026-07-12 (issue #172, Instrument 1; ADR 0052)

Does the `retrospect` agent + skill recover seeded process defects from a session substrate
better than bare Claude given identical inputs and tool access? Pre-registered per ADR 0042 /
`pre-registration.md`; methodology inherited, not restated: ADR 0019 (eval-clustered CI),
ADR 0023 (hermetic control arm + auditable raw sample), ADR 0025 (fraction-met,
`met_final = min(grader, prosecutor)`), ADR 0026 (artifact formats), ADR 0041 (scaffold from
`benchmarks/lib`; dated dirs append-only, `empirical-evals.md:159`). **This directory is a pre-registration only — no substrate
has been built and no run executed.** Build order per ADR 0052 decision 2: shared plumbing
pilot -> this grid -> Instrument 2.

## Question and pre-registered bar

Primary (`metadata.json:bar`): **mean_delta(recall_C - recall_A) > 0**, eval-clustered
(cluster = substrate, 6 seeded clusters), CI reported as confidence signal (strong if the
95% CI lower bound > 0, weak otherwise) — directional point-estimate bar, not CI-exclusion,
per the ADR 0027 / tiered-fullgrid precedent at small cluster counts. Verdict word via
`lib/verdict.py:verdict_of` on the delta.

False-positive guard (pre-registered, binds the claim): on the 2 clean substrates,
**mean_FP_C <= mean_FP_A + 1.0** findings/cell (prosecutor-confirmed non-real assertions).
Recall win + guard fail = **INCONCLUSIVE-spray** (the skill "wins" by asserting more, not
seeing better) — recorded as such, never promoted to KEEP. A null or abandoned run is a
recorded artifact either way (ADR 0023 spirit; ADR 0052).

Cost: after the ADR 0052 plumbing pilot prices a cell, run
`python3 ../lib/cost_gate.py --cells 48 --pilot-cost-usd <measured...> --ceiling-usd 30`
— nonzero exit halts this grid. Ceiling rationale (set from the pilot, not a pre-pilot guess):
the faithful arm-C cell measured $0.375 -> $18.02/48, so **$30** is ~1.6x that projection and
clears the $26.50 conservative both-cells mean, with headroom for the 10-20-commit real
substrates the 6-commit pilot under-priced (`../2026-07-12-pdca-plumbing-pilot/README.md`). The
earlier $15 gate (a pre-pilot guess) FIRED on this projection and routed here per ADR 0052
decision 3's fresh-`/decide` rule; the hard-stop mechanism is that decision's, applied here too.

## Arms (2), same substrates, symmetric tool access

Both arms: same model (**sonnet** — ADR 0006 tiers the retrospect agent at sonnet; recorded
here as the issue requires), same substrate working dir, same tool allowance
(Read/Grep/Glob/Bash only — the deny-list minus the agent's declared tools; everything else
from `lib/deny_tools.txt` stays denied), same inputs (transcript file, git repo, session log,
friction list). The TREATMENT is content only (ADR 0023 arm symmetry):

| Arm | Config |
|---|---|
| A (bare) | neutral prompt: "Review this session for process problems: transcript at `transcript.md`, session log at `docs/pdca/session-log.txt`, friction list at `friction.md`; the git history is this repo. Report each problem with its evidence." |
| C (skill) | the `retrospect` agent's system prompt (`pdca-workflow/agents/retrospect.md`) + the `/retrospect` skill flow, orchestrator inputs supplied identically (range `origin/main...HEAD` of the substrate repo, friction list verbatim) |

No mid-run hints, no re-prompting; one shot per cell, 3 reps per arm per substrate.
**Cells: (6 seeded + 2 clean) x 2 arms x 3 reps = 48** — this resolves #172's "~36" (its
arithmetic counted only the 6 seeded substrates).

## Substrate: 8 synthetic session repos (specs pre-registered, build follows)

Each substrate = a small git repo (10-20 commits, one21tools-shaped: skills, ADRs, gate
scripts) + `transcript.md` (condensed session narrative) + `docs/pdca/session-log.txt` +
`friction.md`. Seeds are planted in commits/docs/transcript so each is objectively findable;
`seeds.json` (this dir) is the manifest — per seed: id, class, plant site (commit/file),
and a **"found iff" predicate** (the objective match rule the grader applies, e.g. "cites
commit <sha> or the narration's file:line"). The substrate build MUST NOT copy manifest
text into the substrate (grep-checked at build time: no manifest phrase appears verbatim).

Defect classes (each grounded in a shipped repo rule; 8 classes x 3 plants = 24 seeds,
K=4 per seeded substrate, classes rotated so each appears in exactly 3 substrates):

1. `backstory-drift` — doc edit narrating how-it-got-here (CLAUDE.md Docs: cut on sight).
2. `one-home-violation` — same fact restated at two altitudes (CLAUDE.md Docs).
3. `gate-piped-filter` — a gate command piped through `grep`/`head`, masking its exit code.
4. `missing-retrospective-line` — PR body without the `Retrospective:` line (ADR 0030).
5. `unpointed-amendment` — an ADR's decision changed with no amendment pointer in the record
   it touches (adr-template.md Rationalize rule).
6. `two-dot-range` — branch preview/retro ranged `main..branch` two-dot (CLAUDE.md Shipping).
7. `sacred-no-test` — a gate script changed without its paired decision-logic test in the
   same commit (CLAUDE.md Never rule).
8. `hand-edited-version` — manifest version edited directly, bypassing `set-version.mjs`,
   with plugin.json/marketplace drift (ADR 0017/0048).

Clean substrates C1/C2: same shape, zero seeds, including 2-3 innocuous-but-suspicious
patterns each (e.g. a legitimate revert with its rationale) — the FP guard's material.

## Grading pipeline (validates Instrument 2's before it spends)

1. Normalize every cell's output through the shared neutral-schema extractor
   (`lib/blind.py` home per ADR 0052 decision 4 — findings as {claim, evidence-cite}; strips
   arm-telling format).
2. Blind grader maps findings -> seed ids via the manifest predicates; recall = found/K.
3. Prosecutor re-judges every claimed match AND every non-seed finding;
   `met_final = min(grader, prosecutor)` (ADR 0025). Non-seed findings judged real/not-real
   -> precision + the FP guard.
4. Guess-the-arm audit on 8 sampled normalized cells (precedent:
   `2026-07-08-grading-bias-audit/`); auditor accuracy significantly above 0.5 = blinding
   leak -> revisit trigger per ADR 0052.
5. Aggregate per ADR 0019 (cluster = substrate); raw outputs sampled + archived per
   `lib/bench_io.py:sample_and_archive_raw`.

## Results (run 2026-07-12 — grid 48/48 cells, $26.28; grading 152/152 agents; `results.json`)

**Verdict: INCONCLUSIVE (pre-registered bar not met; direction NEGATIVE).**
mean_delta(recall_C − recall_A) = **−0.125**, 95% cluster-t CI [−0.306, +0.056] (weak).
Per-substrate deltas: T1 −0.25, T2 0, T3 0, T4 −0.333, T5 −0.25, T6 +0.083. FP guard PASSES
(C cleaner: 1.167 vs 1.333 non-real assertions/cell on clean substrates). Guess-the-arm audit:
4/8 = chance — blinding held, no revisit trigger.

Diagnosis (recorded, not post-hoc re-scoring):
1. **Ceiling effect.** Bare arm A recalled 0.83–1.0 — each substrate's CLAUDE.md states the
   exact rules the seeds violate, so a tools-enabled bare reviewer finds them by direct
   rule-checking. The eval carries little discriminating headroom for C>A (the inverse of ADR
   0025's flooring concern); absolute recall numbers here say "both arms near ceiling," not
   "skill adds nothing on hard substrates."
2. **Metric–design mismatch.** The retrospect agent's contract optimizes routed, systemic,
   deduplicated improvements ("keep only systemic ones", "note omitted one-offs") — it
   deliberately triages, and triage costs recall points against an exhaustive-enumeration
   metric. The negative direction is consistent with suppression, not blindness; C's better
   FP discipline supports this reading.
3. Pipeline validation (this instrument's other job, ADR 0052) SUCCEEDED: hermetic
   skill+agent cells, schema normalization, predicate grading, prosecutor, and the blinding
   audit all ran clean end-to-end — Instrument 2 can spend on a proven pipeline.

Per ADR 0024 the loop's next move on a null is targeted IMPROVEMENT with transcript-level
diagnosis, and any re-measure is a NEW dated dir (append-only): candidate design fixes for a
successor run are harder substrates (rules not restated verbatim in the substrate CLAUDE.md)
and/or a triage-aware metric (score routed-improvement quality, not raw enumeration). This
dir stays as-is: the frozen record of what was measured. Raw outputs: 1 per (substrate, arm)
kept in `outputs/`, remainder in `outputs/all.tar.gz` (ADR 0026).

## Threats to validity (pre-registered)

- Author-written substrates (author also wrote the skill) — mitigated by objective found-iff
  predicates fixed before any run; residual named.
- Seeded defects may be easier than wild ones (synthetic-injection critique; DeepSource, in
  `../2026-07-12-pdca-decide-outcome/prior-art.md`) — claims scoped to "seeded-defect
  recall", never "real-world".
- Small cluster count (6) -> wide CI; confidence language pre-committed above.
- Same-family grader (Claude-grades-Claude, ADR 0019 residual) — unchanged here.
