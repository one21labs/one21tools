# Decision log — Architecture Decision Records (ADRs)

An **ADR** is a dated, append-only note capturing one judgment call: its context, the decision,
the justification, the assumptions (tagged), and the triggers that would reopen it. One file per
decision: `NNNN-slug.md` (zero-padded, monotonic). Produced by the `pm` agent in the
`/roadmap-review` flow.

This file is the canonical ADR template. `/pdca-init` copies it into a new project as
`docs/decisions/README.md`, and creates a sibling `docs/decisions/INDEX.md` (one row per ADR +
the shared-assumption register).

Rules:
- The roadmap references a decision by ID; it never re-states or re-argues it.
- Every record carries justification AND assumptions (tagged) + revisit triggers.
- **One ADR per PR (max).** A PR captures one decision in one ADR. If that ADR must change
  before the PR merges, **revise it in place** — never add a second ADR to amend or overrule a
  still-unmerged sibling (the draft history is squashed away anyway, and two records for one
  decision is proliferation). Genuinely-separate decisions = separate PRs.
- Never edit an *already-merged* accepted decision to reverse it — add a new ADR that supersedes
  it (set the old one's Status to `superseded by NNNN`). **Pre-merge: revise in place.
  Post-merge: supersede.**
- **Allocate a number** by `git fetch` first, then `max(local, origin/main, open PRs) + 1` —
  parallel branches grab the same int otherwise. If your branch's highest ADR is below
  origin/main's, you are stale: rebase / pull `docs/decisions/` before writing.
- `/roadmap-review` scans open ADRs' revisit triggers against the current product at the start of
  each run.
- **Guard the ledger executably** (poka-yoke): `adr-lint` (see `adr-lint.md`) fails on a duplicate
  ID, an INDEX↔file mismatch, or an over-budget record — the drifts manual numbering and parallel
  branches invite. Run it in CI / pre-merge; "monotonic by luck" is not a guard.

## Template

Telegraphic fragments, not prose — one full sentence budgeted for the crux (load-bearing why +
weakest assumption), the rest fragments; cite each `file:line` once. The weakest assumption is the
most visible line in the record. **Budget: ≤50 lines** for a single-decision ADR (the norm); a
consolidated multi-layer ADR (the one-ADR-per-PR rule) may approach **≤70 absolute max**, and only
with each layer terse + specs externalized to a lower home (code, roadmap). Over budget = bloat or
a missed lower home: relocate, keep the crux. The linter enforces the absolute max (configurable;
default it to this template's number).

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
trigger. A shared unverifiable assumption lives once in the INDEX register — reference it, don't
restate per ADR. Append `## Act` after each tagged release merges; omit lines with nothing to say
(three lines is the ceiling, not the floor).

**Status = decision validity, not shipping.** Ship-state reads from the roadmap release ladder
(strike the row when its tag merges); an ADR is *done* iff every release it maps to is struck. The
git tag is the one home for "shipped" — no per-ADR shipped field.

## INDEX.md — catalog + shared register

`INDEX.md` carries one row per ADR; this README owns only the rules + template (add a new ADR's row
to INDEX, not here). **Pin the row to this link format** — the linter regexes it, so keep it exact:

```
| [NNNN](NNNN-slug.md) | <decision, one line> | <ships> |
```

Ship-state in the `<ships>` column is a **derived mirror**, never a second authority: strike the
`→ <release>` token (`→ ~~1.2.0~~`) in the same edit that strikes the roadmap ladder row. Docs-only
ADRs have no release. Decision validity (`Status`) lives in the ADR file, not this table.

**Shared register.** When several decisions hinge on the same unverifiable fact, record that
assumption ONCE in a register section at the foot of INDEX.md and have each dependent ADR reference
it — so a single data point reopens every dependent decision. Never restate the same market/usage
assumption per record.
