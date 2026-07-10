---
id: 0029
title: "check-workflow.mjs joins the required gates: workflow syntax + model: on every agent() call"
status: accepted
tier: lite
summary: "Owner call (issue #54): scripts/check-workflow.mjs runs in gates.yml as a required check. Prevent>detect: the #53 defect class (a benchmark workflow agent() without model: silently burning the session model) becomes unmergeable, and workflow scripts get a real syntax check (bare node --check cannot parse their runner-wrapped top-level return/await). The Never rule's test requirement is already met (check-workflow.test.mjs, 7 cases, runs in the same gates job)."
---

# 0029 — check-workflow.mjs is a required CI gate

- Date: 2026-07-09
- Owner: PM (owner call; advisory-vs-gate was #54's question)

Decision + why: wire `node scripts/check-workflow.mjs benchmarks` into `gates.yml`. The lint's
decision logic (findMissingModel, wrapForCheck) is unit-tested in `scripts/check-workflow.test.mjs`,
which the same job already executes — satisfying "never ship a process-gating script without a test
of its decision logic." Cost is one sub-second step; the defect it prevents recurred across 5
merged files before #53 backfilled it. Enforced: gates.yml + scripts/check-workflow.test.mjs.
