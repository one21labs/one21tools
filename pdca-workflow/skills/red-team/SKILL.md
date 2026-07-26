---
name: red-team
description: Use when a decision, design, or change is about to be accepted and needs an adversary — especially safety-adjacent or assumption-heavy work. Spawns the fresh red-team agent to break it against the real product; every break must be answered or folded in, and a self-referential candidate with no cross-lineage adversary returns FRAME-UNCHECKED.
---

# /red-team — the adversary, standalone (Check)

The adversarial leg of the `/decide` panel as a right-sized primitive: run it before accepting
anything whose failure would be expensive. `/decide` requires it (with `tech-lead`) whenever an
ADR folds a safety caveat in as a BLOCKER.

## Run

1. **Hand over the candidate** — the decision, design, or diff about to be accepted — plus the
   real artifacts it touches. No softening context, no "we already checked X".
2. **Spawn the `red-team` agent fresh.** Its only job is to BREAK the candidate against the
   real product — abuse cases, boundary breaks, wrong-assumption probes — grounded in code.
   A candidate about this loop's own behaviour it will REFUSE — it holds the very priors the
   attack has to target (class + why: ADR 0093). Route that one to an adversary of another
   lineage: `node "${CLAUDE_PLUGIN_ROOT}/scripts/crosscheck.mjs" --claim-file <file>`, with the
   claim written to aim at what the candidate takes for granted rather than at its argument. It
   answers from whichever foreign CLI this machine has, or exits 3 — `FRAME-UNCHECKED`. Record
   the lanes probed (`--list`); "nobody available" asserted without probing is not a result.

## Return

Each break gets a response before proceeding: accept it and fold the fix in, or refute it with
evidence (cite file:line or output). An unanswered break BLOCKS. A `FRAME-UNCHECKED` round names
what stayed unexamined and ends there — reporting zero breaks instead is the exact failure this
token exists to prevent, and it is never a reason to re-run against the same lineage. Fold
accepted breaks into the artifact or ADR itself — a break answered only in conversation is drift.
A fold is work no adversary has seen yet, so run another round; stop at the first round that
changes nothing in the artifact, counting findings you refute with cited evidence as changing
nothing. Gates going green is not that signal, and the rounds spent get disclosed (ADR 0062).
