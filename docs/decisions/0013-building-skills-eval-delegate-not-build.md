---
id: 0013
title: "building-skills evals: delegate execution to skill-creator, own the cost verdict"
status: accepted
tier: lite
summary: "Empirical skill evals are hybrid: execution stays delegated to skill-creator's benchmark harness (paired with/without runs, graded assertions); this repo owns only the schema gate in validate.py and eval_verdict.py, the cost-per-benefit verdict (Wilson CI + delta per 1k chars of SKILL.md body). No owned paired-benchmark harness (ADR 0033 owns the trigger runner). Keeps: author-separation, fresh independent grader, validate.py authoritative, prose vendored."
---

# 0013 — building-skills evals: delegate execution, own the cost verdict

- Decision: delegate execution to skill-creator's benchmark harness (paired baseline + graded
  assertions + aggregate stats); protocol home is
  `skills/building-skills/references/empirical-evals.md`. Own two things only: (1) the schema
  gate — validate.py R7 gates eval artifact shape; (2) the verdict layer —
  `skills/building-skills/scripts/eval_verdict.py` + test, post-processing upstream
  `benchmark.json` only: Wilson 95% CI win rate, mean pass-rate delta, and delta per 1k chars of
  SKILL.md body. Not a CI gate (non-deterministic; only decision logic runs in gates).
- Why: budgets cap cost but nothing measured benefit. Upstream has the expensive machinery but
  not the decision layer. Owning ~150 lines of post-processing buys the verdict without
  maintaining a rival harness against a moving upstream schema.
- Rejected: a full owned paired runner (re-forks upstream execution for zero marginal
  information); adopting upstream as-is (cost-normalization unmet); mirroring the schema into
  docs (drifts on the next upstream change); making eval runs a CI gate (ADR 0012).
- Reopen-if: `eval_verdict.py` breaks on an upstream schema change twice in a row -> reconsider
  owning execution.
- Enforced: validate.py R7 (`validate_test.py`); `eval_verdict.py` + `eval_verdict_test.py`.
