---
id: 0061
title: "Operationalize the #172-gating experiments: #186 Phase-0 DoD-check + #185 poker arm P"
status: accepted
tier: lite
summary: "Operationalized the owner-frozen #186/#185 pre-regs (norm input, dual-family classifier, within-arm three-state test; framer-fixed options, 3 reps + MDE, fresh A, $150 gate, outcome-spread-only bar). Outcome: #186 Phase-0 SUPPORTED (bare arm only); #185 H1 FALSIFIED judge-robust and its dual-cost premise violated. Pivoted #172's closure to ADR 0062."
---

# 0061 — priority experiments (#186 Phase-0, #185) operationalization

- Decision: operationalized #172's two frozen pre-regs. **#186 Phase-0**: norm (arm-blind) input, dual-family classifier on model-graded items (cross-family disagreement excluded, not counted), within-arm/within-corpus three-state test (n>=5 floor else INCONCLUSIVE) on full fraction-met. **#185**: framer-required option enumeration, 3 reps with stated MDE, fresh arm-A pricing, a $150 cost ceiling gated by a $10 pilot, and outcome-spread as the sole P-vs-C-computable bar. Outcome (Act): #186 Phase-0 SUPPORTED, bare arm only, 20.1% cross-family disagreement excluded; #185 H1 FALSIFIED judge-robust (a decider-capture defect) and the dual-cost premise violated ($16.82 vs the assumed <$1). Pivoted #172's plateau cut-vs-keep call to ADR 0062.
- Why: cost x validity per call; the owner-frozen kills (fraction-met, dual-judge, pre-registered bars) applied verbatim rather than re-litigated.
- Rejected: single-family classification (underpowers judge bias); pulling bucket counts before the floor (violates pre-reg blindness); hard-pair as #186's kill (silently swaps the owner-frozen kill).
- Reopen-if: discharged — outcome recorded above; superseded by ADR 0062 for what comes next.
- Enforced: `benchmarks/2026-07-13-pdca-decide-armd/grid_armd.py` + `results.json`; `benchmarks/2026-07-12-pdca-decide-outcome/README.md`.
