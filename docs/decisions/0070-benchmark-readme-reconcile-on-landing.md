---
id: 0070
title: "Benchmark READMEs: landing results retires prep-era text in the same PR"
status: accepted
tier: lite
summary: "A PR that lands a run's results.jsonl into a dated dir whose README still carries pre-registration 'no run executed'/PREP-ONLY language must update that language in the same PR. Doc rule in benchmarks/README.md, not a new gate. From PR #216's retrospective (issue #215: both 10-Jul occurrences of the phrasing shipped beside completed results)."
---

# 0070 — benchmark README reconciles with landed results in the same PR

- Decision: when a PR lands a run's results into a dated benchmark dir, any
  pre-registration "no run executed" / PREP-ONLY language in that dir's README
  is updated in the SAME PR. The append-only rule (ADR 0026/0041) freezes a
  dir at merge, not at authoring — reconciling before merge is not a retrofit;
  after merge, the fix is an appended dated correction.
- Why: 2/2 corpus occurrences of the phrasing were wrong the day they merged
  (PRs #102/#103 landed completed results beside prep-only text; issue #215) —
  a reader of the README alone concludes the run never happened. A doc rule at
  the scaffold-convention home suffices; ADR 0041 already rejected a
  detection gate at this volume (prevent > detect, n~2 dirs/day).
- Enforced: `benchmarks/README.md` (the ADR 0041 scaffold-convention home) —
  reviewer-checked, no script.
