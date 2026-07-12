# Issue #109 — Follow-up experiment: routing (Haiku attempts, escalate whole task to Sonnet on reject) — the config #41's literature actually supports


## Hypothesis

Issue #41's tiered config (strong plans/validates, weak implements, coach-and-retry) was rejected decisively: quality equal to Haiku-solo at 8.8x Sonnet-solo tokens. The mechanism finding — iterating a weak implementer against a strong critic converges to the implementer's ceiling — leaves the cascade literature's actually-validated shape untested: **routing**. Haiku attempts the task once; a checker decides accept-or-escalate; on escalate, Sonnet redoes the WHOLE task (no coaching). Quality is then bounded below by whichever model ships, not by Haiku's ability to incorporate feedback.

## Why it is cheap to test

`benchmarks/2026-07-10-tiered-execution/` is reusable nearly verbatim: same 8 gradient tasks, same hermetic harness/blind-grade pipeline, and the haiku-solo and sonnet-solo cells ARE the two halves of the routing arm — only the checker calls and the composition are new. Measured baselines: haiku 0.315 frac-met at ~$0.016/cell; sonnet 0.597 at ~$0.055/cell. Routing cost ~= 0.016 + E x (checker + 0.055) for escalation rate E; quality depends entirely on the checker's false-accept rate.

## The known threat (pre-registered up front)

#41 measured the Sonnet validator at **25% false-accept** on final artifacts — under routing, every false-accept ships a Haiku-floor artifact. The experiment's primary secondary-metric must therefore be checker fidelity, and the design should compare checker variants (e.g. Sonnet judge vs. checklist-scored deterministic checks) before any adopt decision. If no checker beats ~10-15% false-accept, routing cannot reach Sonnet-solo quality and the null should be recorded without a full grid.

Decision rule sketch (to be finalized per ADR 0024 before spend): adopt iff frac-met non-inferior to Sonnet-solo (margin -0.05, clustered CI) AND median cost materially below Sonnet-solo. Timing: owner's call; no urgency — Sonnet-solo is the measured frontier and the default meanwhile.

Related: issue #41 (rejected tiered config), ADR 0019/0023/0024/0025/0026.
