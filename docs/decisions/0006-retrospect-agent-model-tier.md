---
id: 0006
title: "Drop retrospect opus->sonnet; classify the Act-loop role in the model-split doctrine"
status: accepted
summary: "Cut retrospect opus->sonnet (the only non-gating agent, both failure modes backstopped); keep pm/verifier/red-team=opus (lead/gate/adversary); extend the decide/SKILL.md:53 doctrine line to classify the Act-loop role->tier so the frontmatter is derived, not a reversible outlier. Bet: retrospect's value is grounded reproduction + routing (sonnet-adequate), not opus-class synthesis."
---

# 0006 — retrospect agent model tier (opus->sonnet) + doctrine classification

- Date: 2026-06-29
- Owner: PM
- Panel: 3 per-call lenses — A (cost/muda), B (failure-mode: silent?/uncaught?/load-bearing?), C (doctrine-coherence/poka-yoke); A & B steelmanned opposite sides and converged. `verifier` + `red-team` run next (inherits 0001/0002; per 0004).
- Context: the plugin ships five agents whose tier is set by `model:` frontmatter (SSoT). Verified: pm/verifier/red-team/retrospect=opus, tech-lead=sonnet (`agents/*.md:4`). The doctrine line pins ONLY lead/gate/adversary to the strong tier (`decide/SKILL.md:53`, exact: "lead / gate / adversary on the strongest model, advisors + bridge cheaper"); `retrospect` is named nowhere in it. Open question: does retrospect keep opus, and how is its tier recorded so it stops being an unclassified outlier?

## Decision
1. **retrospect: opus -> sonnet** (one line, `agents/retrospect.md:4`). It is the single agent off the gating path — post-ship, non-gating, its output is advice the orchestrator re-verifies (`retrospect.md:42-44`). Dropping it makes the strong-tier set exactly {pm, verifier, red-team} = the doctrine's lead/gate/adversary, so this ALIGNS the doctrine rather than excepting it.
2. **Keep** pm=opus, verifier=opus, red-team=opus — lead/gate/adversary, doctrine-pinned; each fails silent+uncaught+load-bearing (a missed BLOCKER ships to every consumer). tech-lead=sonnet (bridge — inherited).
3. **Extend the doctrine line** at `decide/SKILL.md:53` (advisor C's poka-yoke) so the tier is derived, not something a reader can "tidy" either way. Append the Act-loop retrospective to that parenthetical's "cheaper" clause — the first half already classifies the strong-tier trio (`decide/SKILL.md:42-46`: lead=pm, gate=verifier, adversary=red-team). Deliberately NO "only the gating roles need the strong tier" gloss: verifier is the only literal gate (`:44`), so that wording would license dropping pm + red-team to sonnet — the cut this ADR forbids.

## Justification
retrospect has two failure modes, both backstopped. (a) Fabrication (padded commit / thin findings) is loud + checkable via the cite tripwire (`retrospect/SKILL.md:33`). (b) Wrong-home routing with REAL cites is the quieter mode the tripwire does NOT catch — the agent owns the routing rules (`SKILL.md:30`); its backstop is the rule sending any judgment-call routing to `/decide`+ADR (`retrospect.md:42-44`), PM-verified before it lands. Mode (b) is what the weakest [checkable] A/B tests, so the cut rides on that test, not on an "always loud" claim. Verdict: effort trivial, risk low (non-gating + re-checked), value modest-but-compounding (every consumer inherits). The doctrine-line extension (Decision 3) is the strongest reason to act beyond the bare cut.

## Assumptions
- **[checkable] WEAKEST — the whole bet: retrospect's value is dominated by grounded git/file reproduction + correct routing-to-lowest-home (sonnet-adequate), NOT opus-class generative synthesis.** TEST (owner: verifier): A/B both tiers over this repo's shipped branches (e.g. the 0004/0005 PRs) with their recorded friction, and diff BOTH finding-presence AND routing-HOME; if sonnet drops a systemic finding opus raised, OR mis-routes one opus placed correctly, KEEP opus. — result: pending.
- [verified] retrospect is non-gating + orchestrator-re-checked — `retrospect.md:42-44`: "your output is advice, not a directive", the orchestrator "independently verifies + muda-assesses before acting"; no path auto-applies a retro finding. The safety rail that makes the cut acceptable. REOPEN-IF retrospect is ever wired to auto-edit agent files / CLAUDE.md / tests without PM verify.
- [checkable] the edit is the two homes above only — adds no script/CI; adr-lint corpus stays green (`node pdca-workflow/scripts/adr-lint.mjs docs/decisions`). — owner: verifier.
- [checkable-doc] no ADR or roadmap depends on retrospect being opus (corpus 0001-0005 reviewed); tech-lead is existing precedent for a non-gating sonnet agent.

## Rejected alternatives
- Keep retrospect on opus — leaves it the lone unclassified outlier AND the lone non-gating agent on the strong tier; the doctrine pins only lead/gate/adversary, and retrospect is none of those.
- Drop verifier (or red-team, or pm) too — gate/adversary/lead, doctrine-pinned; each fails silent+uncaught+load-bearing (Decision 2). Not a safe cut.
- Add a per-agent prose rationale to retrospect.md — muda; role->tier belongs in the doctrine line, the WHY here.

## Revisit triggers
- The weakest-assumption A/B test shows sonnet drops a systemic finding opus caught, or auto-apply wiring lands -> revert / reopen (see the assumption REOPEN-IFs).
- DEFERRED (separate `/decide`, do NOT fold here): the "advisors=sonnet" rule appears in 3 homes — `decide/SKILL.md:53` (SSoT rule) vs `panel-generation.md:27` + `advisor-template.md:8` (literal `model: sonnet` scaffolding). Evaluate whether the two scaffolding lines are a one-home violation or legitimate derive-don't-duplicate.
- Claude Code adds/renames a subagent `model:` tier, or Opus/Sonnet pricing shifts the ~1.67x gap materially -> re-evaluate the whole split.

## Act (post-ship — 2026-06-29, PR #9)
- [outcome] weakest [checkable] (sonnet A/B over shipped branches) — still-open; owner: verifier.
