---
name: verify
description: Use when a claim, a fix, or produced output needs independent confirmation before you rely on it or ship it. Spawns the fresh verifier agent to reproduce load-bearing claims against real code and output; returns PASS or BLOCK findings.
---

# /verify — the independent gate, standalone (Check)

The verification gate of the `/decide` panel as a right-sized primitive: run it on any claim
set worth an independent check — a "the bug is fixed", a review finding, an assumption —
without the full ceremony. `/decide` composes it over every ADR.

## Run

1. **State the claim set.** Each load-bearing claim + where it should be observable (file,
   command, output). Include any `[checkable]` assumptions to check.
2. **Spawn the `verifier` agent fresh** — pass the claims and the paths, never the desired
   verdict or the reasoning that produced them (uncontaminated is the point).
3. It reproduces every claim against the real code and produced output — the method and grading
   rules live in the `verifier` agent's own prompt, not here.

## Return

PASS, or BLOCK with findings. The agent reports per-claim verdicts plus a BLOCKERS list; YOU
synthesize the label — no BLOCKERS = PASS. A verified correctness/safety finding stands — fix the artifact,
don't argue the catch; priority overrules don't apply to verified findings (`/decide`'s rule).
When a fresh finding supersedes a shared handoff note (a verdict, an assumption result),
overwrite it before the next agent reads it — a stale verdict a sibling consumes is drift.
