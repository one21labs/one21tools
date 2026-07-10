# Pre-registration — pre-run discipline for paid experiments

Read this when designing or pre-registering a paid experiment (a benchmark grid, an ablation,
any run that spends real executor budget). It extends ADR 0024 (cost-justification) and ADR
0025 (verdict methodology) UPSTREAM of the run; [empirical-evals.md](empirical-evals.md) owns
the measurement protocol itself.

## Pre-registration cites the settled methodology

A pre-registration CITES the verdict methodology — fraction-met headline with binary
all-expectations-met as secondary (ADR 0025), the eval-clustered CI unit (ADR 0019), the
sequential-escalation rule, cost accounting (ADR 0024) — instead of restating any of it, and
never names a metric the ADRs have superseded. A pre-reg whose stated metric predictably
floors (binary pass-rate floored three benchmarks running) invites exactly the fishing
accusation pre-registration exists to prevent.

## Cost-pilot before any grid

Run 2-3 cells of the MOST EXPENSIVE arm first; if any pre-registered gate is already decidable
from the pilot, stop and record the verdict. Unconditional — it reorders spend, it adds none.
(Live instance: a 216-cell tiered grid whose cost gate was decidable after ~5 cells, ~$0.60 —
roughly 90% of executor spend was saveable.)

## Prior-art pass before designing a paid experiment

Before designing, ask: is the answer already known, and in what parameter regime does it turn?
If known, test the OPEN regime, not the settled one. Size-gated — required only above a
non-trivial spend threshold, never on small pilots (mandating research before trivial runs is
gold-plate).
