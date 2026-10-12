---
id: 0101
title: "#317 expectation coupling: confirmed; claims scoped to own expectations, executable outcomes piloted on code-standards"
status: accepted
tier: lite
summary: "The pre-registered provenance split fired (evals written with the skill in view score far above new blind ones). Claims now read 'beats bare against the skill's own expectations'; evals stay blind-authored with the split reported per batch; executable outcomes are piloted for code-standards first."
---

# 0101 — expectation coupling: scope the claims, pilot executable outcomes

- Decision: (1) new evals are blind-authored; every batch reports the delta split by eval
  provenance next to overlap.json; (2) a KEEP reads "beats bare against the skill's own
  expectations" (README measured block); (3) pilot executable outcomes (seeded defects or hidden
  tests, a script grader) for code-standards; building-skills (validate.py + trigger eval)
  only after the pilot discriminates; doctrine skills stay rubric-graded.
- Why: the pre-registered split fired (`benchmarks/2026-10-12-g8-shortfall/README.md` owns the
  numbers). Provenance and difficulty are confounded; a script grader is immune to coupling
  either way. Panel (adopter, economist, lean, operator) converged.
- Rejected: a difficulty-matched blind re-author (30 of 35 blind tasks saturated; matching
  selects on bare outcomes; either answer leads to the same build). Retiring claims for a
  smaller blind lift (no headroom is not no value). A trigram-overlap gate (a floor).
- Reopen-if: the pilot's bare pass rate is >= 0.85 on 70% of drafted tasks, or its delta CI
  includes 0 at G>=8 -> stop building, keep (2). A CI excluding 0 -> upgrade the claim.
- Enforced: `README.md` (measured block); `benchmarks/2026-10-12-g8-shortfall/aggregate.py`
