---
name: verify
description: Use when a claim, a fix, or produced output needs independent confirmation before you rely on it or ship it. Spawns the fresh verifier agent to reproduce load-bearing claims against real code and output; returns PASS, BLOCK findings, or FRAME-UNCHECKED for a claim no independent checker could reach.
---

# /verify — the independent gate, standalone (Check)

The verification gate of the `/decide` panel as a right-sized primitive: run it on any claim
set worth an independent check — a "the bug is fixed", a review finding, an assumption —
without the full ceremony. `/decide` composes it over every ADR.

## Run

1. **State the claim set.** Each load-bearing claim + where it should be observable (file,
   command, output). Include any `[checkable]` assumptions to check.
2. **Spawn the `verifier` agent fresh** — pass the claims and the paths, never the desired
   verdict or the reasoning that produced them (uncontaminated is the point). A claim about this
   loop's own behaviour is one the agent will REFUSE — it inherits the maker's lineage (ADR 0093
   defines the class and owns why). Route that claim out instead, don't just note it:
   `node "${CLAUDE_PLUGIN_ROOT}/scripts/crosscheck.mjs" --claim-file <file>` finds whichever
   foreign-vendor CLI this machine has, sends the claim, and reports which model answered. Exit 3
   is `FRAME-UNCHECKED` — no lane, or a lane that answered from the maker's own family. Record the
   lanes it probed (`--list`); an unprobed FRAME-UNCHECKED is indistinguishable from not looking.
3. It reproduces every claim against the real code and produced output — the method and grading
   rules live in the `verifier` agent's own prompt, not here.

## Return

PASS, or BLOCK with findings. The agent reports per-claim verdicts plus a BLOCKERS list; YOU
synthesize the label — no BLOCKERS = PASS. A claim step 2 could not route out is
`FRAME-UNCHECKED`: it leaves the PASS set, raises no BLOCKER, and travels with the verdict so
the next consumer sees which claim went unchecked. That closes the claim with its gap recorded —
it is never grounds for another round against the same lineage. A verified correctness/safety finding
stands — fix the artifact,
don't argue the catch; priority overrules don't apply to verified findings (`/decide`'s rule).
When a fresh finding supersedes a shared handoff note (a verdict, an assumption result),
overwrite it before the next agent reads it — a stale verdict a sibling consumes is drift.
