# 2026-07-18 building-skills iteration 3 — VERDICT: NO MERGE (recorded; draft reverted)

Owner-redirected replacement for arbitrating the iter-2 cross-judge flip (#224 Stage 1, PR
#227): author an evidence-based revision and measure whether it is unambiguously better.
Pre-registration: `metadata.json` (committed before generation). The pre-registered bar —
MERGE with diff CI excluding 0 under BOTH judges — was NOT met; per the pre-registration the
draft is reverted and this record ships alone.

## Result (fraction-met; 4 evals x 3 arms x 3 reps; E3/E6 prescreen-dropped saturated)

| judge | d_old (old-bare) | d_new (new-bare) | diff (new-old) | ADR 0027 verdict |
|---|---|---|---|---|
| grok (headline) | +0.153 [-0.016,+0.321] INCONCLUSIVE | **+0.361 [+0.192,+0.530] KEEP** | +0.208 [-0.020,+0.437] | **NO-MERGE** |
| claude (divergence) | +0.236 [+0.004,+0.469] KEEP | **+0.361 [+0.108,+0.615] KEEP** | +0.125 [-0.178,+0.428] | **NO-MERGE** |

No cross-judge flip. The mechanical decision: diff means are positive under both judges but
the CIs straddle zero at n=4, and the +3-codepoint body growth fails the cost prong
(merge_verdict: a weak merge is contingent on chars_delta <= 0) — so NO MERGE.

Honest texture, recorded not acted on: the revision's absolute benefit clears zero under BOTH
families (d_new KEEP twice — with-old never achieved that under grok), E5 (the flagged 0.0-floor
eval, target of the "cut means delete" edit) moved 0.44 -> 1.00 under both judges (diff +0.56),
and the only regression is claude's E1 (-0.17, single-rep noise range). This is a
directional-positive, underpowered miss decided by a 3-codepoint cost prong — not a null.

## Iteration ledger (ADR 0024)

iter1 marginal keep (+0.009) -> iter2 sonnet-null/grok-flip (the Stage 1 fragile) -> iter3
directional positive, underpowered, cost-prong fail. Iteration-4 leads: (a) reshape the same
five edits to be net char-NEGATIVE (4+ more codepoints of cuts flips the cost prong; the
content already measures well), and/or (b) restore eval power (E3/E6 saturated at n=1
prescreen — harden or replace them; n=4 clusters cannot exclude zero at these effect sizes).

## Costs

Generation $14.31 (prescreen $2.16 + pilot $1.02 + grid $12.02 incl. 36 cells) vs estimate
$24 band / ceiling $48; judges: claude $3.72 real, grok $2.06 notional (incl. prescreen +
4-cell integrity re-grade). 0 judge errors. Integrity note: the prescreen's 6 grok rows are
split to `graded/prescreen-grok.jsonl`; the 4 grid bids they shadowed were re-graded from the
grid outputs so both judges graded identical content.

## Reproduce

```bash
python3 prep.py && python3 grid.py --prescreen && python3 grid.py --pilot && python3 grid.py
python3 grade.py && python3 aggregate.py
```
