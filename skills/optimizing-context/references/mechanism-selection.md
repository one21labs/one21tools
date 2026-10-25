# Mechanism Selection: Worked Examples and Depth

Concrete before/after examples, mechanism trade-off tables, and the documentation-altitude
deep-dive that back the decision framework in SKILL.md. Read when you need a worked example
for a specific mechanism choice or the full altitude/SSoT rules.

## Table of Contents

1. [Context Hierarchy by Product](#context-hierarchy-by-product)
2. [Concrete Examples](#concrete-examples)
3. [Documentation Altitude and SSoT](#documentation-altitude-and-ssot)
4. [Measuring Success](#measuring-success)

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

## Concrete Examples

### Example 2: Wrong Mechanism Choice

**Situation**: User wants SQL queries formatted with uppercase keywords.

| Choice | Mechanism | Problem |
|--------|-----------|---------|
| Avoid | Skill | Creates portable package for a personal preference |
| Prefer | User Preferences (Claude.ai) | "Format SQL with uppercase keywords" applies everywhere |
| Prefer | ~/.claude/CLAUDE.md (Claude Code) | User-level defaults for all Claude Code sessions |

### Example 3: Skill vs. CLAUDE.md

**Situation**: Team has Kubernetes deployment procedures.

**Use Skill when** procedure is reusable across projects:
```
deploying-k8s/
  SKILL.md
  scripts/deploy.sh
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
| Avoid | Skill alone | Can't access live data |
| Prefer | MCP + Skill | MCP provides connection, Skill provides schemas/patterns |

### Example 5: Plugin Marketplace Structure

**Situation**: Monorepo with skills for different domains. Want users to install only what they need.

| Choice | Approach | Result |
|--------|----------|--------|
| Avoid | Use repo root as source | Auto-discovery loads all skills for every plugin |
| Prefer | Use component directories as sources | Each plugin loads only specified skills |

Why and how: [plugins.md](plugins.md).

---

## Documentation Altitude and SSoT

Two orthogonal rules — not one axis — determine where a fact lives.

**Altitude routing** — a fact belongs at the altitude matching its abstraction and time-horizon:

| Altitude | Document | Contains |
|----------|----------|---------|
| Strategic | STRATEGY | Why/positioning, year-horizon |
| Tactical | ROADMAP | What's next, quarter-horizon |
| Orientation | README | Getting started (newcomers, read once) |
| Operating contract | CLAUDE.md | Constraints for agents and editors (read repeatedly) |
| Local design intent | File headers | Module role, constraints, non-obvious patterns |
| Exact behavior | Code | Canonical truth for executable facts |

README and CLAUDE.md are roughly the same altitude — the split is audience (orientation vs.
operating contract), not authority.

**SSoT uniqueness** — one home per fact, at the lowest altitude where it is fully determined.
Every higher mention must be a reference, not a copy. Drift = a fact copied above its home.

The axis inverts for executable facts: code sits at the bottom of altitude but the top of
authority. Schema versions, function signatures, filenames — code owns them. Any doc that
restates them will rot.

Common drift patterns (cure: reference or omit):
- Schema version stated in CLAUDE.md, rotted when code changed. Naming the source file doesn't
  license also keeping the value: `Schema is at version 12 (models.py)` still rots, because the
  number is still copied. Fix: `Schema: see models.py` — file only, no number.
- Filenames in SEE ALSO blocks, rotted on rename
- Deleted features still described in CLAUDE.md (cure: [claude-md.md](claude-md.md) Anti-Patterns)

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

**Skill size targets** (SkillReducer empirical baselines, 2026): checklist owned by
[building-skills/SKILL.md](../../building-skills/SKILL.md#quality-checklist) (Anti-Pattern Baselines).

If no measurable improvement, revert changes.
