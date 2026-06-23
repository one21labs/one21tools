# Plugins Reference

Claude Code plugins package agents, skills, commands, and hooks for distribution and selective installation.

## When to Use Plugins

Use plugins to distribute reusable tools that users can selectively install:

- **Scenario**: Team/community wants to share Claude Code extensions
- **Benefit**: Users install only what they need, reducing always-loaded context
- **Alternative**: CLAUDE.md or project settings (for single-repo use)

---

## Critical Behavior: Auto-Discovery

**Auto-discovery loads all content in default directories**, regardless of what you specify explicitly.

### Default Directories

| Directory   | Component     | Auto-Discovered |
|-------------|---------------|-----------------|
| `/skills/`  | Agent Skills  | Yes             |
| `/agents/`  | Subagents     | Yes             |
| `/commands/` | Slash commands | Yes            |

### The Problem

When these directories exist at the **plugin root**, Claude Code automatically discovers and loads **all** content within them.

**Explicit paths supplement, they don't replace.**

### Example: Anti-Pattern

```json
{
  "name": "my-tools",
  "source": "./",
  "skills": ["./skills/skill-a"]
}
```

What happens:
1. Entire repo copied to cache (because `"source": "./"`)
2. `/skills/` directory exists at plugin root
3. Auto-discovery loads **ALL skills** in `/skills/`
4. Explicit `skills` array is ignored

Result: Users get everything, not just `skill-a`.

---

## Solution: Component Directories as Sources

Use component directories (`./skills`, `./agents`, `./commands`) directly as plugin sources.

### Correct Pattern

```json
{
  "name": "embedded-skills",
  "source": "./skills",
  "strict": false,
  "skills": ["./c-embedded-rpi"]
}
```

What happens:
1. Only `/skills/` directory copied to cache
2. Plugin root = the cached skills directory
3. Individual skills at root level: `/c-embedded-rpi/`, `/engineering-epc/`, etc.
4. No `/skills/` subdirectory → no auto-discovery
5. Only explicitly listed skills load

### Why This Works

**Before copying** (repository structure):
```
/repo-root/
  /skills/
    /c-embedded-rpi/
    /engineering-epc/
    /other-skill/
```

**After copying to cache** (plugin root):
```
/plugin-cache/
  /c-embedded-rpi/       ← At root level
  /engineering-epc/      ← At root level
  /other-skill/          ← At root level
```

Auto-discovery looks for `/skills/` directory at plugin root. It doesn't exist (skills are directly at root), so nothing auto-loads.

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
    "description": "Tools for X",
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "source": "./path",
      "description": "What it does",
      "version": "1.0.0"
    }
  ]
}
```

### Key Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `name` | Plugin identifier | `"engineering-skills"` |
| `source` | What gets copied to cache | `"./skills"` |
| `strict` | Require plugin.json? | `false` (for simple plugins) |
| `skills` | Which skills to load | `["./skill-a", "./skill-b"]` |
| `agents` | Which agents to load | `["./agent-a.md"]` |
| `commands` | Which commands to load | `["./cmd-a.md"]` |

### The `strict` Field

Controls whether plugin needs its own `plugin.json` file:

- `strict: true` (default): Plugin must have `.claude-plugin/plugin.json`
- `strict: false`: Marketplace entry entirely defines plugin

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
    "description": "Toolkit for X",
    "version": "1.0.0"
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

When plugins install, Claude Code copies content to cache:

| Scope     | Location                    | Shared With      |
|-----------|-----------------------------|------------------|
| `user`    | `~/.claude/plugins/cache/`  | All your projects |
| `project` | `./.claude/plugins/cache/`  | Team via git     |

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
- All skills loading → Auto-discovery active (check plugin root structure)
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
      "source": "./",
      "strict": false,
      "skills": ["./skills/code-review"],
      "agents": ["./agents/security-scanner.md"],
      "commands": ["./commands/test.md"]
    },
    {
      "name": "designer-tools",
      "source": "./",
      "strict": false,
      "skills": ["./skills/design-review"],
      "commands": ["./commands/export-figma.md"]
    }
  ]
}
```

### Pattern 3: Component Separation (Recommended for Monorepos)

Separate skills, agents, and commands into distinct plugins:

```json
{
  "plugins": [
    {"name": "skills", "source": "./skills", "strict": false, "skills": [...]},
    {"name": "agents", "source": "./agents", "strict": false, "agents": [...]},
    {"name": "commands", "source": "./commands", "strict": false, "commands": [...]}
  ]
}
```

---

## Key Takeaways

1. **Auto-discovery loads everything** in `/skills/`, `/agents/`, `/commands/` at plugin root
2. **Explicit paths supplement** auto-discovery, they don't replace
3. **Use component directories as sources** to avoid auto-discovery
4. **Set `strict: false`** for simple plugins defined in marketplace
5. **Verify with `/context`** to confirm only intended content loads
6. **Organize by component type** in monorepos for selective installation

---

## References

- [Claude Code Plugin Documentation](https://code.claude.com/docs/en/plugins.md)
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces.md)
- [Plugins Reference](https://code.claude.com/docs/en/plugins-reference.md)
