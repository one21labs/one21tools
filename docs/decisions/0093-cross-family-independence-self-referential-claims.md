---
id: 0093
title: "Self-referential loop claims need cross-family independence"
status: accepted
summary: "26-Jul-2026 (#236): a fresh same-family verifier + red-team + ~20 lanes over one session's own work missed three defects, all claims about the SELF; a cross-family agent found all three. Both check agents now REFUSE that class; the primitives route it out of the lineage or return one token, FRAME-UNCHECKED. No resolver ships."
---

# 0093 — cross-family independence for self-referential claims

- Date: 2026-07-26
- Owner: PM
- Panel: none spawned (routine under ADR 0062's routing). Checked instead by five sequential
  adversary rounds, four cross-lineage; rounds 1-4 each returned NOT CONVERGED and each finding
  was folded in. Skip recorded per `/decide` step 6.
- Context: #236 direction 12. `verify` and `red-team` demanded only a FRESH agent, which is
  same-lineage freshness.

## Decision
**The class (operational test).** The claim's subject is the Check machinery itself: does
`/verify`, `/red-team`, `/decide`, an agent prompt, or a gate behave as intended; did a change to
one of them work; what does the loop miss. Claims about the product being checked are ordinary.

**The rule.** A claim in that class cannot be discharged by a spawned subagent — it is the
maker's lineage by construction, and neither model size nor a clean context is lineage. Both
check agents REFUSE it rather than trusting the parent to classify correctly. The primitives
route it to a checker of another lineage — another vendor's CLI, or a person who is not
relaying a model's answer — or
return one shared token, `FRAME-UNCHECKED`: not a pass, not a break, carried into whatever
consumes the verdict, and never grounds for a further same-lineage round. `/decide` records it as
an `[unverifiable]` assumption, never a block. The plugin states the requirement, ships NO
resolver.

## Justification
Fresh clears contaminated REASONING, not shared PRIORS. So the failure worth closing is the
default-open one — an agent CONFIRMING a self-referential claim it had no standing to confirm —
and it closes at the agent, where a mis-classifying parent cannot route around it.

## Assumptions
- [unverifiable] a different vendor's model holds materially different priors on THIS class — REOPEN-IF a same-lineage construction catches it -> demote the rule to advisory.
  WEAKEST, and the evidence is n=1: 26-Jul, a fresh same-family verifier + red-team + ~20 sweep
  lanes over one session's own work caught real defects and missed three, every one of them
  self-referential (an issue still demanding a mechanism the session had deleted; an additive
  remedy for an additive bias; the unbuilt half of its own diagnosis); a cross-family agent
  found all three.
- [unverifiable] a human reviewer counts as another lineage here — REOPEN-IF a human check on this class misses what a cross-vendor model catches -> name the two routes separately.

## Rejected alternatives
- Shipping a resolver (probe for a second-family CLI, pin a model) — the principle ships, this
  repo's grok/copilot invocation does not; copy `skill-bench`'s resolve-else-caveat shape only (ADR 0055).
- Wording the skills as if spawn could switch family — Claude Code subagents cannot, so an
  imperative there is cosplay and the honest product is the token.
- Folding into ADR 0062 — its "independent" means independent CONSTRUCTIONS, a different sense.

## Revisit triggers
- The token is emitted routinely and nothing downstream ever acts on it -> it is ceremony; cut it
  and say plainly that the class goes unchecked.
- A cross-lineage lane becomes reachable by default in the host -> replace the token with the
  real route.
