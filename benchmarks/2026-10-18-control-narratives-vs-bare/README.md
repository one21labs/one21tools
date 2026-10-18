# 2026-10-18 control-narratives vs bare, Claude Opus 5.5 and Claude Sonnet 5.5 — VERDICTS PROVISIONAL (FRAME-UNCHECKED)

First measurement of control-narratives (the README listed it as "unmeasured (no baseline yet)").
Owner answers 18-Oct: $30 cap, both models, blind-authored tasks only. Pre-registration:
`metadata.json` (committed before any generation). Every verdict below was graded by Claude
Opus 5.5, the generators' family, so none may back a README claim until a cross-family judge
grades the same committed cells (`python3 grade.py --dirs outputs --judges grok`, then
`aggregate.py --judge grok`). No cross-lineage CLI was installed in this container.

## Result (with − without fraction-met; eval-clustered 95% t-interval; 2 reps per cell)

| model | G | bare | with | delta [95% CI] | mde80 | win rate | verdict | status |
|---|---|---|---|---|---|---|---|---|
| Opus 5.5 | 6 | 0.861 | 0.719 | −0.142 [−0.238, −0.045] | 0.131 | 0.17 | HARMFUL | diagnostic (G<8) |
| Sonnet 5.5 | 9 | 0.765 | 0.687 | −0.078 [−0.224, +0.069] | 0.203 | 0.22 | INCONCLUSIVE | batch |

Pooled over both models' 15 (model, eval) clusters (pre-registered secondary): −0.103
[−0.191, −0.016]. Per-eval deltas: `results-claude-opus-5-5.json`. Neither model is a KEEP.

## How to read it

- **Direction is negative on both models.** Of 15 (model, eval) clusters, 10 went down, 3 were
  flat and 2 went up; 22 (model, eval, expectation) met-rates got worse with the skill, 9 better. Opus clears zero on the harmful side but at G=6, so it is diagnostic only (ADR 0095
  decision 4); Sonnet is G=9 and straddles zero.
- **Mechanism (from the judge's reasons, not inferred):** the skill's own rules ("numbers live
  in lists, never in prose"; interlocks and alarms "referenced, not duplicated") make replies
  defer the content the task asked for to a setpoint list, a cause-and-effect chart, a vendor
  document, or a TBD placeholder. Examples: E13 lists LSL-110/LSH-120 "only as C&E tags with C&E
  rows left as placeholders" and never says the pump stops; E8 "only asks for a fail position
  table" without giving the positions; E6 leaves thresholds "TBD, not defined". Counted
  directly: "TBD", "setpoint list" and "C&E" appear 149 times in Opus with-arm replies vs 0
  bare, 224 vs 39 on Sonnet. With-arm replies are also 45-60% longer (Opus 13.6k vs 9.5k chars,
  Sonnet 11.3k vs 7.0k), so the loss is not brevity.
- **Is the rubric unfair to the doctrine?** In a full document set, referencing the C&E chart is
  sound practice. But each task supplied no such list and asked for a corrected or drafted
  section, so a reply that points at a list it never writes hands the engineer less. The
  expectations were written blind from the one-line description (trigram excess +0.002,
  `overlap.json`); they encode what the receiving engineer needs, not house doctrine. A domain
  expert's read of a few cell pairs would settle this; the numbers alone cannot.
- **Headroom is thin on Opus.** 10 of 16 tasks saturated bare on Opus (>= 0.85) and 7 of 16 on
  Sonnet: the bare models already write competent control narratives.
- **Multiplicity:** 2 primary intervals at 95%; about 0.1 false calls expected under a null.

## Exclusions

None. No ERROR cells in the prescreen or grid; one judge call retried once and succeeded
(61 calls for 60 cells).

## Costs

Generation $11.15 (prescreen $3.22, pilot $1.41, grid $6.52) + Opus judge $6.35 = $17.50 of the
owner's $30 cap, plus two isolation probes (~$0.015) before pre-registration.

## Reproduce

```bash
python3 prep.py && python3 overlap.py
python3 run_all.py   # prescreen -> grade -> select -> pilot -> cost gate -> grid -> grade -> aggregate
```
