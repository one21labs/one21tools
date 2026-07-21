---
description: Make Shit Happen — pick the highest-value open work item and ship it end to end, autonomously.
argument-hint: [optional target — issue number, file, or task]
---

Make Shit Happen: ship ONE work item end to end, autonomously, right the first time.

Target: $ARGUMENTS — if empty, survey this repo's open work (`gh issue list`, open PRs, pending
items the project docs point at), pick the best value-for-effort item, and state in one line why
it won.

Execute under the repo's standing rules (CLAUDE.md and the homes it cites are loaded — follow
them, never restate them). Do not ask permission for reversible steps; stop only for a
destructive action or a scope call only the owner can make. One item per invocation — name the
runner-up, do not start it.

Close with the plain summary: what shipped, its value in owner terms, what the owner must do
next.
