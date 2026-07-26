---
id: 0035
title: "tiered-agent execution verdict: do not adopt per-task orchestration; tier by work type"
status: accepted
tier: lite
summary: "Issue #41 measured (pre-registered bar): tiered (sonnet plans/validates, haiku implements) fails the cost/time gate outright — 2.94x tokens, 3.22x wall-clock vs sonnet-solo against a <=0.6x bar — with judged quality -0.057. Haiku-solo is 0.36x cost but judged-quality -0.160 (CI excludes zero). DO NOT codify a haiku implementer tier; ADR 0006's split stands, now empirically grounded: haiku mechanical-only, sonnet+ judgment."
---

# 0035 — tiered-agent execution verdict

- Decision: do not adopt per-task tiered orchestration (sonnet plans/validates, haiku implements) or haiku-solo as a general implementer. Pre-registered gate, vs sonnet-solo: tiered used 2.94x tokens / 3.22x wall-clock (bar <=0.6x) for judged quality -0.057; haiku-solo cost 0.36x but judged quality -0.160 (CI excludes zero) — haiku matches sonnet on mechanized/structural expectations, loses on judgment. ADR 0006's model split stands, now empirically grounded: haiku mechanical-only, sonnet+ wherever judgment is the work product.
- Why: the bar was pre-registered before any cell ran (ADR 0024: adopt only what measurably earns its cost); neither configuration did, on two independent runs reaching a compatible verdict.
- Rejected: adopt tiered for its quality gain alone — the issue's premise was cost/time efficiency, paying 2.3x for -0.057 quality is the opposite; difficulty-adjust the bar post-hoc — the exact failure ADR 0024 forbids.
- Reopen-if: a multi-file/agentic workload (this run's single-shot tasks are the pessimal case for orchestration overhead) shows tiered <=0.6x cost at non-inferior quality -> re-test. Haiku pricing/capability shifts materially -> re-run haiku-solo vs sonnet-solo.
- Enforced: `benchmarks/2026-07-10-tiered-execution-fullgrid/aggregate.py`; `benchmarks/2026-07-10-tiered-execution/results.jsonl` (independent replication).
