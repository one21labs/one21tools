# Plugins Reference

Claude Code plugins package agents, skills, commands, and hooks for distribution and selective installation.

## Table of Contents

1. [When to Use Plugins](#when-to-use-plugins)
2. [Critical Behavior: Default Directories and Explicit Paths](#critical-behavior-default-directories-and-explicit-paths)
3. [Component Directories as Sources](#component-directories-as-sources)
4. [Marketplace.json Structure](#marketplacejson-structure)
5. [Monorepo Pattern](#monorepo-pattern)
6. [Plugin Caching](#plugin-caching)
7. [Verification](#verification)
8. [Common Patterns](#common-patterns)
9. [References](#references)

---

## When to Use Plugins

Use plugins to distribute reusable tools that users can selectively install:

- **Scenario**: Team/community wants to share Claude Code extensions
- **Benefit**: Users install only what they need, reducing always-loaded context
- **Alternative**: CLAUDE.md or project settings (for single-repo use)

---

## Critical Behavior: Default Directories and Explicit Paths

A plugin's default directories are scanned automatically:

| Directory    | Component      |
|--------------|----------------|
| `/skills/`   | Agent Skills   |
| `/agents/`   | Subagents      |
| `/commands/` | Slash commands |

How an explicit path combines with the default depends on the field
([plugins reference](https://code.claude.com/docs/en/plugins-reference)):

| You set | Result |
|---------|--------|
| Nothing | Everything in the default directories loads |
| `skills` in a plugin's own manifest | Adds to the default `skills/` scan |
| `commands`, `agents` or `outputStyles` | Replaces the default directory, which is no longer scanned |
| `skills` subdirectories on a marketplace entry whose `source` is the marketplace root | Only those subdirectories load; the default `skills/` is not scanned |

A plugin that has its own manifest and a `skills/` directory therefore loads all of that
directory, whatever else it lists. Confirm what loaded (Verification, below); do not trust the
layout alone.

---

## Component Directories as Sources

One layout that keeps each plugin to its own content: use a component directory (`./skills`,
`./agents`, `./commands`) as the plugin source, and list what loads.

```json
{
  "name": "embedded-skills",
  "source": "./skills",
  "strict": false,
  "skills": ["./c-embedded-rpi"]
}
```

What happens:
1. Only the `skills/` directory is copied to cache
2. Only the listed skills load for this plugin

---

## Marketplace.json Structure

### Basic Format

```json
{
  "name": "my-toolkit",
  "owner": {
    "name": "Team Name",
    "email": "team@example.com"
  },
  "metadata": {
    "description": "Tools for X"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "source": "./path",
      "description": "What it does"
    }
  ]
}
```

### Key Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `name` | Plugin identifier | `"engineering-skills"` |
| `source` | What gets copied to cache | `"./skills"` |
| `strict` | Which manifest defines the plugin | `false` (for simple plugins) |
| `skills` | Which skills to load | `["./skill-a", "./skill-b"]` |
| `agents` | Which agents to load | `["./agent-a.md"]` |
| `commands` | Which commands to load | `["./cmd-a.md"]` |

### The `strict` Field

Decides which manifest defines the plugin when it has its own `plugin.json`:

- `strict: true` (default): `plugin.json` is the manifest; the entry's `skills`, `commands` and
  `agents` are appended to it
- `strict: false`: the marketplace entry defines the plugin. Do not also give that plugin a
  `plugin.json`: the two conflict and the plugin fails to load (`conflicting manifests`)

With no `plugin.json`, the entry defines the plugin under either value.

Use `strict: false` for:
- Simple plugins defined entirely in marketplace
- Component-only plugins (just skills, agents, or commands)
- Avoiding redundant plugin.json files

---

## Monorepo Pattern

Organize by component type for selective installation:

### Directory Structure

```
/repo-root/
  /.claude-plugin/
    marketplace.json
  /skills/
    /skill-a/
    /skill-b/
    /skill-c/
  /agents/
    agent-1.md
    agent-2.md
  /commands/
    cmd-1.md
    cmd-2.md
```

### Marketplace Configuration

```json
{
  "name": "my-toolkit",
  "owner": {"name": "Team"},
  "metadata": {
    "description": "Toolkit for X"
  },
  "plugins": [
    {
      "name": "embedded-skills",
      "source": "./skills",
      "strict": false,
      "skills": ["./skill-a"]
    },
    {
      "name": "engineering-skills",
      "source": "./skills",
      "strict": false,
      "skills": ["./skill-b", "./skill-c"]
    },
    {
      "name": "subagents",
      "source": "./agents",
      "strict": false,
      "agents": ["./agent-1.md", "./agent-2.md"]
    },
    {
      "name": "commands",
      "source": "./commands",
      "strict": false,
      "commands": ["./cmd-1.md", "./cmd-2.md"]
    }
  ]
}
```

### Benefits

- **Flat structure**: Easy to browse and edit
- **Selective loading**: Each plugin loads only specified content
- **Minimal duplication**: Shared source, different loading rules
- **Clear separation**: Users install only what they need

---

## Plugin Caching

When plugins install, Claude Code copies content to
`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` (set `CLAUDE_CODE_PLUGIN_CACHE_DIR`
to move the root). There is no per-project cache, and a project's `.claude/plugins/` is not
scanned: a team shares plugins by declaring them in `.claude/settings.json`.

### What Gets Copied

The `source` field determines what gets copied:

```json
{"source": "./"} → Entire repo copied
{"source": "./skills"} → Only skills/ directory copied
{"source": "./plugins/my-plugin"} → Only that plugin directory copied
```

### Cache Implications

Each plugin copies its `source` separately. If multiple plugins share `"source": "./skills"`:
- All plugins copy the same `/skills/` directory to cache
- Slight duplication, but controlled
- Only specified skills load per plugin

---

## Verification

### Test Plugin Loading

```bash
# Validate marketplace
claude plugin validate .

# Install for testing
claude plugin install my-plugin@my-marketplace

# Check what loaded
# In Claude Code:
/context
```

Look at the "Plugin" section to verify only intended components loaded.

### Debug Issues

```bash
# Detailed plugin loading info
claude --debug
```

Common issues:
- All skills loading → the default `skills/` directory is being scanned (see Critical Behavior)
- Nothing loading → Paths incorrect (verify relative to source)
- Validation errors → Check JSON syntax in marketplace.json

---

## Common Patterns

### Pattern 1: Skill Bundles

Organize skills by domain:

```json
{
  "plugins": [
    {
      "name": "data-skills",
      "source": "./skills",
      "strict": false,
      "skills": ["./data-processing", "./visualization"]
    },
    {
      "name": "web-skills",
      "source": "./skills",
      "strict": false,
      "skills": ["./frontend-design", "./api-testing"]
    }
  ]
}
```

### Pattern 2: Role-Based Plugins

Bundle components by user role:

```json
{
  "plugins": [
    {
      "name": "developer-tools",
      "source": "./plugins/developer-tools"
    },
    {
      "name": "designer-tools",
      "source": "./plugins/designer-tools"
    }
  ]
}
```

Each role is its own directory holding its `skills/`, `agents/`, and `commands/`, so each
plugin's defaults hold only its own content.

---

## References

- [Claude Code Plugin Documentation](https://code.claude.com/docs/en/plugins.md)
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces.md)
- [Plugins Reference](https://code.claude.com/docs/en/plugins-reference.md)
