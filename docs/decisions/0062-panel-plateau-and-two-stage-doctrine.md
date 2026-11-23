---
id: 0062
title: "Panel plateau: re-scope /decide to a two-stage gate; two-stage doctrine; marginal dollar to #186 Phase-1"
status: accepted
summary: "ADR 0057's plateau fired. Re-scope /decide (not cut): routine calls decided in the commit/PR with no ADR or pm spawn (owner, 24-Oct-2026), full panel + ADR only for high-stakes gate-passers. Adopt the owner two-stage doctrine as policy. Marginal dollar -> #186 Phase-1, poka-yoke first. Amended 26-Jul-2026 (#236): advisor BREADTH saturates but adversary DEPTH does not — a Check phase ends at the first round that changes nothing in the artifact, n=1. Amended 23-Nov-2026: the gate is /decide's FIRST step (ask, inherit, panel, inline); two advisors by default; each paneled record carries a self-reported Effect: line, the in-use cost read-out."
---

# 0062 — panel plateau + two-stage doctrine

- Date: 2026-07-14
- Owner: PM
- Context: ADR 0057's plateau trigger fired (arm-D 3-iteration plateau; poker H1 falsified
  judge-robust) — five decision-quality instruments in, the panel ~ bare on rubric under both
  judges.

## Decision
**1 — Re-scope, not cut (two-stage /decide routing).** Default = routine call: the session
decides it and states the rationale in the commit/PR — no ADR, no `pm` spawn (owner, 24-Oct-2026:
"No records for routine calls"). Escalate to the full panel + ADR ONLY for high-stakes/irreversible
calls that clear the cheap gate — never routine/meta/tooling. This drops the 4-7x routine panel
cost (C $3.21-4.05 vs. A $0.50-0.56/cell).

**2 — Adopt the owner two-stage doctrine as repo policy** (owner directive, #184): cheap go/no-go
gate first, powered optimization ONLY for gate-passers. This ADR is its home.

**3 — Marginal measurement dollar -> #186 Phase-1** (~$17), not a sixth panel-quality instrument
(~$130) nor nothing. Panel-quality axis is saturated (five nulls, CIs straddle zero). Phase-1
operationalizes the go/no-go gate itself; poka-yoke first.

**4 — Breadth saturates; DEPTH does not** (amended 2026-07-26, #236). Decisions 1-3 price adding
ADVISORS inside one round. Re-running the adversary AFTER folding its breaks in is the orthogonal
axis, and it has not plateaued: four rounds on one PR each raised fresh defects, one manufactured
by the previous round's own fix, with every gate green throughout. A Check phase ends at the
first dry round (stop rule: red-team `SKILL.md` Return); the owner may call it at any round.
The evidence here is n=1 and deliberately weaker than the
five instruments behind 1-3 — the trigger below is set to match.
Enforced: `pdca-workflow/skills/red-team/SKILL.md` (Return).

**5 — Gate FIRST; the panel prices itself in use** (amended 2026-11-23; owner: "optimized for
value (low cost, high value)"). Decision 1's gate sat at step 4, behind a fetch and a corpus scan
every routine call paid for. It is now `/decide`'s first step, four exits: ask the person, inherit
a record, decide inline, panel. The panel defaults to TWO opposing advisors (decision 4: breadth
saturates). Every paneled record carries an `Effect:` line — the session's pick before any helper
ran, then what advice, PM and check each changed — a free in-use read-out in place of a sixth
paid instrument. The separate `pm` spawn is on trial under that line: no instrument isolated it.
Homes: `pdca-workflow/skills/decide/SKILL.md` (Sort first); `adr-template.md` (`Effect:`).
The line is a convention, unlinted and self-reported; `pdca-workflow/agents/retrospect.md`
reads it and flags a paneled record that lacks one.

## Justification
Re-scope is low-regret: the cut critique bites only on routine calls (now unrecorded); the keep case's
failure-anticipation insurance (0.42 vs. 0.08 trap-acing) is preserved for the high-stakes calls
it exists for, at ~0 re-scope cost.

## Assumptions
- [unverifiable] WEAKEST — the whole re-scope rides on it: the failure-anticipation edge (0.42 vs. 0.08) is a real mechanism, not n=1 construction noise; re-scope is deliberately low-regret regardless (escalation is rare). REOPEN-IF a third independent construction fails to replicate the ~0.42/0.08 gap above run noise -> escalate re-scope to full cut.
- [unverifiable] (Decision 5) A stage's self-reported `nothing` is evidence it is not earning its cost. The session writes the line and judges its own counterfactual; the adversary refused this frame and no cross-lineage lane was reachable (FRAME-UNCHECKED, 23-Nov-2026; Probed: none). REOPEN-IF a stage cut on this evidence is followed by a defect that stage exists to catch.

## Rejected alternatives
- Full CUT (drop panel from default) — forfeits the failure-anticipation edge before it is priced.
- Full KEEP (panel default) — pays 4-6x per routine call for a judge-sensitive +0.010 rubric null.
- A sixth ~$130 panel-quality instrument — saturated axis.
- Phase-1 as a #172 gate — new spend reopens a deferred question (ADR 0061).

## Revisit triggers
- A third construction refutes the failure-anticipation gap, or escalation is never invoked over
  a run of high-stakes calls -> graduate re-scope to full cut.
- A routine call gets re-litigated because no record of it existed -> that class of call is
  recorded again.
- Poka-yoke lite-template fields make the DoD properties structural -> Phase-1 collapses to nothing.
- (Decision 4) Round one comes back dry on three separate PRs -> the depth rule drops to a single
  round. Or a PR needs more rounds than the owner will pay for -> depth gets a hard ceiling, and
  the ceiling is recorded here rather than left to judgment.
- (Decision 5) A stage's `Effect:` reads `nothing` ten records running -> cut that stage. Or a
  call that left at the inline exit is reverted or re-argued -> that row of the sort was too
  loose; tighten it.
