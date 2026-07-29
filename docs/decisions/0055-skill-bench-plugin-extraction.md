---
id: 0055
title: "skill-bench plugin: extract the measurement harness, add a cross-family judge and a rented execution substrate"
status: accepted
tier: lite
summary: "Extract the hermetic skill-measurement harness into a standalone `skill-bench` marketplace plugin per #170, and fold in two capabilities the #172 evidence justifies: (1) a CROSS-FAMILY judge (default auto) as a first-class grader, after a 72-cell prototype showed the same-family opus judge inflated absolute rates ~20pp; (2) a rented execution SUBSTRATE (promptfoo/Inspect AI) under the bespoke causal+pre-registration layer."
---

# 0055 — skill-bench plugin: extraction + cross-family judge + rented substrate

- Date: 2026-07-13 (accepted via ADR 0063)
- Decision: (1) extract into a `skill-bench` plugin housing `benchmarks/lib/*` + tests and the trigger runner; method references stay in `building-skills`, skill-bench references them. (2) a cross-family judge as a first-class, DEFAULT-ON grader (`--judge`, default auto); on divergence, surface via a `judge-divergence` diagnostic, don't average. (3) a rented execution substrate (promptfoo default; inspect-ai/claude/grok as options) behind a `hermetic_driver`, UNDER the bespoke causal layer (arms, blind.py, cost_gate, verdict.py, prosecutor). (4) UX: one explicit-invoke `/bench` skill, subcommands `skill`/`verdict`/`trigger`.
- Why: same-family judging is a MEASURED confound (72-cell prototype: opus ~20pp more lenient, kappa 0.575). Comparative-claim scope corrected by ADR 0096.
- Rejected: keep same-family (opus-only) judging — the measured confound this fixes. Build a fully bespoke tracing/CI layer — commodity parts are cheaper rented.
- Reopen-if: a rented substrate costs more to maintain than the harness it replaces -> drop it, keep the causal layer standalone.
- Enforced: `skill-bench/.claude-plugin/plugin.json`. WEAKEST assumption (grok CLI viability) DISCHARGED 2026-07-14.
