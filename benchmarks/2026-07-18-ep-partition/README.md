# ep-partition — the OPERATIONAL partition carries the skill's effect (2026-07-18)

Issue #244: which content partition of `engineering-principles` carries its measured effect
(07-09 hermetic remeasure, `d_new` mean +0.206, CI [+0.038, +0.373] excluding 0)? Run complete:
72/72 cells, blind sonnet grading + prosecutor + grok cross-family lane. Run parameters:
`metadata.json`; per-eval numbers: `results.jsonl`; the partition ruling implemented (not re-made
here): `partition/SPEC.md`.

## Result (fraction-met, met_final = min(grader, prosecutor))

| eval | without | full | operational | conceptual | d_full | d_op | d_co |
|------|--------|------|-------------|------------|--------|------|------|
| 1 | 0.83 | 1.00 | 1.00 | 0.83 | +0.17 | +0.17 | 0.00 |
| 2 | 0.80 | 0.87 | 0.87 | 0.73 | +0.07 | +0.07 | -0.07 |
| 3 | 0.78 | 0.67 | 0.72 | 0.72 | -0.11 | -0.06 | -0.06 |
| 4 | 0.40 | 0.40 | 0.53 | 0.60 | 0.00 | +0.13 | +0.20 |
| 5 | 0.00 | 0.80 | 0.80 | 0.20 | +0.80 | +0.80 | +0.20 |
| 6 | 0.27 | 0.27 | 0.40 | 0.33 | 0.00 | +0.13 | +0.07 |

- `d_operational` mean **+0.207**, CI [-0.033, +0.448] — the operational-only arm reproduces the
  07-09 full-skill point estimate (+0.206) almost exactly; CI straddles this run (n=6).
- `d_full` mean +0.154, CI [-0.110, +0.417] — the full arm ran WEAKER than its 07-09 anchor
  (+0.206 excluding 0): run-to-run variance is real; E4/E6 gave the full arm nothing this time.
- `d_conceptual` mean +0.057, CI [-0.039, +0.154] — conceptual-only adds no measurable effect.
- Contrast full-vs-operational mean **-0.054**, CI [-0.106, -0.001] — the full skill scored
  slightly BELOW operational-only, CI excluding 0: on this battery, including the
  definitional/attributional content did not help and may cost a little.
- Eval 5 (the "already approved" trap, the skill's strongest lever) is the clean signature:
  without 0.00, full 0.80, operational 0.80, conceptual 0.20.

**Read against the pre-registered kill conditions** (`results.jsonl` verdict record, computed not
asserted): `conceptual_inert` = true; `conceptual_activates` = false; `full_beats_operational` =
false. `operational_retains` computes FALSE under its pre-registered definition — a construction
blind spot recorded honestly: the definition required the full-vs-operational contrast CI to
CONTAIN 0 ("C delta ~ B"), and it instead EXCLUDES 0 in operational's favor, an outcome the
pre-registration never anticipated. The three-way summary booleans are therefore all-false by
construction; the substantive finding — operational content carries the effect, conceptual
content is inert-to-slightly-costly — is the direct reading of the CIs above, and the follow-up
(slim the shipped skill toward its operational core, then re-measure per the ADR 0024 loop) is
what the first kill condition prescribes for exactly this pattern.

**Confidence: weak** (n=6 evals; d_op CI straddles by -0.033; the one CI-excluding-0 result is
the small negative full-vs-operational contrast). No verdict-grade claim beyond: the conceptual
partition shows no measurable contribution on this battery, and every point estimate ranks
operational >= full > conceptual.

**Cross-family robustness (grok lane, all 72 blinded items independently re-graded —
`graded/grok_summary.json`):** the ordering is judge-robust — d_operational +0.230
[-0.052, +0.511] >= d_full +0.207 [-0.115, +0.529] >> d_conceptual +0.067 [-0.022, +0.155] —
and conceptual-inert holds under both judges. The full-vs-operational contrast is NOT
judge-robust: grok reads it -0.022 [-0.094, +0.050] (straddles), so the "full scored below
operational, CI excluding 0" line is a sonnet-only read — treat it as suggestive, not
established.

**Deviations recorded:** (1) one cell empty on the first grid pass, re-run once with the identical
invocation pre-blind (`metadata.json` run_health); (2) generation token counts not captured (07-09
bash harness predates the grid.py cost convention; grading token actuals recorded); (3) the first
grok lane pass parsed grok's envelope wrong (72 nulls, kept as `graded/grok_verdicts.null-run.jsonl`)
— fixed and re-run; nulls never entered any verdict.

## Design

| arm | treatment |
|-----|-----------|
| A `without` | no treatment (bare) |
| B `with-full` | stripped SKILL.md body + 3 refs, filename-headered (07-09 construction, verbatim working-tree source) |
| C `with-operational` | same construction, each source file replaced by its OPERATIONAL variant (imperative/trigger/when-to content) |
| D `with-conceptual` | same construction, each source file replaced by its CONCEPTUAL variant (definitional/attributional content) |

6 evals x 4 arms x 3 reps = 72 cells. Prescreen (bare arm, `benchmarks/2026-07-09-ep-remeasure-hermetic/results.jsonl`):
E1 .833 E2 .800 E3 .778 E4 .600 E5 .200 E6 .200 — no eval >= 0.85, none dropped; E1 flagged
borderline. All 6 evals proceed. See `metadata.json` for the full prescreen/cost/partition blocks.

## Kill conditions (quoted, issue #244)

> - C delta ~ B AND D delta ~ A -> conceptual content inert on this battery; skill slims to
>   operational core (then re-measure the slim body per the 0024 loop).
> - D delta ~ B -> activation hypothesis wins; content can shrink toward a trigger surface.
> - B > C clearly -> conceptual content carries real signal; the 'models know it' prior is
>   refuted twice over.

`aggregate.py` reads these off the eval-clustered 95% CIs as four named booleans (`operational_retains`,
`conceptual_inert`, `conceptual_activates`, `full_beats_operational`), each with a computed evidence
string, and combines them into the three quoted reads above (`verdict.reads_summary`). No Option-E
escalation (07-09/ADR 0027 mechanism; not part of this design).

## Partition method

`partition.py` implements the pre-registered ruling (`partition/SPEC.md`) by H2 section-heading
dispatch (hardcoded table mirroring the spec) plus four named sentence/paragraph-level splits
(SKILL.md intro, design-review.md intro + Core Principle, ssot-enforcement.md intro + Core
Principle, root-cause-analysis.md intro). It fails loudly (exit 2, naming the heading) if a source
file's H2 headings don't exactly match the dispatch table — extra or missing — so it never silently
classifies content the spec didn't account for. TOC blocks are dropped from both variants; a
section's heading travels with whichever variant keeps its content, or is emitted into both when the
section (Core Principle, in two of the four files) is itself SPLIT.

**Ambiguity resolved (flagged, not invented):** the spec never classifies each file's H1 document
title (`# Engineering Principles`, `# SSoT Enforcement`, `# Design Review`, `# Root Cause Analysis`)
— only body content below it. Resolution: H1 is structural, not classified content; it is kept in
BOTH the operational and conceptual variant of each file (same treatment a document title gets in
the unpartitioned `with-full` construction) and is excluded from the heading-mismatch fail-loud
check (that check applies to the named `## ` sections only, which is what the spec enumerates
exhaustively). This is why the per-file char reconciliation below carries a small positive overlap
term for H1 (and, on the two SPLIT files, for the duplicated `## Core Principle` heading) rather
than reconciling to zero.

### Char verification

`with-full` char count vs a hand computed reconstruction (stripped body + 3 refs + headers, built
independently of `prep.py`) — **matches exactly**: body 4012, full 22774.

Per-file reconciliation (`operational_chars + conceptual_chars + toc_dropped_chars` vs `raw_full_chars`,
printed by `partition.py`):

| file | operational | conceptual | toc_dropped | raw_full | gap | accounted overlap | residual |
|------|-----------:|-----------:|------------:|---------:|----:|-------------------:|---------:|
| SKILL.md | 3000 | 1036 | 0 | 4012 | +24 | 24 (H1) | 0 |
| design-review.md | 6416 | 276 | 411 | 7069 | +34 | 32 (H1 + dup. Core Principle heading) | +2 |
| root-cause-analysis.md | 3730 | 351 | 0 | 4060 | +21 | 21 (H1) | 0 |
| ssot-enforcement.md | 6822 | 389 | 333 | 7507 | +37 | 35 (H1 + dup. Core Principle heading) | +2 |

The accounted overlap is the H1 title (kept in both variants) plus, on the two files with a SPLIT
Core Principle section, the `## Core Principle` heading (emitted once per variant since both variants
retain part of that section). The +2 residual on those same two files is `"\n\n".join()` reconstruction
whitespace (a fresh joiner appears where TOC removal, or the sentence-level intro split, changed local
adjacency versus the source's inline spacing) — every non-TOC *content* character is assigned to
exactly one of {operational, conceptual}; nothing is silently duplicated or dropped at the content
level. See `metadata.json`'s `partition.reconciliation_note` and `partition/chars.json`.

## Reproduce

```bash
python3 partition.py                              # skills/engineering-principles/{SKILL.md,references/*}
                                                    #   -> partition/{operational,conceptual}/*.md + SPEC.md
python3 prep.py                                    # treatments/{with-full,with-operational,with-conceptual}.txt,
                                                    #   prompts/, cells.tsv, meta.json, treatments/costs.json

PILOT=1 bash harness.sh                            # 2 cells (eval 5 without rep1, eval 5 with-full rep1)
                                                    #   -> pilot-outputs/ ; review before the grid

HERMETIC_RELOCATE_USER_MEMORY=1 bash harness.sh    # 72 cells -> outputs/ (verify ~/.claude/CLAUDE.md after)

python3 blind.py                                   # outputs/ -> graded/items/ (arm withheld) + arm_map.tsv
# Workflow ../2026-07-08-skills-hermetic/grade.workflow.js            {itemsDir, bids} -> graded/verdicts.jsonl
# Workflow ../2026-07-08-skills-hermetic/prosecute_counts.workflow.js {itemsDir, bids} -> graded/prosecute_counts.jsonl
# grok cross-family re-grade lane on the same blinded items (divergence check, not a promotion)

python3 aggregate.py                               # -> results.jsonl + verdict (kill-condition reads)
python3 archive_raw.py                             # once: outputs/all.tar.gz + per-(eval,arm) sample
```

*Disclosure: written by Claude (Claude Code) under the direction of the repo owner.*
