---
name: red-team
description: Use when a decision, design, or change is about to be accepted and needs an adversary — especially safety-adjacent or assumption-heavy work. Spawns the fresh red-team agent to break it against the real product; every break must be answered or folded in.
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
   Candidate is a claim about this loop's own behaviour? Spawn from a different model lineage
   (a bigger sibling or a clean context is the same lineage) and point it at what the candidate
   takes for granted, not at its argument — an adversary holding the same priors breaks the
   reasoning and leaves the framing standing (ADR 0093). No second lineage available: "no breaks
   found" reports as FRAME-UNATTACKED, which is not a clean bill.

## Return

Each break gets a response before proceeding: accept it and fold the fix in, or refute it with
evidence (cite file:line or output). An unanswered break BLOCKS. Fold accepted breaks into the
artifact or ADR itself — a break answered only in conversation is drift.
