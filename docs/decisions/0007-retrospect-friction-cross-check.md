---
id: 0007
title: "Retrospect friction handoff: independent git cross-check, not transcript-as-default"
status: accepted
summary: "A prior /retrospect dropped its top finding because the orchestrator never PERCEIVED it as friction. REJECT transcript-as-default: the spawn prompt is the only orchestrator->subagent channel, so anything passed is orchestrator-SELECTED = curation renamed, never a severed curator/worker. PRIMARY fix: the retrospect AGENT cross-checks the supplied list against the rework / fix-of-a-fix / revert / force-push signals it already finds in git and FLAGS git-visible friction ABSENT from it — an independent second witness at zero new cost. Git-visible class only; the rest stays under a gated extractor trigger."
---

# 0007 — retrospect friction handoff: independent git cross-check

- Date: 2026-06-29
- Owner: PM
- Panel: 3 fresh lenses converged against a transcript default; verifier PASS; red-team applied (HIGH break folded in). Inherits 0001/0002, lenses per 0004.
- Context: a prior `/retrospect` dropped its highest-cost finding (an undocumented squash-merge trap) from the list handed to the `retrospect` agent — root cause: the orchestrator never PERCEIVED it as friction, upstream of any curate step. The agent cannot see the chat (tools: Read/Grep/Glob/Bash); the orchestrator authors AND curates in one ephemeral turn. User ask: make raw/abridged transcript handoff the DEFAULT.

## Decision
1. **REJECT transcript-as-default.** The spawn prompt is the only orchestrator->subagent channel, so anything passed is orchestrator-SELECTED — an "abridged transcript" is just "curate less aggressively"; it renames curation, never severs curator from worker. A raw default also harms every consumer: secrets (customer data into a subagent each PR), cost (window blowup vs the sonnet tier, ADR 0006), dilution. "Abridged caught it once" is one draw from a graded-own-homework channel, not reproducible.
2. **PRIMARY fix: the retrospect AGENT becomes a second, independent reader.** It cross-checks the supplied friction list against the rework / fix-of-a-fix / revert / force-push signals it independently finds in git, and FLAGS any git-visible friction ABSENT from the list. An independent DATA SOURCE (git, not orchestrator perception) is a structurally-separate witness at zero new channel/secrets/cost. Home: `retrospect.md` Method.
3. **SECONDARY (bookkeeping, not the cure): enumerate-before-dedupe in step 4** — list every DISTINCT perceived friction before the agent dedupes at step 5. This re-surfaces only friction already perceived; the demonstrated miss is what (2) fixes. Home: `SKILL.md` steps 4-5.
4. No version bump (CLAUDE.md exempts meta/tooling).

## Justification
The red-team break is correct: the trap was never perceived, so a fix that only re-orders perceive-then-cut is theater — and a "fixed" label suppresses user vigilance (detect-not-prevent, forbidden by CLAUDE.md). The cure must add a witness with an INDEPENDENT data source; the cross-check is a near-free extension over signals the agent already computes, and makes the gated escalation trigger operable.

## Assumptions
- **[checkable] WEAKEST: the cross-check catches the demonstrated-class omission, NOT all perception failures.** A friction with no git fingerprint (pure derivation-effort or near-miss) stays invisible to both the orchestrator and the agent's git scan. TEST (owner: verifier): the clause names concrete git signals and a flag-if-absent action, and cannot pad findings (the flag is advisory, fed into step 5's systemic filter). REVISIT-IF a `/retrospect` drops a friction that LEFT a git fingerprint -> mis-specified detector; a non-git-visible one -> escalate per 0014. — result: pending.
- **[verified] fix applied, two homes (two concerns):** `retrospect.md` Method gains a "friction cross-check (independent witness)" bullet; `SKILL.md` step 4 enumerates each distinct friction before the step-5 dedupe, and step 5 drops non-systemic items before the at-least-two count (files own the wording).
- [checkable-doc] does NOT trip ADR 0006: the cross-check only corroborates signals the agent ALREADY computes (no new input class), and step 4's "distinct" drops the redundant-variant trivia that would load sonnet's weakest systemic-vs-noise axis. — owner: verifier.
- [checkable] adr-lint stays green; the edit adds no script/CI. — owner: verifier.

## Rejected alternatives
- **Enumerate-then-curate as the PRIMARY fix (the original 0007 decision)** — cosmetic for the demonstrated mode: authored+curated in one turn with no second reader, it only re-surfaces already-perceived friction. Demoted to bookkeeping.
- **Raw / abridged transcript (the user's literal ask)** — enlarges the SAME author's selection without severing curator from worker; pays the Decision-1 harms and leans toward the synthesis the sonnet tier was cut against (ADR 0006). Abridged is worst (false-confidence halo).
- **Independent extractor reading a raw transcript (the only full cure)** — severs curator from worker for ALL perception failures, but is gated on unproven raw-transcript-channel feasibility and re-opens ADR 0006. Deferred to the trigger below.

## Revisit triggers
- **Feasibility-gated full fix:** evaluated + re-deferred in 0014 — the raw-transcript channel is not yet clean (unversioned JSONL schema). Re-fire per 0014's sharpened precondition (a documented+versioned schema or a transcript-query API), re-opening ADR 0006.
- A `/retrospect` drops a git-VISIBLE friction despite the cross-check -> mis-specified clause; a non-git-visible one -> escalate per 0014.
- ADR 0006's A/B test lands sonnet-inadequate, OR retrospect is wired to auto-apply a finding -> re-evaluate this contract and the tier together.

## Act (post-ship — 2026-07-01, PR #11)
- [outcome] weakest [checkable] (cross-check clause) — still-open.
- [pivot] L36 trigger fired -> re-deferred to 0014 (channel not yet clean — unversioned schema).
