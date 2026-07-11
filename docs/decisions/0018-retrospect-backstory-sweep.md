---
id: 0018
title: "retrospect sweeps the diff's doc text for git-tellable backstory"
status: accepted
summary: "Add one signal to the retrospect agent's git-signal list: git-tellable backstory in the range's CHANGED doc text (how-it-got-here narration, prior-state retelling — git history owns it). Budget-neutral: the agent sat at 2989/3000, so low-value wording was compressed to fit (0009's lean-prompt budget working as intended). Not an adr-lint rule — backstory is substance, not shape. One home: the agent's Method; the skill's step-2 list is not extended."
---

# 0018 — retrospect sweeps shipped doc text for backstory muda

- Date: 2026-07-07
- Owner: PM
- Panel: owner-direct — review feedback on an open PR (backstory in an ADR Context line reached owner review; owner set the requirement: retrospect finds this before it ships); gates ran as Check.
- Context: CLAUDE.md names git-tellable backstory cut-on-sight muda, but no retrospect step operationalized it — the agent's signals covered git EVENTS (fix-of-a-fix, reverts, repeat-touch, drift) and session friction, never the diff's own doc TEXT. A pre-PR retrospect passed an ADR amendment whose Context narrated fork history and restated a claim homed elsewhere; the owner caught it in review. The author-orchestrator is structurally blind here (it wrote the narration); the fresh-eyes analyst is the right net.

## Decision
1. **One signal clause in the retrospect agent's git-signal list** (`pdca-workflow/agents/retrospect.md`
   Method — full clause text there): the diff's own changed doc text now gets swept for backstory,
   citing CLAUDE.md's cut-on-sight list. The agent's Method is the analysis home; the `/retrospect`
   skill's step-2 orchestrator list is NOT extended (it pre-surfaces git-log signals; the text sweep
   needs no pre-surfacing, and a second list entry would extend an existing near-mirror).
2. **Budget-neutral edit.** The agent sat at 2989/3000 (0009 cap), so the clause was paid for by compressing restatement and flourish (friction examples restated from the skill; a redundant identity line; verbose tails). Compress-don't-grandfather is 0009's intent.
3. **Not a lint rule.** Backstory is SUBSTANCE, not shape (0003's presence-vs-substance split): a regex over "was/previously" would false-positive legitimate prose and miss real narration. The judgment sweep belongs to the analyst agent.

## Justification
The failure class shipped once and was caught only by owner review — the most expensive gate. The fix is one prompt clause at the existing analysis home: near-zero cost, no new machinery, and it converts an inviolable (CLAUDE.md muda list) into a checked step on the path every PR already walks (`/retrospect` before opening).

## Assumptions
- [checkable] the agent stays under its 3000-char budget and every gate (validate.py, adr-lint, node tests) is green with the clause landed — owner: gates; result: green.
- [checkable] the clause would have caught the shipped instance — a fresh retrospect agent, run on the offending range, flags the ADR Context narration — owner: verifier (fresh-eyes run on the range); result: pending (next `/retrospect` on a doc-touching branch is the live test; the signal names that exact pattern).
- [unverifiable] a one-clause sweep is enough net — REOPEN-IF git-tellable backstory reaches owner review again after this lands; then consider a dedicated pre-PR doc-review step, not a bigger prompt.

## Rejected alternatives
- An adr-lint backstory regex — substance-not-shape; false-positives on legitimate prose, misses real narration; a gating script would also demand a decision-logic test for an undecidable predicate.
- Extending the skill's step-2 list instead — restates the agent-owned analysis method (the skill itself says don't), and the orchestrator already failed as the author; fresh eyes are the point.
- Raising the agent char budget — grandfathers bloat; 0009 chose compress-under-cap.

## Revisit triggers
- Backstory reaches owner review again -> the REOPEN-IF above (dedicated review step).
- The agent budget blocks a future load-bearing signal -> reopen 0009's cap, not this ADR.
