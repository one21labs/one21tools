---
name: optimizing-context
description: Invoke when advising on context engineering: CLAUDE.md files, project setup, agent architectures, or choosing between skills, prompts, MCP, subagents, and hooks.
---

# Optimizing Context

Context engineering is curating tokens during LLM inference to maximize desired outcomes.

## Why This Matters

Model performance degrades non-uniformly as context grows — distractors and position effects both
amplify at length — so token efficiency is fundamental: every token competes in a finite window
with diminishing returns.

Mechanism names vary by product (Claude.ai vs. Claude Code vs. API terms for the same layer); full
per-product mapping in [mechanism-selection.md](references/mechanism-selection.md).

## Decision Matrix: Which Mechanism?

| Need | Mechanism | Why |
|------|-----------|-----|
| Repeated procedures across conversations | **Skill** | Loads on-demand, portable, progressive disclosure |
| Codebase conventions and guardrails | **CLAUDE.md** | Always-loaded project context for Claude Code |
| Background knowledge for initiative | **Project** | Always-loaded reference material for Claude.ai |
| External data or tool connectivity | **MCP** | Real-time access, data gateway pattern |
| Deterministic automation on events | **Hooks** | Lifecycle events for validation, formatting, CI |
| Independent task with own context | **Subagent** | Context isolation, tool restrictions |
| Distribute tools with selective installation | **Plugin** | Package agents/skills/commands, install only what's needed |
| One-time instruction | **Prompt** | Ephemeral, conversational |
| User behavior defaults (all chats) | **User Preferences** (Claude.ai) or **User CLAUDE.md** (Claude Code) | Permanent, account-wide |
| Project-specific behavior | **Project Instructions** | Scoped to initiative |

Quick routing:
- Repeated procedure -> Skill
- Project context always loaded -> CLAUDE.md (Code) or Project (Claude.ai)
- External data/tools -> MCP
- Deterministic automation -> Hooks
- Isolated task execution -> Subagent (prefer Task() over custom)
- One-time request -> Prompt
- Personal defaults -> User Preferences (Claude.ai) or ~/.claude/CLAUDE.md (Code)

For worked before/after examples of these choices (bloated vs. lean CLAUDE.md, Skill vs.
CLAUDE.md, MCP vs. Skill, plugin marketplace structure), see
[mechanism-selection.md](references/mechanism-selection.md).

## Core Principles

1. **Smallest High-Signal Tokens**: Every token must justify its cost. Ask: "Does Claude already know this?"
2. **Right Altitude**: Not brittle hardcoded logic (too low), not vague guidance (too high). Match degrees of freedom to task fragility.
3. **Progressive Disclosure**: Metadata first, then content when triggered, then deep resources as needed.
4. **Constitution, Not Manual**: CLAUDE.md captures guardrails for what Claude gets wrong, not comprehensive documentation.

## Documentation Altitude and SSoT (in brief)

Two orthogonal rules decide where a fact lives:
- **Altitude routing**: a fact belongs at the altitude matching its abstraction and time-horizon
  (STRATEGY > ROADMAP > README / CLAUDE.md > file headers > code).
- **SSoT uniqueness**: one home per fact, at the lowest altitude where it is fully determined;
  every higher mention is a reference, not a copy. A fact copied above its home is drift.

Executable facts invert the axis: code sits lowest in altitude but highest in authority. Schema
versions, function signatures, and filenames are owned by code; any doc that restates them rots —
naming the source file does not license also keeping the value ("schema v12, see models.py" rots
exactly like "schema v12" alone). Full altitude table and common drift patterns:
[mechanism-selection.md](references/mechanism-selection.md).

## Measuring Success

After changes, verify token count dropped, previously-failed tasks now succeed, retrieval stays
accurate, and no regressions appear. For skills, confirm activation on 3+ realistic user
phrasings. Skill size targets and the full metrics table:
[mechanism-selection.md](references/mechanism-selection.md). If no measurable improvement, revert.

## Mechanism Guides

Read the appropriate reference when creating/optimizing:

| Mechanism | Reference | When to Read |
|-----------|-----------|--------------|
| CLAUDE.md | [claude-md.md](references/claude-md.md) | Writing for Claude Code |
| Skills | [skills.md](references/skills.md) | Creating skills |
| Plugins | [plugins.md](references/plugins.md) | Marketplace structure, auto-discovery |
| Projects | [projects.md](references/projects.md) | Claude.ai projects |
| User Preferences | [user-preferences.md](references/user-preferences.md) | Claude.ai defaults |
| Prompts | [prompts.md](references/prompts.md) | Designing prompts, including slash commands |
| MCP | [mcp.md](references/mcp.md) | Server design |
| Subagents | [subagents.md](references/subagents.md) | Task delegation |
| Hooks | [hooks.md](references/hooks.md) | Automation |
| Format efficiency | [token-format-efficiency.md](references/token-format-efficiency.md) | Formatting stored data/tool outputs (not SKILL.md/CLAUDE.md bodies) |
| Examples / altitude depth | [mechanism-selection.md](references/mechanism-selection.md) | Worked examples, full SSoT rules, metrics |
