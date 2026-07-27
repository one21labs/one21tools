---
id: 0012
title: "Char-budget gates run as a required CI check"
status: accepted
tier: lite
summary: "Wire the existing gate scripts into one GitHub Actions workflow (.github/workflows/gates.yml) on every PR and push to main, marked required in branch protection. Closes the PR 13 review finding that ADR 0008/0009 describe a hard, CI-failing cap while no CI invoked any gate script."
---

# 0012 — the gates actually gate: required CI

- Date: 2026-07-01
- Decision: one `gates` workflow (`.github/workflows/gates.yml`) on `pull_request` + `push` to main. Which gates run, and how, lives in gates.yml — the SSoT; nothing here mirrors a command. Zero new dependencies (runner-preinstalled python3 + node). `gates` is the required check in branch protection; `claude-review` stays advisory.
- Why: ADR 0008/0009 record CI-failing char caps, but the only workflow was advisory — every gate script ran by hand, so an over-budget artifact could merge green.
- Rejected: soften the 0008 "CI-failing" claim instead — the gates exist and are tested; wiring them is cheaper than weakening the record. Git hooks — client-side only, a clone without hooks bypasses them. Fold the gates into claude-review.yml — that workflow is advisory by design and must not depend on a token.
- Reopen-if: the workflow's runtime or flakiness materially slows PRs -> split or cache. A consumer installs the plugins without GitHub -> document the manual gate invocation as their required-check equivalent.
- Enforced: `.github/workflows/gates.yml`.
