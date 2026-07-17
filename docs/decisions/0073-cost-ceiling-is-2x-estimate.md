---
id: 0073
title: "Benchmark cost gate: ceiling_usd = 2x the pre-registered estimate"
status: accepted
tier: lite
summary: "The mechanical generation cost gate (cost_gate.ceiling_usd) is set to 2x the pre-registered notional estimate — the >2x stop-rule of record — never the estimate itself. From PR #219's retrospective: encoding the estimate band's top ($12) as the ceiling forced a recorded mid-run revision when the pilot projected $15, though the stop rule allowed up to $24."
---

# 0073 — ceiling_usd = 2x estimate, never the estimate

- Decision: every benchmark's `metadata.json:cost.ceiling_usd` is derived as 2x the
  pre-registered notional estimate, so the mechanical gate and the pre-registered stop rule
  (ADR 0066's >2x shape, extended here from grading to generation) are the SAME number. The
  estimate itself is recorded separately in `estimate_note`/pre-registration.
- Why: PR #219's run encoded the estimate band's top as the ceiling; the pilot's $15 projection
  then tripped the gate inside the allowed continue zone ($24), forcing a mid-run recorded
  ceiling revision — transparent but avoidable, and the ambiguity recurs for every future
  bench author. One derivation rule removes the judgment call.
- Enforced: `skill-bench/skills/bench/references/cost-and-verdict.md` (the cost-rule SSoT) +
  the `skill-bench/templates/grid.py` metadata docstring pointing at it. Doc rule, no new gate
  machinery (ADR 0066 precedent).
