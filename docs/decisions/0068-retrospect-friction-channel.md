---
id: 0068
title: "Retrospect friction channel: Phase-0 kill test before any ledger/blind-first machinery"
status: accepted
tier: lite
summary: "Route #189's hypothesis (a mechanical friction ledger beats orchestrator-curated summaries) through a zero-spend Phase-0 test on existing transcripts. Ledger ships only if it surfaces curated-omitted, finding-grade friction; blind-first ordering additionally needs an ADR 0024 measured run."
---

# 0068 — retrospect friction channel: gate before machinery

- Decision: Phase 0 (zero new generation, pre-registered before analysis) compared a mechanical
  friction ledger (from each session's transcript JSONL: tool errors, hook denials, nonzero exits)
  against the curated friction list the retrospect agent actually received, over the 5 most recent
  sessions with a recorded run. Frozen bar: the ledger surfaces >=1 finding-grade item (routable
  to a home, benign retries excluded) the curated list omitted, in >=3 of 5, classified blind to
  which channel produced it — PASSED (3/5). Ledger ships first, pre-registered per ADR 0065/0066.
  Blind-first reordering is separate and costlier, and additionally needs an ADR 0024 measured
  run — never on assertion.
- Why: the bias mechanism is structural (agenda-setting by the reviewed party — #189: 7/9 retro
  threads traced to the orchestrator's list), but the ledger's ADDED value is empirical and the
  data to test it already existed — the cheap gate had to precede any build (ADR 0062).
- Rejected: build ledger + blind-first now (adopt-on-assertion); decline (leaves the bias in the
  one process instrument run on every PR); measure blind-first before the ledger gate.
- Reopen-if: a second blind-classification pass flips the Phase-0 verdict -> the finding-grade
  bar didn't control the hindsight confound; re-run.
- Enforced: `benchmarks/2026-07-15-pdca-retrospect-friction-phase0/`; Phase-1 ledger
  pre-registration gated on ADR 0065/0066 before any retrospect skill/hook edit.
