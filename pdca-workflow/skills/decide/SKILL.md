---
name: decide
description: Use when deciding a roadmap or product judgment call, or on any user feedback such as a bug report, feature ask, or behavioral observation. Sorts the call first, then asks, decides inline, or runs the PM-led panel and records an ADR.
---

# /decide — sort the call, then decide it (PDCA Plan + Check)

Route every judgment call and every piece of user feedback here before acting on it. Most
leave at the sort; the panel is for the few where being wrong is expensive.

$ARGUMENTS (optional) = the artifact or calls to focus on. If empty, review the roadmap against the
current product and surface the open calls yourself.

## Sort first
Before any helper or the loop's reading, take the FIRST exit that fits. Say which, and why, in
one line — several calls: one line each.

| The call | Exit |
|----------|------|
| Its deciding fact is a person's preference (a name, wording, taste, risk appetite) and they are reachable | **ASK** — one question: the options and your recommendation. A panel cannot outvote the client. |
| A record in `docs/decisions/` settles it (`git fetch`, grep the summaries, read its revisit trigger) and the trigger has not fired | **INHERIT** — cite the id; do not re-decide. |
| Contested: a real two-sided trade-off, or hard to reverse — as a name or interface others already depend on is | **PANEL** — add `Pick alone: <your answer now>, riding on <the assumption>.` to that line, then the loop below. |
| Anything else: most bug reports, small asks, tooling | **INLINE** — decide it yourself, plan, act, run the project's tests; rationale in the commit/PR. No panel or `pm`; a record only when asked for one (`tier: lite`). |

Unsure between the last two: a call one commit can undo is INLINE. Whatever the exit, a change
shipping onto a Sacred or hard-to-reverse surface gets the `verify` primitive before it ships.

## Why this shape
Averaging can't resolve a trade-off, so the jobs are split: advisors argue, one PM decides and
records it, an independent gate verifies against real code/output and can BLOCK. `advise`,
`verify` and `red-team` also ship standalone, for a call that needs only one of them.

## Roles
| Role | Agent | Hard rule |
|------|-------|-----------|
| Decider | `pm` | what/why/sequence/scope; may overrule an advisor on priority but NOT a verified correctness/safety finding. |
| Advisors | project's panel (`.claude/agents/`, from `pdca-init`) | advise, don't decide — the required shape + spawn rules live in the `advise` skill. |
| Gate | `verifier` | method in its prompt; BLOCKS on a verified correctness/safety finding. |
| Bridge | `tech-lead` | turns an accepted decision into a buildable spec. |
| Adversary | `red-team` | tries to break each decision against the real product; the PM must respond (when required: the Verify step). |

**Spawning a role.** Spawn it by agent name — its frontmatter `model:` then applies. Name not
registered? Spawn a
general-purpose agent told to read and adopt `../../agents/<role>.md`, passing that file's
`model:` — unset, the helper runs on the session's model. No subagents at all? Play the role
yourself from that file, one at a time, and record that the check was not independent. A helper
that returns nothing (crash, timeout, usage limit) is LOST, not an answer: re-run it once; lost
again, stop and report — never a vote or a pass.

## The loop (PANEL exit)
1. **Inherit.** Check open PRs + remote branches for in-flight ADRs. Read in full
   each record the call touches. Scan open ADRs' revisit triggers vs the current product; flag
   any that fire. The corpus IS the plan: flag drift (shipped but a sibling treats it as open;
   accepted, long stalled, no `## Act`; tracker out of sync) — cite the line; omit if none. Grep-verify a claimed inter-ADR relationship — no cite, not real.
2. **Frame.** Clarify scope FIRST, per the `advise` skill's Frame step (its home). List the open
   calls. Multiple calls: pre-allocate parallel `pm`s' IDs here, one each.
3. **Check output.** For any claim about what the product renders/prints/exports/writes, grade the
   real produced output before advising — the grading rule's home is the `verifier` agent. No
   output layer = skip.
4. **Advise.** INVOKE the `advise` skill on the framed scope — never spawn advisors from this
   file. It owns panel selection (TWO opposing advisors), the spawn/shape rules, and what
   unanimous advice means; the `Pick alone:` you said at the sort is its step 2. Restate your
   pick after, per call; both feed that call's `Effect:` line.
5. **Decide (PM).** Invoke `pm`; it weighs the advice and writes an ADR per call per
   `references/adr-template.md`; a settled call records as `tier: lite`.
6. **Verify + red-team + tech-lead.** Only when the result SHIPS or is hard to reverse — else
   record the skip. Run the `verify` primitive over every load-bearing claim and `[checkable]`
   assumption. An accepted ADR needing implementation gets `tech-lead`. If any ADR folds a
   safety caveat in as a BLOCKER, the `red-team` primitive AND `tech-lead` are required. All
   fresh, uncontaminated by the PM's intent. A verified correctness/safety finding, an
   unanswered red-team break, or an infeasible cut BLOCKS the decision — fix the
   document. A `FRAME-UNCHECKED` return does not block: it lands in the
   ADR as an `[unverifiable]` assumption with a revisit trigger.
7. **Record.** Write accepted ADRs to `docs/decisions/NNNN-slug.md` per
   `docs/decisions/README.md` (vendored `references/adr-template.md`; lint:
   `references/adr-lint.md`), each with its `Effect:` line from steps 4-6, which YOU
   fill in — no helper knows your picks. Ship the ADR as read back from disk, never an agent's
   chat echo. Spawned experiments: a neutral falsifiable
   hypothesis, naming no preferred outcome.
8. **Iterate the system.** Fold what you learned back into its home — an agent file, this
   skill, or CLAUDE.md.

## Return
Whatever the exit, close with a plain brief, most important first: the decision (on ASK, the
question); the one reason; on PANEL also where the advisors split, the assumption that would
reverse it, and what went unchecked. Link the ADR; don't paste it.
