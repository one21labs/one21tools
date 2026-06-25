# Decision log — Architecture Decision Records (ADRs)

An **ADR** is a dated, append-only note capturing one judgment call: its context, the decision,
the justification, the assumptions, and the triggers that would reopen it. One file per
decision: `NNNN-slug.md` (zero-padded, monotonic). Produced by the `pm` agent in the
`/roadmap-review` flow.

This file is the canonical ADR template. `/pdca-init` copies it into a new project as
`docs/decisions/README.md`, and creates a sibling `docs/decisions/INDEX.md` (one row per ADR).

Rules:
- The roadmap references a decision by ID; it never re-states or re-argues it.
- Every record carries justification AND assumptions (tagged verified / checkable /
  unverifiable) + revisit triggers.
- Never edit an accepted decision to reverse it — add a new ADR that supersedes it (set the old
  one's Status to `superseded by NNNN`).
- `/roadmap-review` scans open ADRs' revisit triggers against the current product at the start
  of each run.

## Template

Telegraphic fragments, not prose — one full sentence budgeted for the crux (load-bearing why +
weakest assumption), the rest fragments; cite each `file:line` once. The weakest assumption is
the most visible line in the record. **50 lines max** — over that, the content belongs in a
lower home (code, roadmap, or an agent file).

```
# NNNN — <decision title>

- Status: proposed | accepted | superseded by NNNN
- Date: YYYY-MM-DD
- Owner: PM
- Panel: <which advisors ran + why this subset>
- Context: <the open question, grounded in the product's current state>

## Decision
<what, and the priority/sequence>

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

## Act (post-ship — vX.Y.Z / YYYY-MM-DD)
- [outcome] <assumption> — verified / violated / still-open
- [process] <what the cycle missed or got right>
- [pivot] <any REOPEN-IF that fired>
```

Tag routing: **verified** fine; **checkable** (code) the gate verifies, unchecked = defect;
**checkable-doc** (plan) PM verifies vs roadmap/ADRs before emitting; **contradiction** fix the
sequence in the same ADR, never ship un-fixed; **unverifiable** allowed but becomes the revisit
trigger. Append `## Act` after each tagged release merges; omit lines with nothing to say (three
lines is the ceiling, not the floor).

**Status = decision validity, not shipping.** Ship-state reads from the roadmap (strike the row
when its tag merges); an ADR is done iff every release it maps to is struck. The git tag is the
one home for "shipped" — no per-ADR shipped field.

**INDEX.md** carries one row per ADR (ID, title, status). This README owns only the rules +
template; add a new ADR's row to the index, not here.
