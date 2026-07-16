# Retrospect friction-channel Phase-0 — 2026-07-15 (issue #189; pre-registration = ADR 0068)

Zero-generation-spend kill test of the #189 hypothesis: a mechanical friction ledger
(deterministic extract of tool errors, hook denials, nonzero exits from session transcript
JSONL) surfaces finding-grade friction that the orchestrator-curated summary the retrospect
agent received omitted. Frozen question and threshold fixed in ADR 0068 before any analysis:
does the ledger surface >= 1 finding-grade, curated-omitted item in >= 3 of the 5 most recent
retrospect-bearing sessions? Below threshold -> recorded null, #189 closes, no machinery.

## Verdict: PASS, exactly at threshold — 3/5 sessions (S1, S2, S4)

| session | agreed finding-grade (all) | ledger FG pre-retrospect | curated-omitted | pass |
|---------|---------------------------|--------------------------|-----------------|------|
| S1 (6 branch retrospects, 15-Jul) | 8 | 2 | 1 (Edit-before-Read x2, pre-registration.md) | YES |
| S2 (#170-completion, 15-Jul) | 10 | 6 | 1 (Edit-before-Read x2, run_eval.py) | YES |
| S3 (0051-amend, 15-Jul) | 3 | 0 | 0 | no |
| S4 (#172-closure, 14-Jul) | 11 | 3 | 2 (gate-pipe denial x4; python-not-found) | YES |
| S5 (route-i2, 14-Jul) | 4 | 4, all POST-retrospect | 0 (timing-excluded) | no |

The omitted class is consistent: repeated guard-denial friction (Edit-before-Read, gate
piping) — the orchestrator's own discipline slips — while the same orchestrators DID curate
tool quirks, platform gaps, and third-party defects. That is the agenda-setting signature
#189 hypothesized: the reviewed party under-reports evidence against itself. S4's curated
list itself proves the class is finding-grade by repo practice: the one Edit-before-Read
cluster the orchestrator noticed (MEMORY.md x4) WAS curated as friction 1.

## Method (files here are the audit trail)

- `extract.py` — deterministic ledger extract (every is_error tool_result, deduped,
  categorized) + curated-channel extract (retrospect spawn prompts) from 5 session JSONLs.
  Raw transcripts are private session data and stay outside the repo; the extracted pools
  committed here are the analysis substrate.
- `pool.py` — blind pools: ledger + curated items, channel-stripped, seeded shuffle.
- `pools/` + `key.json` — per-session blind pools and the unblinding key.
- `grades.json` — 10 independent classifier passes (5 sessions x 2, sonnet subagents,
  identical prompts, no cross-access), agreement rule pre-stated: finding-grade iff BOTH
  passes agree; uncertain -> BENIGN (conservative toward null).
- `verdict.py` + `final.json` — aggregation: agreed finding-grade ledger items, cut at each
  session's LAST genuine retrospect spawn timestamp (a ledger built at retrospect time only
  contains prior events), coverage-checked against the curated items (quoted in COVERED_BY).

## Corrections log (all pre-verdict; recorded per ADR 0059 honesty bar)

1. **Pooled-run contamination, discarded.** The first design pooled all 5 sessions into one
   blind list; one classifier violated the judge-independently instruction and marked items
   BENIGN as "duplicate of" items from OTHER sessions, corrupting the per-session question.
   Discarded before any verdict; re-run with per-session pools (`classA/B-pooled.json` kept
   for the record).
2. **Spawn-detector false positives.** Two S5 "retrospect spawns" were build-spec agents
   whose prompts mention retrospect+friction; S5's genuine retrospect spawn carried NO
   friction summary, so its curated channel is empty. Its ledger items were then
   timing-excluded anyway (all post-retrospect).
3. **Curated-format parse.** S1's friction lists are inline "(1) ... (2) ..." enumerations;
   the first bullet-only parser missed them (caught by a zero-curated-items sanity check).

## Sensitivity (the honest hinge)

The pass hinges on classifying REPEATED discipline violations (count>=2 of the same guard
denial) as finding-grade. The per-session classifier prompt states repetition IS the systemic
signal — consistent with ADR 0047's recurring-miss promotion trigger and with S4's own
curated treatment of the class. Under the opposite reading (every caught-by-guard denial is
benign regardless of repetition), the verdict flips to 1/5 NULL on this corpus: S4 alone
passes (python-not-found, count=1, is not repetition-based). ADR 0068's [unverifiable]
assumption REOPEN-IF covers exactly this: an independent re-classification that rejects the
repetition rule reopens the verdict.

## Disposition (per ADR 0068 decision 2)

Phase 1 licensed for the LEDGER only: pre-registration per ADR 0065 (gate-or-optimization
field, variance, MDE) + ADR 0066 (grading-cost estimate) before any retrospect-skill or hook
edit. Blind-first ordering stays a separate claim requiring an ADR 0024 measured run.
Notional classifier cost: 12 sonnet subagent calls (2 discarded-run + 10 per-session),
zero generation spend, zero API spend (session subagents).
