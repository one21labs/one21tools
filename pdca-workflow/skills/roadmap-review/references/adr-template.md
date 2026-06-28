# Decision log — Architecture Decision Records (ADRs)

An **ADR** is a dated, append-only note capturing one judgment call: its context, the decision,
the justification, the assumptions (tagged), and the triggers that would reopen it. One file per
decision: `NNNN-slug.md` (zero-padded, monotonic). Produced by the `pm` agent in the
`/roadmap-review` flow.

This file is the canonical ADR template. `/pdca-init` copies it into a new project as
`docs/decisions/README.md` (which also holds the shared-assumption register, below).

Rules:
- The roadmap references a decision by ID; it never re-states or re-argues it.
- **Don't narrate backstory.** Git history is the SSoT for how a decision got here — retired /
  renumbered IDs, what-folded-into-what, draft history, "Learned" logs are drift; state the
  current decision, cut the story.
- Every record carries justification AND tagged assumptions + revisit triggers.
- **One ADR per PR (max).** A PR captures one decision in one ADR. If it must change before the PR
  merges, **revise it in place** — never add a second ADR to amend or overrule a still-unmerged
  sibling (proliferation; the draft history is squashed away anyway). Separate decisions = separate PRs.
- **Rationalize in place.** Correct, re-sequence, or fold an amendment into the ADR it touches — on
  the next PR that works that area. Don't spawn a new ADR to amend / correct / re-sequence an
  existing one (an "amends NNNN" ADR folds into NNNN). Reserve `status: superseded by NNNN` for a
  decision *wholly retired* by a separate one.
- **No version numbers in an ADR** (version-agnostic): name the feature / cut / relationship
  ("Cut 1a", "ahead of the cal record"), never a release. Sequence + ship-state live once in the
  roadmap ladder, not copied into the ADR — coupling a decision to a release means every
  re-sequence edits every ADR. `adr-lint` fails on any `vX.Y.Z`.
- **Allocate a number** only after confirming it's a *new* decision (an amend/re-sequence edits the
  existing ADR in place, per Rationalize): `git fetch`, then `max(local, origin/main, open PRs) + 1`
  — parallel branches grab the same int otherwise. Below origin/main's highest = stale: rebase first.
- **Guard the corpus executably** (poka-yoke): `adr-lint` (see `adr-lint.md`) fails on bad/missing
  frontmatter, an id≠filename, a duplicate id, a release version, a dangling `ADR NNNN` cite, or an
  over-budget record. `/roadmap-review` scans open ADRs' revisit triggers each run.

## Template

Telegraphic fragments, not prose — one full sentence for the crux (load-bearing *why* + weakest
assumption), the rest fragments; cite each `file:line` once. The weakest assumption is the most
visible line. **Budget: ≤50 lines** for a single-decision ADR (the norm); **≤70 absolute max** for
a consolidated multi-layer ADR, and only with each layer terse + specs externalized to a lower home.
Over budget = bloat or a missed lower home: relocate, keep the crux. `adr-lint` enforces the max.

```
---
id: NNNN
title: "<short decision title>"
status: proposed        # proposed | accepted | superseded by NNNN
summary: "<one line for the skim catalog>"
---

# NNNN — <decision title>

- Date: YYYY-MM-DD
- Owner: PM
- Panel: <which advisors ran + why this subset>
- Context: <current problem/gap first (crisp, cite file:line), then the open question it raises>

## Decision
<what, and the priority/sequence — name the cut/feature, not a release>

## Justification
<why this over the alternatives — cost x risk x value>

## Assumptions
- [verified] <proven against code/render — cite file:line or output>
- [checkable] <reproduce against code/logic/render — the gate's job> — owner, result
- [checkable-doc] <a planning fact, checked vs roadmap/ADRs — PM verifies before emitting>
- [contradiction] <Decision contradicts the plan of record — headline + fix the sequence here>
- [unverifiable] <needs usage data / market fact> — REOPEN-IF: <trigger>

## Rejected alternatives
- <option> — why not

## Revisit triggers
- <condition that reopens this decision>

## Act (post-ship — YYYY-MM-DD)
- [outcome] <assumption> — verified / violated / still-open
- [process] <what the cycle missed or got right>
- [pivot] <any REOPEN-IF that fired>
```

Tag routing: **verified** fine; **checkable** (code) the gate verifies, unchecked = defect;
**checkable-doc** (plan) PM verifies vs roadmap/ADRs before emitting; **contradiction** fix the
sequence in the same ADR, never ship un-fixed; **unverifiable** allowed but becomes the revisit
trigger. A shared unverifiable assumption lives once in the register below — reference it, don't
restate per ADR. Append `## Act` after the work ships; omit lines with nothing to say.

**Status = decision validity**, in the frontmatter `status` — not shipping. Ship-state is read from
the roadmap ladder (strike the row when its release ships); the git tag / roadmap stay the one home
for "shipped" — no per-ADR shipped field, no version in the ADR.

**No index file (poka-yoke).** The ADR files ARE the catalog — skim them by grepping frontmatter
(`summary` / `status`); a mirror you don't maintain can't drift, so there is nothing to police.
`adr-lint` guards frontmatter validity + id↔filename + that no `ADR NNNN` cite dangles.

## Shared assumption register

Several calls can hinge on the same market/usage fact; one data point then resolves many. Track such
a shared `[unverifiable]` ONCE here (each dependent ADR references it), so a single signal reopens the
right ADRs. Don't restate it per ADR.

| Assumption | Affects | Resolve with |
|------------|---------|--------------|
| <a market/usage fact several ADRs depend on> | <ADR ids> | <the signal that resolves it> |
