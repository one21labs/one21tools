---
id: 0002
title: "Generalize the plugin for any project; ADR = Authoritative Decision Record; /roadmap-review -> /decide"
status: accepted
summary: "ADRs ARE the plan-of-record (roadmap optional); strip stack/UI/process leaks; rename the expansion + the decision-panel skill"
---

# 0002 — Generalize the framework for any project + naming

- Date: 2026-06-27
- Owner: PM
- Panel: 3 advisory audit agents (stack / domain-UI / process-infra lenses) + the `verifier` and
  `red-team` agents (dogfooded the `/decide` loop on this decision). No standing product panel.
- Context: the plugin baked in assumptions a generic consumer may not share — UI idioms ("render"/
  "the picture"), a guaranteed `ROADMAP.md`, a versioned artifact, a JS manifest — and named things
  too narrowly ("Architecture" Decision Record; a `/roadmap-review` skill that is really the
  decision panel). The framework must fit any stack / product-shape / process.

## Decision
- **ADRs ARE the plan-of-record.** The decision corpus (always present) is canonical: build-order =
  dependency order among unshipped accepted ADRs; ship-state = DERIVED from a dated `## Act` (no
  per-ADR shipped field, no version). A roadmap / changelog / tracker is an OPTIONAL human-readable
  projection. No self-graded "skip if no roadmap" — the plan always exists. (Closes red-team BREAK 1.)
- **ADR = "Authoritative Decision Record"** (was "Architecture" — too narrow). Under rationalize-in-
  place + git-as-backstory the ADR file IS the authoritative current statement; `status` flags the
  exceptions (`proposed`/`superseded`). Acronym + filenames + `adr-lint` + cite syntax unchanged.
- **The `/roadmap-review` skill -> `/decide`** (it is the decision panel, not a roadmap review;
  `/review` was rejected — collides with the built-in PR-review command).
- **Strip the structural leaks:** produced-output (renders/prints/exports), scoped to "if there is
  an output layer", keeping "never from source alone"; version-bump stays a CLAUDE.md pointer (not
  restated); `package.json` -> "a versioned manifest (any stack)"; "the roadmap" -> "the plan of
  record (ADR corpus + any roadmap/tracker)".

## Justification
One defect class (a generic tool hardcoding a stack/UI/artifact/process assumption it already
generalizes elsewhere); each fix copies an in-plugin pattern. The red-team killed the weak roadmap
opt-out by making the always-present ADR corpus the plan — prevention over a per-run skip-judgment.
"Authoritative" fits the doctrine and reinforces "inherit the ADR, don't re-derive from git."

## Assumptions
- [verified] linter + decision-logic test + all 3 skill validations green after the change.
- [verified] rename is mechanically safe — the `ADR NNNN` cite regex, `status` enum, and all
  file/path refs are untouched; grep shows no stale "Architecture Decision" or `roadmap-review`.
- [checkable] no unconditional UI idiom ("render the picture") or self-graded roadmap skip remains — gate greps.
- [unverifiable] "Authoritative" reads right to consumers — REOPEN-IF one wants pure-architecture records.

## Rejected alternatives
- "Accountable" / plain "Decision Record" — Authoritative fits rationalize-in-place; the title names the record's role, status names validity.
- Keep `/roadmap-review`, or use `/review` — the former misnames the panel; the latter collides with the built-in command.
- "Skip if no roadmap" conditional — a self-graded gate opt-out (red-team); ADRs-as-plan removes the conditional entirely.
- Delete the render language — loses the load-bearing "never from source alone"; the fix is scoping, not deletion.

## Revisit triggers
- A consumer reports a remaining hardcoded stack/UI/artifact/process assumption — fold the fix in place, don't spawn an ADR.
- "Authoritative" or "/decide" reads wrong to a consumer — reopen that naming only.

## Act (post-ship — 2026-06-28, PR #2)
