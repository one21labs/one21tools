# Projects Guide (Claude.ai)

Projects are Claude.ai workspaces that maintain context across conversations through Project Instructions and Project Knowledge.

## Core Concept: Scoped Context

Everything in a project is available to every conversation in that project:
- Uploaded documents (Project Files)
- Custom instructions (Project Instructions)
- Conversation history

## When Project vs Other Mechanisms

| Use Project when... | Use Something Else when... |
|---------------------|---------------------------|
| Need shared context for initiative | Procedure repeats across initiatives (use Skill) |
| Team collaboration needed | Personal workflow (use User Preferences) |
| Background knowledge applies to all chats | Just need one conversation |
| Organizing related work | Context needs to travel to other products |

## Project Components

### Project Instructions
Custom system prompt for all conversations in the project.

**Good instructions**:
```
You are helping with Q4 product launch. Priorities:
1. User experience over feature count
2. Meet November 15 deadline
3. Focus on mobile-first

Tone: Direct, action-oriented. Skip preamble.
```

**Avoid**:
- Repeating what's in uploaded docs
- Generic instructions Claude already follows
- Contradicting User Preferences without reason

### Project Files (Knowledge Base)
Documents Claude can reference across all conversations in the project.

**Good candidates**:
- Product specifications
- Research reports
- Reference documentation
- Meeting notes and decisions
- Competitor analysis

**Poor candidates**:
- Entire codebases (use Claude Code instead)
- Data that changes frequently (use MCP)
- Procedural how-tos (use Skills)

## Project vs Skill

| Project | Skill |
|---------|-------|
| **What** to know | **How** to do |
| Static reference | Dynamic procedure |
| Always loaded | Loaded on demand |
| Scoped to initiative | Travels everywhere |
| Background knowledge | Procedural knowledge |

**Example**:
- Project: "Q4 Launch" containing specs, research, timeline
- Skill: "create-prd" containing PRD writing procedure

Use together: Skill references Project knowledge when creating PRD.

## Project Organization Patterns

### By Initiative
```
Projects/
├── Q4 Product Launch
├── Customer Research 2024
├── Infrastructure Migration
└── Team Onboarding
```

### By Domain
```
Projects/
├── Engineering
├── Marketing
├── Sales
└── Operations
```

## Large Knowledge Bases

When Project Files exceed direct context loading, Claude uses retrieval (RAG):
- Searches files for relevant chunks rather than loading everything
- May miss connections across documents that aren't retrieved together

**Implications for organization**:
- Include summary documents that reference key connections across files
- Front-load important context in document beginnings
- Use clear headings and structure for better retrieval

For current context limits and RAG behavior, see the Projects documentation (Sources below).

## Project Instructions Best Practices

### Be Specific to Initiative
```
# Good
This project analyzes competitor pricing. 
Compare against our $99/mo baseline.
Focus on enterprise tier differences.

# Poor
Help me with analysis tasks.
```

### Set Tone and Constraints
```
# Good
Respond in bullet points, max 5 per section.
Flag assumptions explicitly.
Ask before making recommendations over $10K.

# Poor
Be helpful and thorough.
```

### Reference Uploaded Docs
```
# Good
The PRD in project files is the source of truth for features.
Competitor analysis is in "competitor-matrix.xlsx".

# Poor
Use the documents I uploaded.
```

## Common Patterns

### Research Project
- Instructions: Research methodology, source preferences
- Files: Literature, data sets, previous findings

### Writing Project  
- Instructions: Style guide, audience, voice
- Files: Examples, brand guidelines, outlines

### Analysis Project
- Instructions: Frameworks to apply, output format
- Files: Data, context docs, comparison baselines

## Sources

- Projects documentation: https://support.claude.com/en/articles/9519177-how-can-i-create-and-manage-projects
- Personalization features: https://support.claude.com/en/articles/10185728-understanding-claude-s-personalization-features
