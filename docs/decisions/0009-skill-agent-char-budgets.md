---
id: 0009
title: "Char budgets extend to SKILL.md bodies, skill references, and agent prompts"
status: accepted
tier: lite
summary: "Extend char-budget discipline (ADR 0008) beyond ADRs + CLAUDE.md: SKILL.md bodies, skill references/*.md (TOC past a sub-threshold) and agent prompts all carry char caps. Gate splits by runtime: validate.py owns SKILL.md body + references; char-budget.mjs/adr-lint owns agents (+ its existing ADR/CLAUDE.md caps). Caps live in each gate's own constants — no cross-plugin dependency. No exemptions: the 3 over-budget bodies were rewritten under cap, not grandfathered."
---

# 0009 — char budgets for SKILL.md, references, and agent prompts

- Decision: owner-set char caps on SKILL.md bodies, `references/*.md` (TOC past a sub-threshold)
  and agent prompts. Gate splits by runtime: `validate.py` owns SKILL.md body + reference caps;
  `char-budget.mjs`/`adr-lint.mjs` owns the agent cap alongside its ADR/CLAUDE.md caps. VALUES
  live in each gate's constants — `validate.py`'s ship inside the skill, so no cross-plugin
  dependency; `validation-rules.md` owns the rules and why.
- Why: `validate.py`'s prior `BODY_MAX_LINES=500` was gameable — the largest body was 230 lines
  yet 9,756 chars, so a char cap replaced it. No exemptions: the 3 then-over-budget bodies were
  rewritten under cap, not grandfathered.
- Rejected: keep the line cap (proven gameable) — one shared gate for all caps (Python/JS can't
  share a constant without the cross-plugin dependency this ADR forbids).
- Reopen-if: a skill/reference/agent legitimately cannot fit its cap without cutting a
  load-bearing crux.
- Enforced: `skills/building-skills/scripts/validate.py` (body + reference caps),
  `pdca-workflow/scripts/char-budget.mjs` (`AGENT_CHAR_BUDGET`, agent cap).
