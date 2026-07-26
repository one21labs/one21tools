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
   A candidate about this loop's own behaviour is beyond a spawned agent's reach — it holds the
   very priors the attack has to target (why: ADR 0093 — the plugin ships no resolver). Send
   that one outside the model lineage instead, aimed at what the candidate takes for granted
   rather than at its argument.

## Return

Each break gets a response before proceeding: accept it and fold the fix in, or refute it with
evidence (cite file:line or output). An unanswered break BLOCKS. With no adversary outside the
lineage reachable, the round returns `FRAME-UNCHECKED` and you name what stayed unexamined —
reporting zero breaks instead is the exact failure this token exists to prevent. Fold accepted
breaks into the artifact or ADR itself — a break answered only in conversation is drift. A fold
is work no adversary has seen yet: run another round, and keep running while a round still turns
something up. Gates going green is not that signal (ADR 0062).
