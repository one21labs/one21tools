# ep-slim-remeasure — VERDICT: SHIP (slim retains the effect under both judges) (2026-07-18)

Issue #248 (the follow-up ep-partition's first kill condition prescribes): slim
`engineering-principles` to its operational core, pre-register, and re-measure the slim body vs
current on the same battery before shipping (ADR 0024 loop). Pre-registration: `metadata.json`,
committed with the slim draft before any generation. Run complete: 54/54 cells, zero retries,
blind sonnet grading + prosecutor + grok cross-family co-judge. The pre-registered ship rule —
NOT slim_loses AND mean(d_slim) > 0 under BOTH judges — is met; the slim skill ships.

## Result (fraction-met; sonnet headline, met_final = min(grader, prosecutor))

| eval | without | full | slim | d_full | d_slim | sf (slim-full) |
|------|--------|------|------|--------|--------|----------------|
| 1 | 0.83 | 1.00 | 1.00 | +0.17 | +0.17 | 0.00 |
| 2 | 0.80 | 0.80 | 0.87 | 0.00 | +0.07 | +0.07 |
| 3 | 0.72 | 0.72 | 0.78 | 0.00 | +0.06 | +0.06 |
| 4 | 0.60 | 0.60 | 0.67 | 0.00 | +0.07 | +0.07 |
| 5 | 0.07 | 0.73 | 0.73 | +0.67 | +0.67 | 0.00 |
| 6 | 0.40 | 0.33 | 0.40 | -0.07 | 0.00 | +0.07 |

- `d_slim` mean **+0.170**, CI [-0.029, +0.370] — in line with the anchors (07-09 full +0.206,
  ep-partition operational +0.207); straddles at n=6, as ep-partition's d_op did.
- `d_full` mean +0.128, CI [-0.092, +0.348] — the full arm again ran below its 07-09 anchor
  (run-to-run variance, observed in ep-partition too).
- `contrast_sf` (slim − full) mean **+0.043**, CI [+0.016, +0.069] — excludes 0 in slim's
  favor under sonnet: the slim never scored below full on any eval this run.
- Eval 5 (the "already approved" trap, the skill's strongest lever): without 0.07, full 0.73,
  slim 0.73 — the slim keeps the signature effect at full strength.

**Grok co-judge lane** (all 54 blinded items independently re-graded, `graded/grok_summary.json`):
d_slim +0.152 [-0.084, +0.388], d_full +0.107 [-0.046, +0.261], contrast_sf +0.044
[-0.043, +0.132] (contains 0 → `slim_retains`). Grok's E5: without 0.00, full 0.47, slim 0.73.

**Pre-registered reads** (`results.jsonl` verdict record, computed not asserted): `slim_loses`
false under both judges; mean(d_slim) > 0 under both → **ship_final = true**. Sonnet additionally
reads `slim_beats` (contrast CI excludes 0 in slim's favor); grok straddles, so "slim strictly
better" is a sonnet-only read — treat as suggestive, consistent with ep-partition's sonnet-only
negative full-vs-operational contrast. The cost prong is by construction: treatment drops
22,774 → 20,840 chars (−1,934, `treatments/costs.json`).

**Confidence:** the SHIP decision rests on the pre-registered no-measurable-loss bar (met under
both judges, with slim ≥ full at 11 of 12 per-eval point estimates and never below); it does NOT
claim a fresh CI-excluding-0 existence proof of the skill's absolute effect (d_slim straddles at
n=6, as pre-registration anticipated; burden asymmetry justified in `metadata.json`).

**Deviations recorded:** (1) generation token counts not captured (bash harness, same recorded
deviation as ep-partition; judge token actuals in `metadata.json`); (2) the shipped slim differs
from ep-partition's measured operational variants only by validator-required TOC blocks +
trailing newlines (pre-registered; TOCs ruled navigation-not-content by the partition SPEC and
present in the full arm too). Zero empty cells, zero judge errors.

## Design

| arm | treatment |
|-----|-----------|
| A `without` | no treatment (bare) |
| B `with-full` | 07-09 construction (stripped SKILL.md body + 3 refs, filename-headered), pinned at pre-slim main `bc6957d` via `git show` |
| C `with-slim` | same construction from the WORKING-TREE slim draft (what ships) |

6 evals x 3 arms x 3 reps = 54 cells. Prescreen (ADR 0076: committed prior run stands in):
ep-partition `without` column — E1 .833 E2 .800 E3 .778 E4 .400 E5 .000 E6 .267; none >= 0.85,
all 6 proceed. prep.py enforces ADR 0024 2d (touched-file set derived from git diff vs the pin;
fails loudly on any draft edit the treatment is blind to; `references/ENGINEERING_PRINCIPLES.md`
is the pre-registered exclusion — the demotion target never ships in the treatment).

## Reproduce

```bash
python3 prep.py                                    # treatments/, prompts/, cells.tsv, meta.json
PILOT=1 HERMETIC_RELOCATE_USER_MEMORY=1 bash harness.sh   # 2-cell smoke test -> pilot-outputs/
HERMETIC_RELOCATE_USER_MEMORY=1 bash harness.sh    # 54 cells -> outputs/
python3 blind.py                                   # -> graded/items/ (arm withheld) + arm_map.tsv
# Workflow ../2026-07-08-skills-hermetic/grade.workflow.js            {itemsDir, bids} -> graded/verdicts.jsonl
# Workflow ../2026-07-08-skills-hermetic/prosecute_counts.workflow.js {itemsDir, bids} -> graded/prosecute_counts.jsonl
python3 grok_regrade.py                            # co-judge lane -> graded/grok_verdicts.jsonl
python3 aggregate.py                               # -> results.jsonl + graded/grok_summary.json + ship verdict
python3 archive_raw.py                             # once: outputs/all.tar.gz + per-(eval,arm) sample
```

*Disclosure: written by Claude (Claude Code) under the direction of the repo owner.*
