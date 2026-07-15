---
id: 0062
title: "Panel plateau: re-scope /decide to a two-stage gate; two-stage doctrine; marginal dollar to #186 Phase-1"
status: accepted
summary: "ADR 0057's plateau fired. Re-scope /decide (not cut): lite/bare go/no-go default, full panel only for high-stakes gate-passers, forced-record guarantee kept. Adopt the owner two-stage doctrine as policy. Marginal dollar -> #186 Phase-1, poka-yoke first."
---

# 0062 — panel plateau + two-stage doctrine

- Date: 2026-07-14
- Owner: PM
- Panel: opposing counsel CUT (flip default to lite) + KEEP (keep panel default), process-economist (keep-with-scope-narrowing). ADR 0057 d1's measured loop is discharged (plateau), so composition is now the PM's call.
- Context: ADR 0057's plateau trigger fired — arm-D 3-iteration plateau (`benchmarks/2026-07-13-pdca-decide-armd/README.md`), poker H1 falsified judge-robust (`benchmarks/2026-07-14-pdca-decide-poker/README.md`); five decision-quality instruments in, panel ~ bare on rubric under both judges (`pdca-workflow/README.md:29`). Open: cut/keep/re-scope the panel default; adopt the owner two-stage doctrine; route the marginal measurement dollar.

## Decision
**1 — Re-scope, not cut (two-stage /decide routing).** Default = lite/bare go/no-go record (ADR 0020 lite tier already ships): PM writes the call; the ADR carries a falsifiable criterion + spend gate. Escalate to the full panel ONLY for high-stakes/irreversible calls that clear the cheap gate — never routine/meta/tooling. Panel stays callable; nothing deleted. **Process-guarantee value (explicit, per the trigger): the forced record — falsifiable criterion, spend gate, retrospect FP discipline — is constructional (spend gates fired correctly 3x this week) and kept unconditionally by the lite default, independent of the panel spawn; re-scope forfeits none of it while dropping the 4-7x routine panel cost** (C $3.21-4.05 vs A $0.50-0.56/cell, `mean_cell_cost_usd`, poker + armd `results.json`).
Implementation (post-gate, to spec): `pdca-workflow/skills/decide/SKILL.md` loop step 4/5 — a two-stage routing note before Advise (routine/reversible -> lite record; escalate only on high-stakes/irreversible gate-pass). Plugin doc-budget lint applies.

**2 — Adopt the owner two-stage doctrine as repo policy** (owner directive, #184 comment 2026-07-14 — a DECIDED input, recorded not re-litigated): cheap go/no-go gate first, powered optimization ONLY for gate-passers. This ADR is its home. Implementation: the pre-registration template gains a mandatory "gate or optimization?" field — lands in #170's method-reference extraction (does not exist yet; per ADR 0042 pre-spend discipline).

**3 — Marginal measurement dollar -> #186 Phase-1** (~$17), NOT a sixth panel-quality instrument (~$130) NOR nothing. Panel-quality axis saturated (five nulls, CIs straddle zero, no variance damping). Phase-1 operationalizes the go/no-go gate itself — DoD predicts quality among BARE records (`benchmarks/2026-07-14-pdca-dod-phase0/README.md:81`, +0.225/+0.208). Poka-yoke FIRST (tie-break): make the DoD PROPERTIES structural via mandatory lite-template fields (subject-matter assumption, failure class, rejected alt — adr-lint already gates the criterion); Phase-1 then measures only whether record QUALITY needs a standing classifier-detector. If poka-yoke suffices, Phase-1 collapses to nothing.

## Justification
Re-scope is the low-regret reframe both counsels' value survives: CUT's 4-7x-for-+0.010 critique bites only on routine calls (now lite); KEEP's failure-anticipation insurance (C 0.42 vs B 0.08, `benchmarks/2026-07-12-pdca-decide-outcome/README.md:143`) is preserved for the high-stakes calls it exists for. Re-scope cost ~0 (default flip; ADR 0020 machinery exists). The two-stage doctrine (call 2) is the routing rule that makes the reframe mechanical, not judgment.

## Assumptions
- [unverifiable] WEAKEST — the whole re-scope rides on it: the failure-anticipation edge (0.42 vs 0.08) is a real mechanism, not n=1 construction noise. If noise, the panel has NO measured edge and should be CUT fully. Re-scope is deliberately low-regret here (escalation is rare; the record is kept regardless). REOPEN-IF a third independent construction fails to replicate the ~0.42/0.08 gap above run noise -> escalate re-scope to full cut.
- [checkable] the trap-acing edge is within run variance, not a causal panel advantage — C cross-run scenario spread 0.187 ~ A 0.167 (`benchmarks/2026-07-14-pdca-decide-poker/exploratory-crossrun.json:67`), no variance damping. owner: verifier. result: verified — so failure-anticipation is the panel's SOLE candidate edge (itself n=1), strengthening re-scope over full-keep.
- [checkable-doc] no ADR contradicted: 0057 d1's loop discharged with plateau (composition now PM's); 0024 permits cut after 3-plateau (re-scope is less); 0020 lite tier ships; 0061's #185-verdict trigger fired here, and 0061 keeps Phase-1 a follow-up not a #172 gate — call 3 honors that; the "gate or optimization?" field sequences after #170's extraction. result: verified.

## Rejected alternatives
- Full CUT (drop panel from default) — forfeits the failure-anticipation edge before it is priced; re-scope keeps it callable at ~0 cost.
- Full KEEP (panel default) — pays 4-6x per routine call for a judge-sensitive +0.010 rubric null; the premium belongs only on gate-pass calls.
- Sixth ~$130 panel-quality instrument — saturated axis; diminishing returns vs a $17 gate-operationalizing spend.
- Phase-1 as a #172 gate — new spend reopens a deferred question (ADR 0061); #172 closes on Phase-0 + #185 verdicts.

## Revisit triggers
- A third construction replicates the failure-anticipation gap -> harden the escalation criterion; the edge is bankable.
- A third construction refutes it, or escalation is never invoked over a run of high-stakes calls -> graduate re-scope to full cut.
- Poka-yoke lite-template fields make the DoD properties structural -> Phase-1 collapses to nothing; record the null.
