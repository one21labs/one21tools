---
id: 0006
title: "Drop retrospect opus->sonnet; classify the Act-loop role in the model-split doctrine"
status: accepted
tier: lite
summary: "Cut retrospect opus->sonnet (only non-gating agent; both failure modes backstopped); keep pm/verifier/red-team=opus (lead/gate/adversary). Extend the decide/SKILL.md doctrine line to classify the Act-loop role->tier. Bet: retrospect's value is grounded reproduction + routing (sonnet-adequate), not opus-class synthesis."
---

# 0006 — retrospect agent model tier (opus->sonnet) + doctrine classification

- Decision: `agents/retrospect.md` drops from opus to sonnet — the one agent off the gating
  path, whose output is advice the orchestrator independently re-verifies before acting. Keep
  pm/verifier/red-team on opus (lead/gate/adversary — each fails silent + uncaught +
  load-bearing if wrong). Extend the model-tier doctrine line (`decide/SKILL.md`) so the
  Act-loop retrospective role is explicitly classified into the "cheaper" tier, deriving the
  frontmatter instead of leaving it an unclassified outlier.
- Why: retrospect's two failure modes are both backstopped — fabrication is loud and
  cite-checked; wrong-home routing still routes any real judgment call to `/decide`+ADR,
  PM-verified before it lands. Value is dominated by grounded git/file reproduction and
  correct routing, not opus-class generative synthesis.
- Rejected: keep retrospect on opus — leaves it the lone unclassified, non-gating agent on the
  strong tier. Drop verifier/red-team/pm too — each is doctrine-pinned lead/gate/adversary, not
  a safe cut.
- Reopen-if: a tiered A/B over shipped branches shows sonnet drops a systemic finding opus
  caught, or retrospect is ever wired to auto-apply a finding without PM verification -> revert
  to opus / add the safeguard first.
- Enforced: `pdca-workflow/agents/retrospect.md` (`model: sonnet`); the doctrine line in
  `pdca-workflow/skills/decide/SKILL.md`.
