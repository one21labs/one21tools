# JIT Documentation

Just-In-Time documentation: place each piece of knowledge at the point of use, loaded at the moment it is needed — not always.

## Core Principle

Documentation has a load cost. Always-loaded context (CLAUDE.md, system prompts) consumes tokens on every session whether or not the information is relevant. Source file headers load only when that file is read. The right location is determined by scope.

> "Would Claude need this before opening any file, or only when editing this specific file?"

- Cross-cutting constraint (applies everywhere) → always-loaded context (CLAUDE.md)
- File-specific constraint (only relevant when in this file) → source file header

Placing file-specific documentation in always-loaded context is waste: it costs tokens every session but adds value only rarely.

## Decision Test

Ask these questions in order:

| Question | Yes | No |
|----------|-----|-----|
| Must the rule travel with a skill/plugin when installed elsewhere? | → a shipped skill/plugin file (SKILL.md, references/, agents/, hooks/, scripts/); repo-level docs may point at it, never solely house it | next question |
| Does this apply to every file in the project? | → CLAUDE.md | next question |
| Does this apply to a specific module or file? | → source header | next question |
| Does this describe a feature plan or future intent? | → ROADMAP | next question |
| Is this a reusable procedure across projects? | → Skill | consider if needed at all |

## What Belongs Where

| Location | Scope | Examples |
|----------|-------|---------|
| CLAUDE.md | Cross-cutting; always relevant | Storage key prefix, naming conventions, sacred files, build commands |
| Source file header | File-specific; JIT on read | Architecture role, design constraints, used-by, see-also, gotchas |
| ROADMAP.md | Future intent | Planned features, deferred decisions |
| Skill | Reusable procedure | Decision frameworks, checklists, domain patterns |

## Source File Header Pattern

A source header carries the file's **architecture role, design constraints, used-by, and
see-also** — omit any section with nothing non-obvious to say. The section *schema* and the
SSoT/altitude tests for what belongs in a header have their one home in the `code-standards` skill
(File Headers); this skill owns only the *placement* call above — that this knowledge lives in the
header (loaded JIT on read), never in always-loaded CLAUDE.md.

## Worked Example

**Scenario**: A `license.js` module gates Pro features. The pattern — "all new features must call a `canX()` function before rendering" — needs to be documented somewhere.

**Wrong**: Add to CLAUDE.md.
- It only matters when working in license.js or adding a gated feature
- Costs tokens every session; relevant rarely
- CLAUDE.md is for cross-cutting constraints, not module-specific patterns

**Right**: Document in the license.js header under DESIGN CONSTRAINTS and USED BY.
- Loads JIT when Claude opens the file
- Lists every `can*` export and their callers
- Zero always-loaded cost

Result: Claude reads the header when opening license.js and has exactly the context needed, exactly when needed.

## Common Violations

| Symptom | Violation | Fix |
|---------|-----------|-----|
| CLAUDE.md lists every feature the app has | Feature inventory in always-loaded context | Move to source headers or ROADMAP |
| Source header says "this is a React component" | Restates the obvious | Delete; document only non-obvious constraints |
| Same constraint in CLAUDE.md and source header | SSoT violation | Pick one canonical location; remove the other |
| No header on a file with non-obvious behavior | Missing JIT doc | Add header with DESIGN CONSTRAINTS |

## Relationship to SSoT

JIT documentation is SSoT applied to documentation placement. SSoT asks "is this fact in one place?" JIT asks "is that one place the right place?" Both violations result in wasted tokens or missed context.

See `ssot-enforcement.md` for the broader SSoT audit process.
