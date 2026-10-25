---
name: red-team
description: Use when a decision, design, or change is about to be accepted and needs an adversary — especially safety-adjacent or assumption-heavy work.
---

# /red-team — the adversary, standalone (Check)

The adversarial leg of the `/decide` panel as a right-sized primitive: run it before accepting
anything whose failure would be expensive.

## Run

1. **Hand over the candidate** — the decision, design, or diff about to be accepted — plus the
   real artifacts it touches. No softening context, no "we already checked X".
2. **Spawn the `red-team` agent fresh** (its prompt owns the attack method).
   A candidate about this loop's own behaviour it will REFUSE (ADR 0093): route it out per the
   `verify` skill's step 2, the claim aimed at what the candidate takes for granted rather than
   at its argument.

## Return

Each break gets a response before proceeding: accept it and fold the fix in, or refute it with
evidence (cite file:line or output). An unanswered break BLOCKS. A `FRAME-UNCHECKED` round names
what stayed unexamined and ends there — reporting zero breaks instead is the exact failure this
token exists to prevent. Fold
accepted breaks into the artifact or ADR itself — a break answered only in conversation is drift.
A fold is work no adversary has seen yet, so run another round; stop at the first round that
changes nothing in the artifact, counting findings you refute with cited evidence as changing
nothing. Gates going green is not that signal, and the rounds spent get disclosed (ADR 0062).
