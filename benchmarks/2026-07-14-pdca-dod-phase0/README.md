# DoD record check — does it predict rubric quality at all? Phase-0 kill test (issue #186; ADR 0061)

Does a mechanical Definition-of-Done check over a decision record predict that record's
already-graded rubric score, within the same arm — or are the checkable properties formalities
uncorrelated with quality? H1 may be false in either direction; a recorded null closes #186
per its own Phase-0 STOP rule. Zero generation spend: the substrate is the two frozen graded
corpora (`../2026-07-12-pdca-decide-outcome/`, `../2026-07-13-pdca-decide-armd/`), 72 cells
each, read-only. Methodology inherited, not restated: ADR 0059 (neutral framing), 0025
(fraction-met), 0019 (recorded snapshots), 0061 (every operationalization below).

**This README is the pre-registration — committed before any classifier call or bucket
count.** The floor and threshold are set BLIND (ADR 0061 1c): no pass/fail split has been
computed at commit time.

## The check (frozen; per-item predicates in `dod_check.py`, tested in `dod_check_test.py`)

Input per cell = the arm-blind normalized record `norm` from `graded/verdicts.jsonl`
(ADR 0061 1a; never the raw response, never the expectations).

1. Names >=1 falsifiable SUBJECT-MATTER assumption (not process/tooling/measurement) — classifier.
2. Names >=1 ACCEPTED FAILURE CLASS — classifier.
3. States a falsifiable acceptance/reopen criterion — mechanical predicate on `norm.criterion`.
4. Records >=1 rejected alternative with a reason — mechanical predicate on `norm.options`.

DoD-pass = all four. Items 1-2 are classified DUAL-FAMILY (claude sonnet + grok-4.5, one
frozen prompt, JSON schema; ADR 0061 1b — the verdict pivots on classification reliability,
0057 d2's failure mode). A cell whose two families disagree on overall DoD pass/fail is
EXCLUDED from both buckets and recorded (count + bids in `results.json`).

## Frozen question (owner text, #186) and its pre-registered operationalization

Within arm, do DoD-pass cells beat DoD-fail cells on fraction-met by >= 0.15, in BOTH
corpora? Below threshold in either -> H1 falsified, STOP, recorded null.

- Buckets are within-arm, within-corpus; never pooled (ADR 0061 1c).
- Arm three-state: both buckets n >= 5 and neither bucket > 90% of the arm's included cells
  -> TESTED (delta = mean fraction-met pass − fail); otherwise INCONCLUSIVE — absence of
  data, never falsification.
- Corpus verdict: any TESTED arm with delta < 0.15 -> FALSIFYING; all TESTED arms >= 0.15
  (and >= 1 TESTED) -> SUPPORTED; no TESTED arm -> INCONCLUSIVE.
- H1: any corpus FALSIFYING -> **FALSIFIED (STOP, no Phase 1)**; both corpora SUPPORTED ->
  SUPPORTED (Phase 1 becomes eligible follow-up work — NOT a #172 gate, ADR 0061);
  otherwise INCONCLUSIVE (recorded; Phase 1 does not proceed).
- Kill metric = FULL 4-expectation fraction-met (owner freeze). Pre-registered DIAGNOSTIC
  (ADR 0061 1d): the same three-state machinery on the exps-3+4 subset — reported alongside,
  informs a REOPEN, never overrides the kill.

## Confound (owner-named, recorded)

Correlation here cannot distinguish "check causes quality" from "good records co-occur with
checkable structure"; the grader may reward surface structure. Phase 0 only decides whether
Phase 1's causal test is worth its spend.

## Threats to validity

- Classifier reliability IS the verdict pivot — mitigated dual-family + exclude-on-disagree;
  the disagreement rate is itself reported (ADR 0061 assumption, pending this run).
- Arm-C records may pass items 3/4 near-universally by construction (the /decide template
  requires them) — the within-arm design controls this; a degenerate split lands
  INCONCLUSIVE, not a fake kill.
- Mechanical predicates are author-written regexes; frozen here, unit-tested, and every
  per-cell item verdict ships in `dod.jsonl` for audit.
- Exps 1-2 ceiling (~0.92) dilutes the full-fraction delta toward null — named at ADR 0061
  1d; the diagnostic subset exists exactly to read this.

## Cost

Zero generation. Classifier: 144 cells x 2 families x 1 call (~$1-2 notional grok via
`costing.py`; claude sonnet CLI). No cost gate needed below $5; recorded in `results.json`.

## Artifacts

`dod.jsonl` (per-cell item verdicts, both families, mechanical results), `results.json`
(buckets, deltas, three-state, H1 verdict, disagreement ledger, diagnostic, costs),
`metadata.json` (frozen config). Append-only dated dir (ADR 0041).
