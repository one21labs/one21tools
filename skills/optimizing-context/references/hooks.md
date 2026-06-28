# When to Use Hooks

Hooks are lifecycle event handlers in Claude Code that run code before or after Claude performs operations. This guide covers *decision-making only*; for implementation, see Claude Code documentation.

## When Hooks vs Other Mechanisms

| Situation | Use Hooks? | Alternative |
|-----------|------------|-------------|
| Must ALWAYS happen on every operation | Yes | — |
| Policy enforcement (hard rules) | Yes | — |
| Context-dependent decision | No | Let Claude decide, use CLAUDE.md for guidance |
| One-time rule | No | State in prompt |
| Procedural knowledge | No | Skill |

## Decision Questions

Ask these before implementing a hook:

1. **Must this ALWAYS happen?** Hooks fire on every matching event. If it's optional or contextual, don't use a hook.
2. **Is this enforcement or guidance?** Hooks enforce; CLAUDE.md guides.
3. **Can Claude reasonably decide?** If judgment is needed, skip the hook.
4. **Is it cross-cutting?** Hooks work across all operations of a type.

## Hook Types and When to Use Each

| Hook | Fires When | Decision Criteria |
|------|------------|-------------------|
| **PreToolUse** | Before any tool runs | Need to validate, block, or modify before execution? |
| **PostToolUse** | After tool completes | Need to log, transform output, or trigger follow-up? |
| **Stop** | Session/turn ends | Need cleanup, summary, or quality gate? |
| **UserPromptSubmit** | User sends message | Need to inject context or validate input? |
| **Notification** | Events occur | Need external alerts or integrations? |

## Hooks vs CLAUDE.md

| Hooks | CLAUDE.md |
|-------|-----------|
| **Enforces** automatically | **Guides** Claude's judgment |
| Runs code | Provides instructions |
| Cannot be bypassed | Claude interprets |
| For hard policies | For soft conventions |

**Example distinction**:
- Hook: "Block writes to /prod" (hard enforcement)
- CLAUDE.md: "Prefer staging for testing" (guidance)

## Hooks vs Skills

| Hooks | Skills |
|-------|--------|
| Event-driven automation | On-demand procedures |
| Cross-cutting concerns | Task-specific knowledge |
| Always active when configured | Loaded when relevant |
| Policy layer | Knowledge layer |

## When NOT to Use Hooks

- **Context-dependent decisions**: Let Claude reason with CLAUDE.md guidance
- **One-off requirements**: State in prompt
- **Complex procedural logic**: Use Skills with scripts
- **External data needs**: Use MCP
- **Guidance over enforcement**: Use CLAUDE.md

## Performance Consideration

Hooks run on every matching operation. If a hook is slow, it slows everything. Consider whether the enforcement value justifies the overhead.

## Implementation

Once you've decided a hook is needed, see:
- Claude Code documentation for hook configuration
- `product-self-knowledge` for settings file locations


## Sources

- [Claude Code Hooks Documentation](https://code.claude.com/docs/en/hooks) - Implementation reference
- [Claude Code Settings](https://code.claude.com/docs/en/settings) - Configuration locations
