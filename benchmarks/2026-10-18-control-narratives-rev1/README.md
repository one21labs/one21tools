# 2026-10-18 control-narratives revision 1 vs bare, Opus 5.5 and Sonnet 5.5 — VERDICTS PROVISIONAL (FRAME-UNCHECKED)

Re-measure after `../2026-10-18-control-narratives-vs-bare/` found the skill's direction negative.
Owner answers 18/19-Oct: revise and re-measure, held-out tasks as the primary, cap $30 raised
to $35 to regenerate truncated cells. Pre-registration: `metadata.json` (committed before any
generation; its `deviations` list both departures). Every verdict below was graded by Claude
Opus 5.5, the generators' family, so none may back a README KEEP until a cross-family judge
grades the same committed cells (`python3 grade.py --dirs outputs --judges grok`).

## Result: held-out tasks (ids 17-32, written after the revision), primary

| model | G | bare | with | delta [95% CI] | mde80 | win rate | verdict | status |
|---|---|---|---|---|---|---|---|---|
| Opus 5.5 | 7 | 0.857 | 0.917 | +0.059 [−0.056, +0.175] | 0.158 | 0.71 | INCONCLUSIVE | diagnostic (G<8) |
| Sonnet 5.5 | 14 | 0.732 | 0.833 | +0.101 [−0.028, +0.231] | 0.182 | 0.57 | INCONCLUSIVE | batch |

Pooled over both models' 21 (model, eval) clusters: +0.087 [−0.001, +0.176]. Pre-registered
decision rule: the pooled held-out delta is not HARMFUL, so revision 1 replaces the measured
version. Neither model is a KEEP.

The tuned-on secondary (ids 1-16) did not run: the cost gate's pre-registered fallback fired
(full grid projected $24.92 against $24.07 remaining).

## How to read it

- **The sign flipped versus the first run.** The original text measured −0.078 (Sonnet, G=9)
  and −0.142 (Opus, diagnostic) on ids 1-16. Revision 1 measures +0.101 and +0.059 on new
  tasks. Different task sets, so this is not a paired version-vs-version comparison; both runs
  share the instrument, judge and models.
- **The targeted mechanism moved.** Mentions of "TBD", "setpoint list" and "C&E" per reply,
  with-arm vs bare: first run Opus 12.4 vs 0.0 and Sonnet 12.4 vs 2.2; this run Opus 5.4 vs 1.0
  and Sonnet 2.0 vs 2.7. Across 84 graded cells, 26 (model, eval, expectation) met-rates rose
  with the skill and 10 fell.
- **Not yet a claim.** Both intervals include zero; the pooled one misses clearing zero by
  0.001. Sonnet's design could reliably detect only +0.18 or larger.
- **Cost of the gain:** with-arm replies run about 60% longer (Opus 22.8k vs 14.2k chars,
  Sonnet 15.9k vs 8.7k), on top of about 1,300 tokens of skill text.
- **Headroom:** 9 of 16 held-out tasks saturated bare on Opus, 2 of 16 on Sonnet.

## Deviation: 7 truncated replies (found after grading, fixed before write-up)

Seven with-arm replies ran past the inherited 32,000-token output cap and the CLI returned only
their last chunk, so the judge graded fragments. Before the fix the result read Opus −0.071,
Sonnet −0.006, pooled −0.028; with the fragments excluded it read pooled +0.067. The 7 cells
were marked ERROR, regenerated at a 64,000-token cap (all 7 came back as complete documents),
and regraded; the superseded grades and first aggregate are kept in `graded/superseded-*`.
`grid.py` now marks any reply within 3% of its cap as ERROR. The first run had no cell near
the cap.

## Costs

Generation $21.90 (prescreen $3.50, grid $18.40 including the regenerated cells) + Opus judge
$10.23 = $32.13 of the owner's $35 cap. The pre-registered per-cell estimate ($14.32 for the
grid) undershot the actual $26.2: revision 1's replies are longer than the first run's, which
supplied the estimate.

## Reproduce

```bash
python3 prep.py && python3 overlap.py
python3 run_all.py   # prescreen -> grade -> select -> cost-gated grid -> grade -> aggregate
```
