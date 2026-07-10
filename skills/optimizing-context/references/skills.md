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

**Key differentiator**: Skills are *procedural* (how to do things), Projects are *declarative* (what things are).

## What Makes Skills Effective

### The Description is the Trigger

The `description` field in frontmatter is how Claude decides whether to load the skill. This is the most important part of a skill.

**Include in description:**
- What the skill does
- When to use it (file types, scenarios, keywords)
- Trigger phrases users might say

**Weak**: "Helps with documents"
**Strong**: "Create, edit, and analyze .docx files. Use for Word document creation, tracked changes, comments, or any professional document task."

### Progressive Disclosure

Skills use a three-level loading system:
1. **Metadata** (~100 tokens): Always in context
2. **SKILL.md body**: Loaded when skill triggers
3. **References/scripts**: Loaded as needed

This minimizes context cost while maintaining capability.

### Token Efficiency

Conciseness discipline (challenge each piece against what Claude already knows) is owned by the
`building-skills` skill — see its Core Principles: Conciseness section.

## Skill vs Reference vs Prompt

| Need | Mechanism | Reasoning |
|------|-----------|-----------|
| Procedure used across many conversations | Skill | Portable, on-demand loading |
| Deep domain knowledge for one project | Project Knowledge | Always-loaded for that project |
| One-time complex instruction | Detailed prompt | Ephemeral, no persistence needed |
| External API or data source | MCP server | Real-time access, not static knowledge |

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

## Implementation

For how to actually build skills—structure, scripts, patterns, validation, packaging—see the `building-skills` skill.
