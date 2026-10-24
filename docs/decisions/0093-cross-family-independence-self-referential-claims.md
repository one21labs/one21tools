---
id: 0093
title: "Self-referential loop claims need cross-family independence"
status: accepted
summary: "A claim about the Check machinery itself cannot be discharged by a same-family subagent: both check agents REFUSE it; `pdca-workflow/scripts/crosscheck.mjs` routes it to a foreign-vendor CLI and verifies which model answered, else returns one token, FRAME-UNCHECKED."
---

# 0093 — cross-family independence for self-referential claims

- Date: 2026-07-26
- Owner: PM
- Panel: none (routine, ADR 0062); six adversary rounds instead, five cross-lineage.
- Context: #236 direction 12 — a fresh same-family verifier + red-team + ~20 lanes missed three
  defects in claims about the SELF; a cross-family agent found all three. `verify` and `red-team`
  demanded only a FRESH agent, which is same-lineage freshness.

## Decision
**The class (operational test).** The claim's subject is the Check machinery itself: does
`/verify`, `/red-team`, `/decide`, an agent prompt, or a gate behave as intended; did a change to
one of them work; what does the loop miss. Claims about the product being checked are ordinary.

**The rule.** A claim in that class cannot be discharged by a spawned subagent — the maker's
lineage by construction; neither model size nor a clean context is lineage. Both check agents
REFUSE it rather than trust the parent to classify. Route it out — another vendor's CLI, or a
person not relaying a model's answer — or return `FRAME-UNCHECKED`: not a pass, not a break,
carried into whatever consumes the verdict, never grounds for a further same-lineage round.
`/decide` records it as an `[unverifiable]` assumption, never a block.

**The route.** `pdca-workflow/scripts/crosscheck.mjs` probes for a foreign CLI
(`$PDCA_CROSSCHECK_CMD`, grok, copilot), sends the claim with READ allowed and writes denied, and
reads back WHICH model answered. A CLI resolving into the maker's family, or naming a model the
script cannot place, returns FRAME-UNCHECKED (copilot `auto` lists `claude-haiku-4.5`). The token
means no lane was reachable; `adr-lint` requires the probe recorded on the bullet that claims it.

**Anti-priming** — the lane is only as clean as the PROMPT sent down it.
(a) Persist claim + raw response + resolved model id per run, at the `runLane` boundary, BOTH
branches, outside the repo tree.
(b) `--blind` REFUSES (FRAME-UNCHECKED) on a maker-tell hit; never redacts. Opt-in,
independence-critical checks only; DEFERRED behind (a): the tell list derives from the persisted
corpus.
(c) An independence-critical claim is a verbatim artifact quote plus a neutral question, else its
prompt is authored by a fresh minimal-context agent.

## Justification
Fresh clears contaminated REASONING, not shared PRIORS, so the failure worth closing is an agent
CONFIRMING a self-referential claim it had no standing to confirm — closed at the agent, where a
mis-classifying parent cannot route around it.

## Assumptions
- [unverifiable] WEAKEST — a different vendor's model holds materially different priors on THIS class (n=2: the #236 misses; `crosscheck.mjs`'s first-cut fail-open caught cross-lineage only) — REOPEN-IF a same-lineage construction catches it -> demote the rule to advisory.
- [unverifiable] a human reviewer counts as another lineage here — REOPEN-IF a human check on this class misses what a cross-vendor model catches -> name the two routes separately.
- [unverifiable] maker framing measurably moved an observed lane's verdict (n=1, evidence lost to rmSync) — REOPEN-IF the first persisted corpus shows no framing effect -> (b) never ships and (c) downgrades to advisory.

## Rejected alternatives
- Pinning a vendor or model — entitlement decides what a CLI runs (copilot rejects every explicit
  `--model` here), so the probe resolves what EXISTS (ADR 0055's shape).
- Wording skills as if spawn could switch family — subagents cannot; the honest product is the token.
- Folding into ADR 0062 — its "independent" means independent CONSTRUCTIONS.

## Revisit triggers
- The token is emitted routinely and nothing downstream acts on it -> cut it; say plainly the
  class goes unchecked.
- The host makes a cross-lineage lane reachable by default -> drop the probe for it.
