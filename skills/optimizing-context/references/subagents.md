# When and Why to Use Subagents

Subagents are specialized AI assistants with their own context windows, system prompts, and tool permissions. Available in Claude Code and Claude Agent SDK.

## Core Concept: Context Isolation

Each subagent operates in a fresh context. This prevents:
- Main conversation pollution from deep exploration
- Irrelevant details leaking between tasks
- Context window exhaustion on complex work

## When Subagent vs Other Mechanisms

| Use Subagent when... | Use Something Else when... |
|----------------------|---------------------------|
| Task needs own context window | Just need procedural knowledge (use Skill) |
| Different tool permissions needed | Same permissions as main agent |
| Parallel exploration useful | Sequential, single-focus work |
| Task is self-contained | Frequent back-and-forth needed |

## Subagent vs Task() Delegation

**Prefer general `Task()` delegation over custom subagents.**

Custom subagents:
- Gatekeep context (may over-restrict)
- Force rigid workflows
- Require maintenance

General delegation:
- Flexible context access
- Adapts to task requirements
- Lower overhead

**Use custom subagents only when you need**:
- Specific tool restrictions (read-only for reviewers)
- Strict behavioral constraints (security-focused)
- Repeatable specialized workflows

## Built-in Subagents (Claude Code)

| Subagent | Model Tier | Tools | Purpose |
|----------|------------|-------|---------|
| **General** | Capable | All | Complex multi-step tasks |
| **Explore** | Fast | Read-only | Quick codebase search |
| **Plan** | Capable | Read-only | Research for planning |

**Explore** is optimized for speed but read-only. Use for finding information without changes.

**General** can read and write. Use for tasks requiring both exploration and modification.

For current model assignments, see Claude Code documentation.

## Model Tiering + Parallelism (match tier and concurrency to task)

Two first-class efficiency levers: this repo is the main workflow people run loops through, so
waste here compounds across every user x every iteration (rationale:
[token-format-efficiency.md](token-format-efficiency.md)).

### Model Tiering

- **Top tier (Opus) orchestrates and judges.** Planning, routing, and final adjudication — work
  where capability gates outcome quality.
- **Delegate BULK to cheaper/faster tiers (Sonnet/Haiku).** Implementation, extraction, and grading
  fan out across many agents — run the bulk on the cheapest tier that clears the quality bar.
- **ALWAYS set the worker/grader model explicitly** — subagents INHERIT the session model when
  `model` is unset, so a 100+-agent grid launched from an Opus session silently runs every worker
  on the expensive tier. Real miss: two 144-agent grading passes ran on Opus because the tier was
  left implicit. Set `model: sonnet`/`haiku` explicitly; use `inherit` only when you mean it.

### Parallelism

- **Fan out INDEPENDENT work concurrently** — Workflow `parallel()`/`pipeline()` for many agents or
  items at once, not chained one-by-one.
- **Serialize ONLY what shares a singleton resource** — a single git worktree/branch, or the
  hermetic-executor's user-CLAUDE.md relocation symlink, can't take concurrent writers without
  corrupting state.
- **Avoid FALSE serialization** — don't chain independent steps just because they touch the "same"
  repo. Give each worker its own git worktree, or have workers return drafts to one coordinator
  that applies them.

## Custom Subagent Configuration

```yaml
---
name: code-reviewer
description: Reviews code for quality and security. Use proactively after changes.
tools: Read, Grep, Glob, Bash
model: sonnet
---

You are a senior code reviewer focusing on:
- Security vulnerabilities
- Performance issues
- Code quality and maintainability

Review process:
1. Run git diff to see changes
2. Analyze modified files
3. Report issues by priority (critical/high/medium/low)
```

## Subagent Design Principles

### Focused Scope
One subagent = one responsibility. Don't create swiss-army-knife agents.

### Clear Descriptions
Description drives automatic delegation. Be specific:
```
# Good
Reviews code for security vulnerabilities. Use after code modifications.

# Poor  
Helps with code stuff.
```

### Appropriate Tool Restrictions
Only grant tools the subagent needs:
```yaml
# Code reviewer: read-only
tools: Read, Grep, Glob

# Test runner: can execute
tools: Read, Bash, Write
```

### Model Selection
- **Fast tier**: Quick exploration, simple tasks
- **Balanced tier**: Most tasks, good capability-to-speed ratio
- **Capable tier**: Complex reasoning (use when needed)
- **inherit**: Match main conversation's model

## Resumable Subagents

Subagents can be resumed to continue previous work:

```
Initial: "Use code-analyzer to review authentication module"
[Agent returns with agentId: abc123]

Resume: "Resume agent abc123 and now review authorization"
[Agent continues with full context from previous work]
```

Useful for:
- Multi-session research
- Iterative refinement
- Sequential related tasks

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Custom subagent for everything | Overhead, rigidity | Use general Task() |
| Too broad scope | Context pollution | Split into focused agents |
| No tool restrictions | Security/safety risks | Grant minimal needed tools |
| Vague description | Poor automatic delegation | Be specific about when to use |

## Sources

- Prefer Task() over custom subagents: https://shrivu.substack.com/p/tips-for-claude-code-power-users
- Subagents documentation: https://docs.claude.com/en/docs/claude-code/sub-agents


## Sources

- [Claude Code Subagents](https://code.claude.com/docs/en/sub-agents) - Official documentation
- [How I Use Claude Code](https://shrivastava.io/p/how-i-use-claude-code) - Task() delegation patterns
