---
id: 0092
title: "Context earns its place: record only what is useful AND non-obvious; cap the corpus as a WIP limit"
status: accepted
summary: "Owner-direct. Per-file caps bound each record but never the count, so the corpus reached 422,915 chars while every file passed. Bar for writing anything into context: useful AND non-obvious TO THE READER — doubt about contested, record; doubt about obvious, don't. Operationalized by ADR_CORPUS_BUDGET, a WIP cap in char-budget.mjs enforced by adr-lint: growth is paid for by compaction, never granted. A 4-condition experiment on a copy of the real corpus confirms it forces a trade rather than obstructing."
---

# 0092 — context earns its place

- Date: 2026-07-26
- Owner: PM (owner-direct; recorded because it governs every future record)
- Context: per-file caps (ADR 0008/0009) bound each record but not the count, so 91 records
  reached 422,915 chars with every file under cap — unreadable whole, so sessions sample it by
  grep, which is how a passing MENTION gets inherited as a DECISION (ADR 0091's failure).
  Always-loaded context measured this session at only 10,238 chars; the cost is not inference,
  it is carrying.

## Decision
**1 — The bar.** Anything written into context must be useful AND non-obvious to a future
READER, not to its author — everything is obvious to whoever just worked it out. Asymmetry that
keeps the bar safe: doubt whether it is CONTESTED -> record it; doubt whether it is OBVIOUS ->
don't. A blocking, contested call passes the bar; process minutiae fail it and belong in git
history.

**2 — Storage is never free.** An unread record costs no inference tokens but carries
drift-maintenance, retrieval noise, and triage. Needed means retrieved, which costs; not needed
means waste — no free third state. A rarely-read record that prevents re-litigating a settled
call is insurance with real option value.

**3 — `ADR_CORPUS_BUDGET`** (char-budget.mjs, enforced by adr-lint), owner-set at 200,000 and MET
by compaction the same day: 428,269 -> 194,883 (54% cut, 92 records kept, none deleted). Growth is
PAID FOR by compacting or superseding, never granted.
The bar alone is prose and would drift; the cap is the executable half (ADR 0047: a decidable
requirement needs an executable home) that forces "does this earn its carrying cost?" to be
answered instead of deferred. A lite record spends 1/6 of a full one, so the cheapest way to
stay under is the default tier.

## Assumptions
- [verified] the cap forces a TRADE, not a block — 4-condition experiment on a copy of the real
  corpus: baseline 422,915 PASS; +one full record FAILS over by 3,915; after compacting one
  record 8,965 -> 1,500, PASS; a LITE record instead of the full one PASSES where it didn't.
- [unverifiable] WEAKEST — compaction under the cap removes NOISE rather than reasoning that prevents re-litigation. REOPEN-IF a decision is re-litigated because its record was compacted away -> the cap is trading the wrong thing; raise it or exempt insurance-class records.

## Rejected alternatives
- A repo-wide token budget over all files — taxes the archive identically to always-loaded
  context, which is already capped and healthy at 10,238 chars.
- No cap, bar only — a judgment shell with no forcing function; the corpus reached 422,915 chars
  under exactly that regime.
- A scorecard readout instead of a gate — that is what the per-file caps already were: visible
  and unbinding.

## Revisit triggers
- The WEAKEST REOPEN-IF fires -> raise the cap or exempt insurance-class records.
- The cap is raised twice without a compaction pass between -> re-decide the instrument.
