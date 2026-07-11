# Decision log — Authoritative Decision Records (ADRs)

## Table of Contents
- [Template](#template)
- [Lite tier](#lite-tier)
- [Shared assumption register](#shared-assumption-register)

An **ADR** is a dated note capturing one judgment call: its context, the decision, the
justification, the assumptions (tagged), and the triggers that would reopen it. It is the
**authoritative current statement** of that decision — kept current in place (rationalize, don't
re-supersede); git history holds how it got there. One file per decision: `NNNN-slug.md`
(zero-padded, monotonic). Produced by the `pm` agent in the `/decide` flow.

This file is the canonical ADR template. `/pdca-init` copies it into a new project as
`docs/decisions/README.md` (which also holds the shared-assumption register, below).

Rules:
- References to a decision (a roadmap, changelog, issue, or another ADR) use its ID; never re-state
  or re-argue it.
- **Don't narrate backstory.** Git history is the SSoT for how a decision got here — retired /
  renumbered IDs, what-folded-into-what, draft history, "Learned" logs are drift; state the
  current decision, cut the story.
- Every record carries justification AND tagged assumptions + revisit triggers.
- **Mint a falsifiable criterion (Plan-phase gate).** Every decision states at least one criterion
  its Check can later test — a `[checkable]`/`[checkable-doc]`/`[contradiction]` assumption, or an
  `[unverifiable]` paired with a REOPEN-IF (revisitable on a signal). A decision for which none can
  be stated is **UNFALSIFIABLE** — a quality signal the PM must address (reframe the call until it
  is testable, or accept it as explicitly unfalsifiable), not wave through. `adr-lint` enforces
  PRESENCE of a criterion; whether it is *genuinely* falsifiable is the PM's + gate's call.
- **One ADR per PR (max).** A PR captures one decision in one ADR. If it must change before the PR
  merges, **revise it in place** — never add a second ADR to amend or overrule a still-unmerged
  sibling (proliferation; the draft history is squashed away anyway). Separate decisions = separate PRs.
- **Rationalize in place.** Correct, re-sequence, or fold an amendment into the ADR it touches — on
  the next PR that works that area. Don't spawn a new ADR to amend / correct / re-sequence an
  existing one (an "amends NNNN" ADR folds into NNNN). Reserve `status: superseded by NNNN` for a
  decision *wholly retired* by a separate one.
- **No version numbers in an ADR** (version-agnostic): name the feature / cut / relationship
  ("Cut 1a", "before the export feature"), never a release. The ADR carries no release version;
  sequence is the dependency order among the unshipped accepted ADRs and ship-state derives from
  `## Act` (the plan-of-record note below) — coupling a decision to a release number means every
  re-sequence edits every ADR. `adr-lint` fails on any `vX.Y.Z`.
- **Allocate a number** only after confirming it's a *new* decision (an amend/re-sequence edits the
  existing ADR in place, per Rationalize): `git fetch`, then `max(local, origin/main, every origin/*
  branch's docs/decisions/) + 1` — a parallel or never-PR'd branch's ADR collides otherwise. Below
  origin/main's highest = stale: rebase first. This is the single-call rule; deciding several calls
  in parallel uses pre-assigned IDs instead — see `/decide`'s Frame step.
- **Guard the corpus executably** (poka-yoke): `adr-lint` (see `adr-lint.md`) fails on bad/missing
  frontmatter, an id≠filename, a duplicate id, a release version, a dangling `ADR NNNN` cite, an
  unfalsifiable decision (no stated criterion), or an over-budget record. `/decide` scans open ADRs'
  revisit triggers each run.

## Template

Telegraphic fragments, not prose — one full sentence for the crux (load-bearing *why* + weakest
assumption), the rest fragments; cite each `file:line` once. The weakest assumption is the most
visible line. **Budget: ≤6,000 chars (~2 pp) norm** for a single-decision ADR — a char count can't
be gamed by long lines (see ADR 0008; cap + predicate SSoT in `char-budget.mjs`). No exemptions —
an over-budget ADR is rewritten under the cap, not grandfathered. **Draft to a margin (~5,000) and
measure once (`node -e` char count) before finalizing** — don't write long and trim in N passes.
The margin also reserves room for the `## Act` block appended at ship (below); an ADR finalized
at the cap edge forces a trim at close time.
Over budget = bloat or a missed lower home: relocate to a lower home; keep the crux + every
cite + the falsifiable criterion. `adr-lint` enforces the cap.

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
- [verified] <proven against code/render — cite file:line or output; recompute post-edit if the ADR's own decision edits the artifact>
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

Tag routing: **verified** fine; **checkable** (code) the gate verifies, unchecked = defect. A
`[checkable]` whose TEST is a deterministic check the gate can run in-session (a command, a file
read, a formula reproduction) must be resolved before the ADR ships `accepted` — its `— result:`
reads verified/refuted, never `pending`; a runnable check left `pending` is the defect. `pending`
is reserved for a TEST awaiting a future or external signal the gate cannot obtain now (a later
A/B's outcome, a future retro miss), which it must NAME. A permanently out-of-sandbox fact is
`[unverifiable]` (routes to REOPEN-IF), never a `[checkable]` pending.
**checkable-doc** (plan) PM verifies vs roadmap/ADRs before emitting; **contradiction** fix the
sequence in the same ADR, never ship un-fixed; **unverifiable** allowed but becomes the revisit
trigger. A shared unverifiable assumption lives once in the register below — reference it, don't
restate per ADR. Append `## Act` after the work ships; omit lines with nothing to say. Across the
corpus, the rate at which resolved `[checkable]` assumptions verify vs. refute (the `## Act`
`[outcome]` lines) is the **assumption hit-rate** — the emergent, bottom-up quality signal of the
loop. It is a read-out, not a target (optimizing it invites Goodhart); compute it, if wanted, via
the `metrics-engine.md` contract over `## Act` outcomes — no separate metrics home.

**Status = decision validity** (frontmatter `status`), not shipping — `accepted` is the authoritative
live decision; `proposed` = not yet authoritative; `superseded by NNNN` = retired by a separate one
(rare; rationalize in place instead). **The ADR corpus IS the plan-of-record:** an ADR with no
`## Act` is decided-but-not-yet-shipped (the live plan); a dated `## Act` marks it shipped;
build-order is the dependency order among the unshipped accepted ADRs. Ship-state is thus DERIVED
from the record (Act presence) — no per-ADR shipped field, no version in the ADR. A roadmap /
changelog / release tracker is an OPTIONAL human-readable projection: if the project keeps one it
references ADR IDs and mirrors ship-state there; if not, the corpus suffices.

**No index file (poka-yoke).** The ADR files ARE the catalog — skim them by grepping frontmatter
(`summary` / `status`); a mirror you don't maintain can't drift, so there is nothing to police.
`adr-lint` guards frontmatter validity + id↔filename + that no `ADR NNNN` cite dangles.

## Lite tier

For SETTLED decisions only — the boundary is mechanical, not judgment: **a decision that carries a
live revisit trigger or an open assumption needs a full ADR; one that is settled (no trigger,
enforced by a test/script/commit) records as `tier: lite`.** Same directory, same catalog, same id
sequence; `adr-lint` enforces the tier: a lite record containing `REOPEN-IF`, an `[unverifiable]`
bullet, or a `## Revisit triggers` section fails with "graduate it to a full ADR". **Budget:
≤1,500 chars** (`LITE_ADR_CHAR_BUDGET`); the criterion gate does not apply (settled = nothing left
to test). Shape — three parts, no panel/assumptions/alternatives machinery:

```
---
id: NNNN
title: "<short decision title>"
status: accepted
tier: lite
summary: "<one line for the skim catalog>"
---

# NNNN — <decision title>

- Decision: <what, in one or two fragments>
- Why: <the one load-bearing reason>
- Enforced: <test / script / gate file that makes it stick>
```

If a lite record later gains a trigger (something changed), graduate it: rewrite as a full ADR in
place, same id — the tier field is state, not history.

## Shared assumption register

Several calls can hinge on the same market/usage fact; one data point then resolves many. Track such
a shared `[unverifiable]` ONCE here (each dependent ADR references it), so a single signal reopens the
right ADRs. Don't restate it per ADR.

| Assumption | Affects | Resolve with |
|------------|---------|--------------|
| <a market/usage fact several ADRs depend on> | <ADR ids> | <the signal that resolves it> |
