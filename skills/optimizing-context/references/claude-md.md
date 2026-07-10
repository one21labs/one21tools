# CLAUDE.md Guide

CLAUDE.md is Claude Code's project-level context mechanism. It's loaded automatically at session start.

## Table of Contents

1. [When to Use Which File](#when-to-use-which-file)
2. [Core Philosophy: Constitution, Not Manual](#core-philosophy-constitution-not-manual)
3. [What to Include](#what-to-include)
4. [Pitching References](#pitching-references)
5. [Structure Guidance](#structure-guidance)
6. [Token Allocation](#token-allocation)
7. [Examples](#examples)
8. [Iteration](#iteration)

## When to Use Which File

| File | Scope | Use Case |
|------|-------|----------|
| `~/.claude/CLAUDE.md` | User (all projects) | Personal conventions, global preferences |
| `./CLAUDE.md` | Project root | Team conventions, project architecture |
| `./.claude/CLAUDE.local.md` | Project (gitignored) | Personal project overrides, experiments |

Precedence: Project overrides user. Local overrides project.

## Core Philosophy: Constitution, Not Manual

CLAUDE.md is a set of guardrails, not comprehensive documentation.

**Start with what Claude gets wrong**, not what it should know. If Claude makes the same mistake repeatedly, add a guardrail. If Claude handles something well already, don't document it.

**Anti-pattern**: Documenting your entire codebase architecture
**Pattern**: Noting the non-obvious decisions Claude keeps missing

**Reorganizing is not preserving.** "Keep everything, don't lose our work" asks you to respect the
effort behind existing material, not to keep every line verbatim — it does not suspend the
constitution-not-manual test. Apply that test per item, to one-line rules exactly as you would to a
paragraph: if Claude already does something by default (4-space indent, docstrings, logging not
print, composition over inheritance), cut it, don't relocate it under a tidier heading. Cutting
loses no history — git already has it.

## What to Include

### High-Value Content

1. **Correction patterns**: "When X, do Y instead of Z"
2. **Non-obvious conventions**: Things that differ from common practice
3. **Tool-specific quirks**: Your linter config, test runner flags, deployment targets
4. **Path hints**: Where to find schemas, configs, key modules
5. **Decision rationale**: Why unusual choices were made (so Claude doesn't "fix" them)

### Anti-Patterns to Avoid

| Anti-Pattern | Problem | Instead |
|--------------|---------|---------|
| `@`-file entire docs | Bloats context, Claude may not read | Pitch *why* to read specific files |
| "Never do X" without alternative | Claude needs a path forward | "Instead of X, do Y because Z" — supply Y even if the source material only states the prohibition; infer it from what the project already uses |
| Comprehensive architecture docs | Too long, low signal | Note only non-obvious parts |
| Duplicating README content | Redundant, SSoT violation | Reference README location |
| Style guide regurgitation | Claude knows common styles | Note only deviations |
| Rule cites a removed/decommissioned component | References dead code, misleads | Delete outright — the removal is a known fact, not a pending team decision to flag |
| A procedure described as identical across many repos/teams, even in passing | Inlining duplicates upkeep N times over | Point to one on-demand home (skill, script, doc); recognize this from context, not only when explicitly asked where something belongs |
| CLAUDE.md deep-links into a skill's `references/` | Bypasses the skill's SKILL.md routing table, skipping its onward handoffs | Link the skill or its SKILL.md; deep-link only leaf procedures |

## Pitching References

Don't just mention files exist—explain *why* Claude should read them:

**Weak**: "See docs/api.md for API documentation"

**Strong**: "Before implementing new endpoints, read docs/api.md for our auth pattern—we use a custom header scheme that differs from standard Bearer tokens"

## Structure Guidance

Be specific: "Use 2-space indentation" is better than "Format code properly". Use bullet points for each memory item regardless of file size ([official guidance](https://docs.claude.com/en/docs/claude-code/memory.md)).

| File Size | Formatting | Rationale |
|-----------|------------|-----------|
| <15 lines | Bullets only | Headers add overhead without navigation benefit |
| 15-50 lines | Minimal headers | Light grouping aids clarity |
| 50+ lines | Full sections | Navigation and instruction separation matter |

Keep CLAUDE.md lean. Suggested sections:

```markdown
# Project Name

Brief one-liner on what this is.

## Key Decisions

Non-obvious architectural choices Claude should respect.

## Common Mistakes

Things Claude gets wrong; corrections.

## Commands

Project-specific commands Claude should use.

## Where to Look

Pointers to key files with *why* they matter.
```

## Token Allocation

For large projects, budget deliberately: key decisions and common mistakes are Critical (200-400
tokens each); commands and path hints are High/Medium (100-200 each); background is Low (50-100).

**Line count heuristic**: target under 1,000 tokens for most projects (enterprise monorepos may need
up to 3,000), which maps to roughly 60–100 lines depending on density. Target under 60; treat 100 as
a hard ceiling to prune before adding. Anthropic: "Bloated CLAUDE.md files cause Claude to ignore your actual instructions." Community empirical data: adherence degrades noticeably around 80 lines, significantly past 200. No official line count exists — prune by the token target and the per-line test ("would removing this cause Claude to make mistakes?").

## CLAUDE.md as Forcing Function

If CLAUDE.md is getting too long, it's a signal that your tooling is too complex. Use CLAUDE.md maintenance as a forcing function to simplify:
- Consolidate scripts
- Standardize conventions
- Reduce special cases

## Examples

### Good: Correction Pattern

```markdown
## Common Mistakes

When running tests, always use `npm run test:unit` not `npm test`—the latter runs E2E which requires a running server.
```

### Good: Non-Obvious Convention

```markdown
## Key Decisions

We use barrel exports (`index.ts`) only at module boundaries, not within modules. This is intentional to avoid circular dependency issues we had previously.
```

### Bad: Over-Documentation

```markdown
## Architecture

This is a Next.js application using React 18 with TypeScript. We use Tailwind for styling and Prisma for database access...
[300 more lines]
```

Claude already knows what Next.js, React, Tailwind, and Prisma are. Only document deviations.

## Iteration

CLAUDE.md should evolve:

1. Start minimal (or empty)
2. Notice when Claude makes mistakes
3. Add targeted corrections
4. Remove entries when Claude stops needing them
5. Simplify tooling when CLAUDE.md grows too large

## Sources

- [Memory documentation](https://docs.claude.com/en/docs/claude-code/memory.md) - Official formatting guidance (bullets, headings)
- [Using CLAUDE.md Files](https://claude.com/blog/using-claude-md-files) - Official guidance
- [How I Use Claude Code](https://shrivastava.io/p/how-i-use-claude-code) - Practical patterns, constitution-not-manual philosophy
