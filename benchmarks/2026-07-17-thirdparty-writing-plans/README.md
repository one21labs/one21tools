# Third-party planning skills under /bench — writing-plans + CEK plan-task (2026-07-17, issue #193 item 2)

First `/bench` measurement of skills authored OUTSIDE house conventions — the object under test
is as much skill-bench's out-of-distribution validity as the skills themselves. Pre-registration
of record: issue #193 (2026-07-16 comment + CEK addendum); owner spend approval on the issue,
17-Jul. Run contract mirrored in `metadata.json` and committed before any generation.

## Question (neutral, ADR 0059)

Does loading a third-party planning skill change graded implementation-plan quality on planning
tasks versus a bare arm? Direction unstated; KEEP/CUT per the shared `benchstats.keep_verdict`
rule (ADR 0025). A null is an equally valid recorded outcome. GATE, not optimization (ADR
0062/0065).

## Candidates (upstream-fetched, `treatments/provenance.json`)

| arm | skill | source | version | body bytes |
|-----|-------|--------|---------|-----------|
| `wp` | `writing-plans` | obra/superpowers @ d884ae04edeb | 6.1.1 (MIT) | 7,092 |
| `cek` | `sdd/plan-task` | NeoLabHQ/context-engineering-kit @ a0bfff193862 | 3.1.2 (GPL-3.0) | 46,099 |

Injected per-arm via `--append-system-prompt`, frontmatter stripped — deterministic body-effect
(L2) loading. **Labeled caveat (pre-registered infrastructure asymmetry):** both skills
orchestrate files/subagents their body cannot execute under the hermetic arm (Task/Agent/Bash
denied) — this measures body-as-guidance, not the full workflow product.

## Design

- 4 feature-planning evals (`evals.json`) against a committed Flask fixture repo (`fixture/`),
  6 consumer-side expectations each (exact paths, per-step verification, code-level
  decomposition, named tests, zero-context executability, scope discipline) — authored from the
  plan-consumer's needs; the skill's own reviewer prompt was grounding only, never the rubric.
- 3 arms x 3 reps, hermetic `claude -p` (sonnet, ADR 0023 recipe via `hermetic_driver`), fresh
  fixture copy per cell, tools carved to Read/Grep/Glob/Write/Edit. Bare cells generated ONCE
  and shared by both pairs (pre-registered protocol fact).
- Graded artifact: the cell's new `*.md` files (expected `PLAN.md`), else response text — same
  rule every arm; `artifact_check` min 400 chars, failures are ERROR cells never quality 0
  (#191); `capture_symmetry` sweep gates grading.
- Judges: grok headline (cross-family), claude divergence pass on identical cells; a verdict
  flip on either pair = exploratory, no KEEP/CUT promotion (pre-registered kill condition).
- Sequence: saturation prescreen (bare x4, ceiling 0.85 / floor flag, ADR 0065) -> cost pilot
  (wp x2 + cek x1 on E1, >2x-estimate hard stop, ADR 0066) -> 36-cell grid under the
  `metadata.json` cost gate + spend backstop.

## Reproduce

```bash
python3 grid.py --prescreen   # bare x 4 evals x 1 rep -> prescreen-outputs/
python3 grid.py --pilot       # E1 x (wp x2 + cek x1)  -> pilot-outputs/
# fill metadata.json cost.per_arm_estimate_usd from the observed cell costs, then:
python3 grid.py               # 36 cells -> outputs/ (cost-gated, resumable)
python3 grade.py              # -> graded/cells-{grok,claude}.jsonl + symmetry.json
python3 aggregate.py          # -> results.jsonl
```

## Results (run 2026-07-17; 43 committed cells, 0 ERROR cells, capture symmetry clean)

| pair | grok (headline) | claude (divergence) | verdict |
|------|-----------------|---------------------|---------|
| wp - bare | **+0.167** [0.167, 0.167] | +0.181 [0.153, 0.208] | **KEEP, strong, judge-robust** |
| cek - bare | **0.000** [0.0, 0.0] | -0.014 [-0.082, 0.055] | **CUT-CANDIDATE, weak, judge-robust** |

- Arm means (grok): bare 0.833, wp **1.000**, cek 0.833; binary all-met rate: bare 0/12, wp
  **12/12**, cek 0/12. Consistency: within-eval rep spread 0.0 in every arm; worst-rep = mean.
- **Mechanism (cell-cited, not exploratory):** the entire wp delta is expectation 2 — per-step
  verification. Bare and cek missed it in 12/12 cells each; wp met it in 12/12
  (`graded/cells-grok.jsonl`). `writing-plans`' core promise ("how to test it" per bite-sized
  task) is exactly the consumer expectation bare plans skip — and its 7KB body delivers it
  uniformly. The prescreen had flagged this concentration pre-grid (metadata.json:prescreen).
- **cek null, labeled caveat:** plan-task's 46KB body produced zero measured movement on these
  consumer expectations. Its value proposition is a multi-agent refinement WORKFLOW that cannot
  execute under the hermetic arm (Task/Agent denied) — this run measures body-as-guidance only
  (pre-registered infrastructure asymmetry); a workflow-capable substrate could measure what
  this design cannot. 6.5x wp's injected bytes for none of its measured effect.
- Cross-judge agreement 0.977 over 216 expectation-cells (grok stricter 1, claude stricter 4);
  no verdict flip on either pair — the pre-registered kill condition did not fire.
- **Instrument gate (the secondary question): PASS.** First out-of-distribution measurement:
  judge-robust, mechanism-attributable verdicts on two skills authored outside house
  conventions, one positive and one null — the method discriminates rather than flattering.
- **Cost actuals:** committed generation cells $17.46 (prescreen $1.24 + pilot $1.43 + grid
  $14.80, real API-priced envelopes) + ~$0.78 duplicate-pilot operator error (overwritten
  cells, recorded in metadata.json:pilot) + claude judge $5.03 real + grok judge notional ~$1.1
  (subscription-billed). Real total ~$23.3 — over the initial $12 encoding, under the
  pre-registered >2x stop ($24); the ceiling revision is recorded pre-grid in metadata.json.
- Judge-timeout note: one grok grading call timed out (300s) mid-pass; grading is resumable and
  the re-run completed — no cell was regraded twice (`graded/cells-grok.jsonl` is append-once).
