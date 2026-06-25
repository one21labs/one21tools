# one21tools

Claude Code skills for software development and engineering workflows.

Built on manufacturing engineering principles — Lean, TPS, Deming — applied to AI-assisted development. Every skill is designed to give Claude the right context at the right altitude: no redundancy, no noise, no content Claude already knows.

The differentiating idea: manufacturing quality principles translate directly to AI-assisted code. Lean's waste elimination becomes YAGNI and SSoT enforcement. Toyota's poka-yoke becomes boundary validation. Deming's "build quality in" becomes catching defects at source rather than inspecting them out downstream. The skills encode these as Claude directives, not engineering platitudes.

## Skills

| Skill | What it does |
|-------|--------------|
| `code-standards` | Language-agnostic code quality standards: file headers, naming, error handling, logging. SSoT and altitude as the governing tests for what belongs in a comment. |
| `engineering-principles` | Lean/TPS/Deming manufacturing principles applied to software, documentation, and process. Includes context engineering mapped to TPS. |
| `building-skills` | Framework for creating, testing, and validating Claude Code skills. Covers conciseness, description-as-instruction, and iterative testing. |
| `optimizing-context` | Patterns for structuring Claude's context efficiently: CLAUDE.md, skills, plugins, subagents, MCP, hooks. |

## Install

Add the marketplace and install plugins from within Claude Code:

```
/plugin marketplace add one21labs/one21tools
/plugin install dev-skills@one21tools
/plugin install engineering-skills@one21tools
```

`dev-skills` bundles code-standards, building-skills, and optimizing-context. `engineering-skills` bundles engineering-principles, engineering-epc, and c-embedded-rpi.

To get updates after installation:

```
/plugin marketplace update one21tools
```

Or clone and symlink individual skills without the plugin system:

```bash
git clone https://github.com/one21labs/one21tools.git
ln -s /path/to/one21tools/skills/code-standards ~/.claude/skills/code-standards
```

## License

MIT — see [LICENSE](LICENSE).
