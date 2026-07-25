---
description: Make Shit Happen — pick the highest-value open work and ship one cohesive package end to end, autonomously.
argument-hint: [optional target(s) — issue numbers, file, or task; naming several declares them one package]
---

Make Shit Happen: ship ONE cohesive work package end to end, autonomously, right the first time.

Target: $ARGUMENTS — several named targets are the owner's declared package; take them together.
If empty, survey this repo's open work (`gh issue list`, open PRs, pending items the project
docs point at), pick the best value-for-effort item, and state in one line why it won. A further
issue may join a surveyed package only on necessity: shipping the lead means editing a file that
issue's fix must also edit, or makes that issue's recorded fix wrong. Similarity is never
enough. Name every joined issue and its admitting coupling in the PR body and the closing
summary; when in doubt, it stays out.

Execute under the repo's standing rules (CLAUDE.md and the homes it cites are loaded — follow
them, never restate them). Where those rules call for independent judgment — advisors,
verifiers, red-team — run the lanes in parallel, never as co-authors of separate items. Do not
ask permission for reversible steps; stop only for a destructive action or a scope call only the
owner can make. One package per invocation — name the runner-up, do not start it; if the
session's PR is still open, the repo's shipping rules decide where the next package lands.

Close with the plain summary: what shipped, its value in owner terms, what the owner must do
next.
