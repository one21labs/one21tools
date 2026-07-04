---
id: 0012
title: "Char-budget gates run as a required CI check"
status: accepted
summary: "Wire the existing gates — validate.py over every skill folder, validate_test.py, the JS gate tests, adr-lint (ADR + CLAUDE.md + agent caps) — into one GitHub Actions workflow (.github/workflows/gates.yml) on every PR and push to main, marked required in branch protection. Closes the PR 13 review finding that ADR 0008/0009 describe a hard, CI-failing cap while no CI invoked any gate script."
---

# 0012 — the gates actually gate: required CI

- Date: 2026-07-01
- Owner: PM (decided in PR 13 review: wire CI rather than soften the 0008 prior-art claim)
- Context: ADR 0008/0009 record CI-failing char caps, but the repo's only workflow was the advisory
  claude-review; every gate script ran by hand ("run adr-lint pre-merge" — a convention, not a
  check). An over-budget artifact could merge green.

## Decision
One `gates` workflow (`.github/workflows/gates.yml`) on `pull_request` + `push` to main:
validate.py over each `skills/*/` and `pdca-workflow/skills/*/`; `validate_test.py`;
`node --test pdca-workflow/scripts` (char-budget + adr-lint decision logic); adr-lint over
`docs/decisions`. Zero new dependencies — runner-preinstalled python3 + node, matching the gate
scripts' own zero-dep constraint. `gates` becomes the required check in branch protection;
claude-review stays advisory (its own header demands exactly this split).

## Assumptions
- [checkable] the workflow fails on an over-budget artifact: each gate script exits nonzero on a
  violation (validate_test.py + the JS tests pin that decision logic, including positive
  detection) and the workflow runs them with no continue-on-error. — owner: verifier.
- [unverifiable] pull_request + push-to-main is the right trigger set. REOPEN-IF a gate regression
  reaches main through any other path (a direct push before protection, a merge queue).

## Rejected alternatives
- **Soften the 0008 "CI-failing" claim instead** — the gates exist and are tested; wiring them is
  cheaper than weakening the record.
- **Git hooks** — client-side only; a clone without hooks bypasses them.
- **Fold the gates into claude-review.yml** — that workflow is advisory by design and skips
  cleanly without a secret; enforcement must not depend on a token.

## Revisit triggers
- The workflow's runtime or flakiness materially slows PRs -> split or cache.
- A consumer installs the plugins without GitHub -> document the manual gate invocation as their
  required check equivalent.
