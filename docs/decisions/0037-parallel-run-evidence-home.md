---
id: 0037
title: "Parallel-session benchmark evidence lands on main, never lives on a branch or tag"
status: accepted
tier: lite
summary: "The parallel #41 gradient run and its #30 replication record merged from branch claude/issue-41-8awnsc into benchmarks/ on main, ADR-0026-conformed (regenerable prompts/ gitignored; meta.json keeps the run's exact prompts); branch deleted, ADR 0035 repointed. Standing rule: evidence an ADR cites must live on main — a branch reads as work-in-flight and is deletable without review; a tag is even less discoverable. Panel split 2-1 (merge vs tag); owner accepted merge."
---

# 0037 — parallel-run evidence home

- Decision: benchmark evidence cited by an ADR lands on main as an append-only snapshot
  (ADR 0024), conformed to ADR 0026's itemized artifact rules — never left on a branch or a tag
  (less discoverable still; agents don't fetch tags). Applied: claude/issue-41-8awnsc's two
  evidence dirs merged, branch deleted after merge, ADR 0035 repointed.
- Why: ADR 0035's verified numbers and revisit trigger were resolvable only against a ref that
  could vanish without review; on-main is the only home a future session reliably finds.
- Rejected: a tag (less discoverable than a branch — agents don't fetch tags); leaving it on the
  branch (deletable without review, which is the failure this fixes). Panel split 2-1; owner chose merge.
- Enforced: this landing PR; the append-only result-snapshot rule (ADR 0019) + CLAUDE.md Shipping (owner review).
