---
name: roadmap-review
description: Use when deciding a roadmap or product judgment call, or on any user feedback such as a bug report, feature ask, or behavioral observation. Runs the PM-led panel and records the decision as an ADR. Explicit-invoke only; never auto-fire.
disable-model-invocation: true
---

# /roadmap-review — PM-led decision panel (PDCA Plan + Check)

Decide a judgment call the right way: a dialectic of advisors, one accountable decider, an
independent verification gate — never parallel-and-average. This skill IS the system of record
for the workflow; it has no separate doc to restate.

Explicit-invoke only (`disable-model-invocation`): this panel spends 10+ agents and writes
ADRs (and may bump the version) — it must never auto-fire.

**Trigger.** A roadmap/product change, an open judgment call, or ANY user feedback (bug report,
feature ask, behavioral observation, assertion about the product). Route it through this system
— never fix a feedback item directly before planning it here. A judgment call (threshold,
scope, policy) triggers the panel even when it is meta/tooling work.

Arguments (optional): $ARGUMENTS = the artifact or calls to focus on. If empty, review the
roadmap against the current product and surface the open judgment calls yourself.

## Why this shape
A correctness panel finds problems but can't decide between them — averaging can't resolve a
trade-off (sequence/scope/gating turn on cost, risk, money, differentiation, which the
correctness experts don't own). Split three jobs:

```
PM sets intent
  -> advisors argue (opposing counsel per contested call)
  -> PM decides + writes the ADR (justification + tagged assumptions)
  -> tech-lead turns it into a buildable spec
  -> dev team builds
  -> verification gate checks claims + [checkable] assumptions vs the real code/output
  -> PM accepts or revises (the gate can BLOCK on a verified correctness/safety finding)
```

## Roles (agents shipped by this plugin)
| Role | Agent | Hard rule |
|------|-------|-----------|
| Decider | `pm` | what/why/sequence/scope; may overrule an advisor on priority; CANNOT overrule a verified correctness/safety finding; records justification + tagged assumptions per call. |
| Advisors | the project's panel (below) | advise, don't decide; a recommendation + effort x risk x value grounded in code + THE one assumption it depends on, tagged; terse; never primed with a target grade. |
| Gate | `verifier` | fresh, uncontaminated; reproduces every load-bearing claim + grades the real output; checks `[checkable]` assumptions; BLOCKS on a verified correctness/safety finding. |
| Bridge | `tech-lead` | turns an accepted decision into a buildable spec. |
| Adversary | `red-team` | tries to break each decision against the real product; the PM must respond. Mandatory with tech-lead when an ADR folds a safety caveat in as a BLOCKER. |

**The advisor panel is project-specific.** It lives in `.claude/agents/` and is generated for
this project by `/pdca-init` (panel-generation). If `.claude/agents/` has no project panel,
generate one now — see the `pdca-init` skill, which owns panel generation. Pick the subset a
call needs; record which advisors ran and why on the ADR.

**Model split** (lead on the strongest model, workers cheaper): `pm`, `verifier`, `red-team`
run on the strongest model; advisors + `tech-lead` on a cheaper one. Context isolation is
automatic per subagent — pass each only the files it needs; don't restate isolation in a prompt.

## The loop
1. **Inherit.** Read `docs/decisions/` — load prior ADRs so settled calls are not re-litigated.
   Scan each open ADR's revisit triggers against the current product; flag any that fire. Check
   roadmap future-work items already fully shipped but still listed as future (drift) — cite the
   line; omit if none.
2. **Frame.** Clarify scope FIRST — resolve an ambiguous or multi-item ask into a stated scope
   before any advisor runs (a panel on a fuzzy question wastes the spend and anchors wrong).
   List the open judgment calls. One decision register.
3. **Render.** Grade the real picture, not the source — run the project's render/verify step
   (per CLAUDE.md) for any display or output-layer call.
4. **Advise (dialectic).** Spawn the project's advisors fresh, in parallel, never primed with a
   target grade. For genuinely two-sided calls, run opposing counsel (each steelmans one side).
   Require effort x risk x value grounded in current code/output, returned terse.
5. **Decide (PM).** Invoke `pm`. It weighs the advisors and writes an ADR per call (justification
   + tagged assumptions + rejected alternatives + revisit triggers) using
   `references/adr-template.md`.
6. **Verify + red-team + tech-lead.** Invoke `verifier` (reproduces load-bearing claims, CHECKS
   every `[checkable]` assumption). If any ADR folds a safety caveat in as a BLOCKER, `red-team`
   AND `tech-lead` are required (not optional). All fresh, uncontaminated by the PM's intent. A
   verified correctness/safety finding, an unanswered red-team break, or an infeasible cut BLOCKS
   the decision — fix the contradicting document; don't leave the catch.
7. **Record.** Write accepted ADRs to `docs/decisions/NNNN-slug.md`; update
   `docs/decisions/INDEX.md`; add a roadmap entry referencing the ADR ID for every
   feedback-triggered decision.
8. **Iterate the system.** Fold what you learned (a missing field, a redundant persona, a better
   stop rule) back into its home — an agent file, this skill, or CLAUDE.md. Automate this Act
   loop with `/retrospect`.

If behavior/code changed, run the project's test + build (per CLAUDE.md) and bump the version
before committing. A panel returning unanimous consensus either way (all-accept or all-reject)
is itself a mis-scope signal — re-confirm the ask with the user before acting.
