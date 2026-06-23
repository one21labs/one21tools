# When to Use MCP

Model Context Protocol (MCP) provides connectivity to external services. This guide covers *decision-making only*; for implementation, see `mcp-builder` skill.

## When MCP vs Other Mechanisms

| Situation | Use MCP? | Alternative |
|-----------|----------|-------------|
| Need real-time external data | Yes | — |
| Need to trigger external actions | Yes | — |
| Static reference material | No | Project Knowledge or Skill references |
| Procedural knowledge | No | Skill |
| Local file operations | No | Native Claude Code tools |

## Decision Questions

Ask these before building an MCP server:

1. **Does Claude need live data?** If cached/static data works, skip MCP.
2. **Could a simpler approach work?** CLI wrappers, direct API calls in scripts, or uploaded files may suffice.
3. **Is the data source stable?** MCP adds infrastructure overhead—worth it only for frequently-used integrations.
4. **Will multiple conversations need this?** One-time data needs don't justify MCP.

## Core Design Principle: Data Gateway

MCP should expose **high-level data operations**, not mirror every API endpoint.

| Data Gateway (preferred) | API Mirror (avoid) |
|--------------------------|-------------------|
| `get_customer_context()` | `get_customer()`, `get_orders()`, `get_tickets()` |
| `execute_query()` | `connect()`, `prepare()`, `execute()`, `fetch()` |
| Fewer tools, raw data | Many narrow tools |

Let Claude script against raw data rather than managing low-level API navigation. Fewer tools = easier discovery = better results.

## MCP vs CLI Wrappers

| Factor | MCP Server | CLI Wrapper in Skill |
|--------|------------|---------------------|
| State management | Built-in | Manual |
| Tool discovery | Automatic | Explicit invocation |
| Setup complexity | Higher | Lower |
| Best for | Persistent integrations | Simple one-off operations |

**Guidance**: Start with CLI wrappers in skills. Upgrade to MCP when you need persistent connections, automatic tool discovery, or shared infrastructure across projects.

## When NOT to Use MCP

- Data could be pre-loaded to Project Knowledge
- A simple script in a Skill would suffice
- Native tools already handle the operation
- One-time data extraction (just do it inline)

## Implementation

Once you've decided MCP is the right mechanism, see:
- `mcp-builder` skill for server development workflow
- `product-self-knowledge` for MCP configuration in Claude Code


## Sources

- [Claude Code MCP Documentation](https://code.claude.com/docs/en/mcp) - Configuration reference
- [Extending Claude with Skills and MCP](https://claude.com/blog/extending-claude-capabilities-with-skills-mcp-servers) - Skills vs MCP comparison
- [How I Use Claude Code](https://shrivastava.io/p/how-i-use-claude-code) - MCP as data gateway pattern
