---
name: optimizing-context
description: Invoke when advising on context engineering, writing CLAUDE.md files, setting up projects, designing agent architectures, or optimizing any mechanism that shapes Claude's input. Decision framework for choosing between Skills, CLAUDE.md, Prompts, Projects, MCP, Subagents, User Preferences, and Hooks. Optimize Claude's context for better outcomes. 
---

# Optimizing Context

Context engineering is curating tokens during LLM inference to maximize desired outcomes.

## Table of Contents

1. [Why This Matters](#why-this-matters)
2. [Context Hierarchy by Product](#context-hierarchy-by-product)
3. [Decision Matrix](#decision-matrix)
4. [Concrete Examples](#concrete-examples)
5. [Core Principles](#core-principles)
6. [Documentation Altitude & SSoT](#documentation-altitude--ssot)
7. [Measuring Success](#measuring-success)
8. [Mechanism Guides](#mechanism-guides)

---

## Why This Matters

Model performance degrades non-uniformly as context grows:
- Simple tasks degrade with longer context
- Distractors amplify negative impact at length
- Position affects retrieval (primacy/recency effects)

**Implication**: Token efficiency is fundamental. Every token competes in a finite window with diminishing returns.

---

## Context Hierarchy by Product

| Layer | Claude.ai | Claude Code | API |
|-------|-----------|-------------|-----|
| User-level | User Preferences, Memories, Styles | User CLAUDE.md, user settings | — |
| Project/Repo | Project Instructions, Project Knowledge | Repo CLAUDE.md, project settings | System prompt |
| Session | Conversation history, uploaded files | Conversation + tool results | Messages array |
| On-demand | Skills | Skills | Skills |
| External | Integrations | MCP servers, Hooks | MCP servers |

---

## Decision Matrix: Which Mechanism?

| Need | Mechanism | Why |
|------|-----------|-----|
| Repeated procedures across conversations | **Skill** | Loads on-demand, portable, progressive disclosure |
| Codebase conventions and guardrails | **CLAUDE.md** | Always-loaded project context for Claude Code |
| Background knowledge for initiative | **Project** | Always-loaded reference material for Claude.ai |
| External data or tool connectivity | **MCP** | Real-time access, data gateway pattern |
| Deterministic automation on events | **Hooks** | Lifecycle events for validation, formatting, CI |
| Independent task with own context | **Subagent** | Context isolation, tool restrictions |
| Distribute tools with selective installation | **Plugin** | Package agents/skills/commands, users install only what they need |
| One-time instruction | **Prompt** | Ephemeral, conversational |
| User behavior defaults (all chats) | **User Preferences** (Claude.ai) or **User CLAUDE.md** (Claude Code) | Permanent, account-wide |
| Project-specific behavior | **Project Instructions** | Scoped to initiative |

```
Need repeated procedure? ─────────────► Skill
Need project context always loaded? ──► CLAUDE.md (Code) or Project (claude.ai)
Need external data/tools? ────────────► MCP
Need deterministic automation? ───────► Hooks
Need isolated task execution? ────────► Subagent (prefer Task() over custom)
One-time request? ────────────────────► Prompt
Personal defaults? ───────────────────► User Preferences (claude.ai) or ~/.claude/CLAUDE.md (Code)
```

---

## Concrete Examples

### Example 1: Bloated CLAUDE.md → Lean Version

**Before** (wastes tokens on what Claude knows):
```markdown
# Project Guidelines

## About This Project
This is a Python web application using Flask. Flask is a micro web 
framework written in Python. It is classified as a microframework 
because it does not require particular tools or libraries...

## Code Style
We use Python. Python is an interpreted, high-level programming language.
Always use 4 spaces for indentation because that is the Python standard...
```

**After** (only project-specific corrections):
```markdown
# CLAUDE.md

## Conventions
- Flask app, pytest for tests
- 4-space indent, type hints required
- Run `make lint` before commits

## Common Errors to Avoid
- Don't use `datetime.now()` — use `datetime.utcnow()`
- Always close DB connections in finally blocks
```

**Why**: Claude knows what Flask and Python are. CLAUDE.md captures project-specific corrections only.

### Example 2: Wrong Mechanism Choice

**Situation**: User wants SQL queries formatted with uppercase keywords.

| Choice | Mechanism | Problem |
|--------|-----------|---------|
| ✗ Wrong | Skill | Creates portable package for a personal preference |
| OK | User Preferences (Claude.ai) | "Format SQL with uppercase keywords" applies everywhere |
| OK | ~/.claude/CLAUDE.md (Claude Code) | User-level defaults for all Claude Code sessions |

### Example 3: Skill vs. CLAUDE.md

**Situation**: Team has Kubernetes deployment procedures.

**Use Skill when** procedure is reusable across projects:
```
deploying-k8s/
├── SKILL.md
└── scripts/deploy.sh
```

**Use CLAUDE.md when** procedure is repo-specific:
```markdown
# In repo's CLAUDE.md
## Deployment
Run `./deploy.sh staging` then verify at https://staging.example.com
```

### Example 4: MCP vs. Skill

**Situation**: Need to query company's BigQuery tables.

| Choice | Mechanism | Why |
|--------|-----------|-----|
| ✗ Wrong | Skill alone | Can't access live data |
| ✓ Right | MCP + Skill | MCP provides connection, Skill provides schemas/patterns |

### Example 5: Plugin Marketplace Structure

**Situation**: Monorepo with skills for different domains. Want users to install only what they need.

| Choice | Approach | Result |
|--------|----------|--------|
| ✗ Wrong | Use repo root as source | Auto-discovery loads all skills for every plugin |
| ✓ Right | Use component directories as sources | Each plugin loads only specified skills |

**Why**: Default directories (`/skills/`, `/agents/`, `/commands/`) at plugin root trigger auto-discovery that loads everything. Using component directories as sources avoids this. See [plugins.md](references/plugins.md) for implementation.

---

## Core Principles

1. **Smallest High-Signal Tokens**: Every token must justify its cost. Ask: "Does Claude already know this?"
2. **Right Altitude**: Not brittle hardcoded logic (too low), not vague guidance (too high). Match degrees of freedom to task fragility.
3. **Progressive Disclosure**: Metadata first → content when triggered → deep resources as needed.
4. **Constitution, Not Manual**: CLAUDE.md captures guardrails for what Claude gets wrong, not comprehensive documentation.

---

## Documentation Altitude & SSoT

Two orthogonal rules — not one axis — determine where a fact lives:

**Altitude routing** — a fact belongs at the altitude matching its abstraction and time-horizon:

| Altitude | Document | Contains |
|----------|----------|---------|
| Strategic | STRATEGY | Why/positioning, year-horizon |
| Tactical | ROADMAP | What's next, quarter-horizon |
| Orientation | README | Getting started (newcomers, read once) |
| Operating contract | CLAUDE.md | Constraints for agents and editors (read repeatedly) |
| Local design intent | File headers | Module role, constraints, non-obvious patterns |
| Exact behavior | Code | Canonical truth for executable facts |

README and CLAUDE.md are roughly the same altitude — the split is audience (orientation vs. operating contract), not authority.

**SSoT uniqueness** — one home per fact, at the lowest altitude where it is fully determined. Every higher mention must be a reference, not a copy. Drift = a fact copied above its home.

The axis inverts for executable facts: code sits at the bottom of altitude but the top of authority. Schema versions, function signatures, filenames — code owns them. Any doc that restates them will rot.

Common drift patterns (cure: reference or omit):
- Schema version stated in CLAUDE.md → rotted when code changed
- Filenames in SEE ALSO blocks → rotted on rename
- Deleted features described in CLAUDE.md → documented behavior that no longer exists

---

## Measuring Success

After changes, verify improvement:

| Metric | How to Measure |
|--------|----------------|
| Token count | Compare context size before/after |
| Task success | Does Claude complete previously-failed tasks? |
| Retrieval accuracy | Does Claude find relevant info when needed? |
| No regressions | Do previously-working tasks still work? |
| Plugin selectivity | Install test plugin, verify only specified content in `/context` |
| Skill activation | Does the skill trigger on 3+ realistic user phrasings (not documentation language)? |

**Skill size targets** (SkillReducer empirical baselines, 2026): description ≤100 tokens; body ≤500 lines (enforced). Descriptions >200 tokens show diminishing returns. Body content >60% non-actionable (preamble, examples, documentation) is a documented waste pattern.

If no measurable improvement, revert changes.

---

## Mechanism Guides

Read appropriate reference when creating/optimizing:

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

---
