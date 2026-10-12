---
id: 0093
title: "Self-referential loop claims need cross-family independence"
status: accepted
summary: "26-Jul-2026 (#236): a fresh same-family verifier + red-team + ~20 lanes over one session's own work missed three defects, all claims about the SELF; a cross-family agent found all three. Both check agents now REFUSE that class; `pdca-workflow/scripts/crosscheck.mjs` routes it to whichever foreign-vendor CLI the machine has and verifies which model answered, else returns one token, FRAME-UNCHECKED."
---

# 0093 — cross-family independence for self-referential claims

- Date: 2026-07-26
- Owner: PM
- Panel: none spawned (routine under ADR 0062's routing). Checked instead by six adversary rounds,
  five cross-lineage, every one NOT CONVERGED with each finding folded in. Round 6 ran through
  `crosscheck.mjs` itself and broke three things in it. Skip recorded per `/decide` step 6.
- Context: #236 direction 12. `verify` and `red-team` demanded only a FRESH agent, which is
  same-lineage freshness.

## Decision
**The class (operational test).** The claim's subject is the Check machinery itself: does
`/verify`, `/red-team`, `/decide`, an agent prompt, or a gate behave as intended; did a change to
one of them work; what does the loop miss. Claims about the product being checked are ordinary.

**The rule.** A claim in that class cannot be discharged by a spawned subagent — it is the
maker's lineage by construction, and neither model size nor a clean context is lineage. Both
check agents REFUSE it rather than trusting the parent to classify correctly. The primitives
route it out — another vendor's CLI (below), or a person not relaying a model's answer — or
return one shared token, `FRAME-UNCHECKED`: not a pass, not a break, carried into whatever
consumes the verdict, and never grounds for a further same-lineage round. `/decide` records it as
an `[unverifiable]` assumption, never a block.

**The route ships (amended).** `pdca-workflow/scripts/crosscheck.mjs` probes for a foreign CLI
(`$PDCA_CROSSCHECK_CMD`, grok, copilot), sends the claim with READ allowed and writes denied, and
reads back WHICH model answered. A nominally foreign CLI that resolves into the maker's family, or
names a model the script cannot place, returns FRAME-UNCHECKED anyway — copilot's `auto` was
measured listing `claude-haiku-4.5` among its own candidates. So the token now means no lane was
reachable rather than nobody looked, and `adr-lint` requires the probe recorded on the bullet that
claims it.

**Anti-priming (amended 2026-07-29).** The lane is only as clean as the PROMPT sent down it: an
observed incident sent maker framing to a foreign lane — clean lineage, contaminated frame.
(a) Persist claim + raw response + resolved model id per run, at the `runLane` boundary, BOTH
branches, to a path outside the repo tree. Not a one-line fix: the tmpdir is rmSync'd, the
response never touches disk, the custom lane writes no file. Ships now — today no evidence of
priming survives the run that produced it. (b) `--blind` REFUSES (FRAME-UNCHECKED) on a
maker-tell hit; never redacts — silent redaction would alter the claim the lane sees. Opt-in,
independence-critical checks only; DEFERRED behind (a): the tell list derives from the persisted
corpus, not guesses. (c) Prompt-author separation — an independence-critical claim is a verbatim
artifact quote plus a neutral question, else the prompt is authored by a fresh minimal-context
agent. Decided here because it changes this record's mechanism.

## Justification
Fresh clears contaminated REASONING, not shared PRIORS. So the failure worth closing is the
default-open one — an agent CONFIRMING a self-referential claim it had no standing to confirm —
and it closes at the agent, where a mis-classifying parent cannot route around it.

## Assumptions
- [unverifiable] a different vendor's model holds materially different priors on THIS class — REOPEN-IF a same-lineage construction catches it -> demote the rule to advisory.
  WEAKEST. n=1 (the summary's three misses), now n=2: the first cut of `crosscheck.mjs` shipped a
  fail-open — an unplaceable model id passing as foreign — that a cross-lineage round caught and
  this lineage, having just written the rule it broke, did not.
- [unverifiable] a human reviewer counts as another lineage here — REOPEN-IF a human check on this class misses what a cross-vendor model catches -> name the two routes separately.
- [unverifiable] maker framing measurably moved the observed lane's verdict — n=1, and the evidence was destroyed by the rmSync that (a) fixes. REOPEN-IF the first persisted corpus shows no framing effect -> (b) never ships and (c) downgrades to advisory.

## Rejected alternatives
- Pinning a vendor or model — entitlement decides what a CLI will run (copilot rejects every
  explicit `--model` here), so the probe resolves what EXISTS (0055's shape).
- Wording the skills as if spawn could switch family — Claude Code subagents cannot, so an
  imperative there is cosplay and the honest product is the token.
- Folding into ADR 0062 — its "independent" means independent CONSTRUCTIONS, a different sense.

## Revisit triggers
- The token is emitted routinely and nothing downstream ever acts on it -> it is ceremony; cut it
  and say plainly that the class goes unchecked.
- The host makes a cross-lineage lane reachable by default -> drop the probe for it.
