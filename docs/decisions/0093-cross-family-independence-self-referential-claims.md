---
id: 0093
title: "Self-referential loop claims need cross-family independence"
status: accepted
summary: "26-Jul-2026 (#236): a fresh same-family verifier + red-team + ~20 lanes over one session's own work missed three defects, all claims about the SELF; a cross-family agent found all three. Both check agents now REFUSE that class; the primitives route it out of the lineage or return one token, FRAME-UNCHECKED. No resolver ships."
---

# 0093 — cross-family independence for self-referential claims

- Date: 2026-07-26
- Owner: PM
- Context: #236 direction 12. `verify` and `red-team` demanded only a FRESH agent, which is
  same-lineage freshness. Promoted from lite tier once the record acquired load-bearing
  assumptions worth tagging.

## Decision
**The class (operational test).** The claim's subject is the Check machinery itself: does
`/verify`, `/red-team`, `/decide`, an agent prompt, or a gate behave as intended; did a change to
one of them work; what does the loop miss. Claims about the product being checked are ordinary
and unaffected.

**The rule.** A claim in that class cannot be discharged by a spawned subagent — it is the
maker's lineage by construction, and neither model size nor a clean context is lineage. Both
check agents REFUSE it rather than depending on the parent to classify correctly. The primitives
route it to a checker of another lineage — another vendor's CLI, a second account, a person — or
return one shared token, `FRAME-UNCHECKED`: not a pass, not a break, carried into whatever
consumes the verdict, and never grounds for a further same-lineage round. `/decide` records it as
an `[unverifiable]` assumption, never a block. The plugin states the requirement and ships NO
resolver.

## Justification
Fresh clears contaminated REASONING, not shared PRIORS. A same-lineage checker settles
frame-internal claims well and structurally cannot see the frame, so the default-open failure
(agent confirms a self-referential claim it had no standing to confirm) is the one worth closing
at the agent, where a mis-classifying parent cannot route around it.

## Assumptions
- [unverifiable] WEAKEST: that a different vendor's model holds materially different priors on
  THIS class, rather than differing only in style. Evidence is n=1 — 26-Jul, a fresh same-family
  verifier + red-team + ~20 sweep lanes over one session's own work caught real defects and
  missed three, all self-referential (an issue still demanding a mechanism the session had
  deleted; an additive remedy for an additive bias; the unbuilt half of its own diagnosis), and a
  cross-family agent found all three. REOPEN-IF a same-lineage construction catches this class ->
  demote the rule to advisory.
- [checkable] a human reviewer counts as another lineage for this purpose.

## Rejected alternatives
- Shipping a resolver (probe for a second-family CLI, pin a model) — the principle ships, this
  repo's grok/copilot invocation does not; copy `skill-bench`'s resolve-else-caveat shape only.
- Wording the skills as if spawn could switch family — Claude Code subagents cannot, so an
  imperative there is cosplay and the honest product is the token.
- Folding into ADR 0062 — its "independent" means independent CONSTRUCTIONS, a different sense.

## Revisit triggers
- The token is emitted routinely and nothing downstream ever acts on it -> it is ceremony; cut it
  and say plainly that the class goes unchecked.
- A cross-lineage lane becomes reachable by default in the host -> replace the token with the
  real route.
