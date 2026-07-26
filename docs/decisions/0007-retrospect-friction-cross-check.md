---
id: 0007
title: "Retrospect friction handoff: independent git cross-check, not transcript-as-default"
status: accepted
summary: "A prior /retrospect dropped its top finding because the orchestrator never PERCEIVED it as friction. REJECT transcript-as-default: the spawn prompt is orchestrator-SELECTED, never a severed curator/worker. PRIMARY fix: the retrospect AGENT cross-checks the supplied list against rework/fix-of-a-fix/revert/force-push signals it already finds in git and FLAGS git-visible friction ABSENT from it — an independent witness at zero new cost."
---

# 0007 — retrospect friction handoff: independent git cross-check

- Date: 2026-06-29
- Context: a prior `/retrospect` dropped its highest-cost finding (an undocumented squash-merge
  trap) — root cause was the orchestrator never PERCEIVING it as friction, upstream of any curate
  step. The agent cannot see the chat (tools: Read/Grep/Glob/Bash); the orchestrator authors AND
  curates in one ephemeral turn.

## Decision
1. **REJECT transcript-as-default.** The spawn prompt is the only orchestrator->subagent channel,
   so anything passed is orchestrator-SELECTED — an "abridged transcript" just renames curation.
   A raw default also harms every consumer: secrets exposure, cost (ADR 0006), dilution.
2. **PRIMARY fix: the retrospect AGENT becomes a second, independent reader.** It cross-checks the
   supplied friction list against the rework / fix-of-a-fix / revert / force-push signals it
   independently finds in git, and FLAGS any git-visible friction ABSENT from the list — a
   structurally-separate witness at zero new channel/secrets/cost. Home: `retrospect.md` Method.
3. **SECONDARY (bookkeeping): enumerate-before-dedupe in SKILL.md step 4.**

## Justification
The trap was never perceived, so reordering perceive-then-cut is theater; the cure needs a witness
with an INDEPENDENT data source, near-free over signals the agent already computes.

## Assumptions
- [checkable] **WEAKEST: the cross-check catches the demonstrated-class omission, not all
  perception failures.** A friction with no git fingerprint stays invisible to both readers.
  REOPEN-IF a `/retrospect` drops a friction that LEFT a git fingerprint -> mis-specified
  detector; a non-git-visible one -> escalate per 0014. result: pending the next /retrospect run.
- [checkable-doc] does NOT trip ADR 0006 — corroborates signals the agent already computes
  (no new input class). — owner: verifier.

## Rejected alternatives
- Enumerate-then-curate as the primary fix — cosmetic, only re-surfaces already-perceived friction.
- Raw / abridged transcript — enlarges the same author's selection; pays the Decision-1 harms.
- Independent extractor reading a raw transcript — the full cure, but gated on unproven
  raw-transcript-channel feasibility.

## Revisit triggers
- Feasibility-gated full fix: re-fire per 0014's precondition, re-opening ADR 0006.
- A `/retrospect` drops a git-visible friction despite the cross-check -> mis-specified clause.

## Act (post-ship — 2026-07-01, PR #11)
- [outcome] weakest [checkable] (cross-check clause) — still-open.
- [pivot] the trigger above fired -> re-deferred to 0014 (channel not yet clean).
