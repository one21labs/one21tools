---
id: 0062
title: "Panel plateau: re-scope /decide to a two-stage gate; two-stage doctrine; marginal dollar to #186 Phase-1"
status: accepted
summary: "ADR 0057's plateau fired. Re-scope /decide (not cut): lite/bare go/no-go default, full panel only for high-stakes gate-passers, forced-record guarantee kept. Adopt the owner two-stage doctrine as policy. Marginal dollar -> #186 Phase-1, poka-yoke first. Amended 26-Jul-2026 (#236): advisor BREADTH saturates but adversary DEPTH does not — a Check phase ends at the first round that changes nothing in the artifact, n=1."
---

# 0062 — panel plateau + two-stage doctrine

- Date: 2026-07-14
- Owner: PM
- Context: ADR 0057's plateau trigger fired (arm-D 3-iteration plateau; poker H1 falsified
  judge-robust) — five decision-quality instruments in, the panel ~ bare on rubric under both
  judges.

## Decision
**1 — Re-scope, not cut (two-stage /decide routing).** Default = lite/bare go/no-go record: PM
writes the call; the ADR carries a falsifiable criterion + spend gate. Escalate to the full panel
ONLY for high-stakes/irreversible calls that clear the cheap gate — never routine/meta/tooling.
The forced-record guarantee (falsifiable criterion, spend gate, retrospect discipline) is kept
unconditionally by the lite default, independent of panel spawn — re-scope forfeits none of it
while dropping the 4-7x routine panel cost (C $3.21-4.05 vs. A $0.50-0.56/cell).

**2 — Adopt the owner two-stage doctrine as repo policy** (owner directive, #184): cheap go/no-go
gate first, powered optimization ONLY for gate-passers. This ADR is its home.

**3 — Marginal measurement dollar -> #186 Phase-1** (~$17), not a sixth panel-quality instrument
(~$130) nor nothing. Panel-quality axis is saturated (five nulls, CIs straddle zero). Phase-1
operationalizes the go/no-go gate itself; poka-yoke first.

**4 — Breadth saturates; DEPTH does not** (amended 2026-07-26, #236). Decisions 1-3 price adding
ADVISORS inside one round. Re-running the adversary AFTER folding its breaks in is the orthogonal
axis, and it has not plateaued: four rounds on one PR each raised fresh defects, one manufactured
by the previous round's own fix, with every gate green throughout. A Check phase ends at the
first round that changes nothing in the artifact — not when the maker is satisfied, and not when
the gates pass. STOP RULE, so depth cannot become never-ship: a round whose findings are all
refuted with cited evidence counts as dry; the rounds spent are disclosed where the work lands,
and the owner may call it at any round. The evidence here is n=1 and deliberately weaker than the
five instruments behind 1-3 — the trigger below is set to match.
Enforced: `pdca-workflow/skills/red-team/SKILL.md` (Return).

## Justification
Re-scope is low-regret: the cut critique bites only on routine calls (now lite); the keep case's
failure-anticipation insurance (0.42 vs. 0.08 trap-acing) is preserved for the high-stakes calls
it exists for, at ~0 re-scope cost.

## Assumptions
- [unverifiable] WEAKEST — the whole re-scope rides on it: the failure-anticipation edge (0.42 vs. 0.08) is a real mechanism, not n=1 construction noise; re-scope is deliberately low-regret regardless (escalation is rare, the record is kept either way). REOPEN-IF a third independent construction fails to replicate the ~0.42/0.08 gap above run noise -> escalate re-scope to full cut.

## Rejected alternatives
- Full CUT (drop panel from default) — forfeits the failure-anticipation edge before it is priced.
- Full KEEP (panel default) — pays 4-6x per routine call for a judge-sensitive +0.010 rubric null.
- A sixth ~$130 panel-quality instrument — saturated axis.
- Phase-1 as a #172 gate — new spend reopens a deferred question (ADR 0061).

## Revisit triggers
- A third construction refutes the failure-anticipation gap, or escalation is never invoked over
  a run of high-stakes calls -> graduate re-scope to full cut.
- Poka-yoke lite-template fields make the DoD properties structural -> Phase-1 collapses to nothing.
- (Decision 4) Round one comes back dry on three separate PRs -> the depth rule drops to a single
  round. Or a PR needs more rounds than the owner will pay for -> depth gets a hard ceiling, and
  the ceiling is recorded here rather than left to judgment.
