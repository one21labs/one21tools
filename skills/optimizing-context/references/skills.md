# Skills: When and Why

Skills are modular packages that extend Claude's capabilities with procedural knowledge, workflows, and bundled resources. This reference covers **when to use skills** and **what makes them effective**. For **how to build skills**, see the `building-skills` skill.

## When Skill vs Other Mechanisms

| Situation | Use Skill? | Alternative |
|-----------|------------|-------------|
| Repeated procedure across conversations | **Yes** | — |
| Project-specific knowledge | No | CLAUDE.md or Project |
| One-time complex task | No | Detailed prompt |
| External data access | No | MCP server |
| User-wide defaults | No | User Preferences |
| Deterministic automation on events | No | Hooks |

## What Makes Skills Effective

Description-as-trigger, progressive disclosure, and conciseness: the `building-skills` skill's
Core Principles.

## When to Create a New Skill

Create a skill when:
- You find yourself repeating the same complex instructions
- A procedure involves multiple steps with specific patterns
- Domain knowledge isn't in Claude's training
- You want to share capability across conversations or users

Don't create a skill when:
- The task is simple enough to explain each time
- The knowledge is project-specific (use CLAUDE.md/Project instead)
- You need real-time external data (use MCP instead)
