---
name: building-skills
description: Invoke when creating, updating, or validating skills. Apply conciseness principle to all skill content. Validate with `python skills/building-skills/scripts/validate.py` after edits. For context strategy (skill vs CLAUDE.md vs MCP), read optimizing-context skill instead.
---

# Building Skills

## Table of Contents

1. [Core Principles](#core-principles)
2. [Creation Framework](#creation-framework)
3. [Quality Checklist](#quality-checklist)

---

## Core Principles

Apply these to every skill you create.

### Conciseness

The context window is a shared resource. Your skill competes with:
- System prompt
- Conversation history
- Other skills' metadata
- The user's request

**Default assumption**: Claude is already very smart.

Only add context Claude doesn't already have. Challenge each piece:
- "Does Claude really need this explanation?"
- "Can I assume Claude knows this?"
- "Does this paragraph justify its token cost?"

**Good** (~50 tokens):
```markdown
## Extract PDF text

Use pdfplumber for text extraction:

```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```
```

**Bad** (~150 tokens):
```markdown
## Extract PDF text

PDF (Portable Document Format) files are a common file format that contains
text, images, and other content. To extract text from a PDF, you'll need to
use a library. There are many libraries available for PDF processing, but we
recommend pdfplumber because it's easy to use...
```

The concise version assumes Claude knows what PDFs are.

### Description as Instruction

The description is injected into the system prompt—the ONLY part guaranteed in context. Everything else loads on-demand.

```
System prompt (always present):
  └── Skill descriptions (name + description from ALL skills)

Context (loaded on-demand):
  └── SKILL.md body (when skill activates)
      └── references/ (when Claude reads them)
```

**Pattern**: `[Trigger phrase] [conditions]. [Immediate instructions]. [What to check/read].`

**Weak** (passive summary):
```
description: Foundational engineering principles for structured work.
```
Problems: Doesn't tell Claude WHEN to activate or WHAT to do immediately.

**Strong** (active instruction):
```
description: Invoke when designing architecture or reviewing designs BEFORE implementation. Apply waste identification to outputs. Run SSoT check before presenting.
```

### Degrees of Freedom

Match instruction specificity to task fragility.

| Freedom | Use When | Example |
|---------|----------|---------|
| High (text guidance) | Multiple valid approaches | Code review guidelines |
| Low (exact scripts) | Fragile operations, specific sequence | Database migration |

Think of Claude navigating a path:
- **Narrow bridge with cliffs**: Only one safe way. Exact instructions.
- **Open field**: Many paths work. General direction.

### Model Testing

Test with all target models. What works for Opus may need more detail for Haiku.

| Model | Check |
|-------|-------|
| Haiku 4.5 | Enough guidance? |
| Sonnet 4.6 | Clear and efficient? |
| Opus 4.8 | Avoids over-explaining? |

---

## Creation Framework

### 1. Draft Evaluations First

Draft 3+ test cases before writing documentation — a manual authoring discipline, not a tooled gate. Empirical execution (baselines, grading, benchmarks) is delegated; see [evaluation-patterns.md](references/evaluation-patterns.md) for test structure and the delegation pointer.

### 2. Develop Iteratively

Work through a task with Claude A (author). Test with Claude B (fresh instance). Iterate on failures. See [creation-process.md](references/creation-process.md) for Claude A/B workflow.

### 3. Initialize

```bash
python skills/building-skills/scripts/init.py <skill-name> [output-directory]
```

### 4. Implement

Use imperative form ("Extract text" not "This extracts text"). Structure for progressive disclosure—core instructions in SKILL.md, details in references linked inline. See [progressive-patterns.md](references/progressive-patterns.md) for organization patterns.

For multi-step processes, see [workflows.md](references/workflows.md). For output templates, see [output-patterns.md](references/output-patterns.md).

### 5. Validate

```bash
python skills/building-skills/scripts/validate.py <skill-folder>
```

If validation fails, see [validation-rules.md](references/validation-rules.md) for constraints.

### 6. Review Security

Before publishing, verify no hardcoded secrets and audit any third-party code. See [security.md](references/security.md).

### 7. Package

```bash
python skills/building-skills/scripts/package.py <skill-folder> [output-directory]
```

---

## Quality Checklist

### Validation (errors)

- [ ] `name:` FIRST, `description:` SECOND in frontmatter
- [ ] Name: matches folder, kebab-case, <=64 chars, no reserved words
- [ ] Description: STARTS with trigger, <=1024 chars, no XML chars
- [ ] Body: within the char cap (validate.py owns the number), ToC if >150 lines
- [ ] No emojis in SKILL.md or scripts (use ASCII: `[OK]`, `[FAIL]`, `[WARN]`)

### Process

- [ ] 3+ test cases drafted before documentation (manual; empirical eval delegated)
- [ ] Tested with target models
- [ ] Core principles applied (conciseness, description-as-instruction)
- [ ] References inline at point of need, one level deep
- [ ] Scripts tested, dependencies listed
- [ ] Packaged with `package.py`

### Anti-Pattern Baselines (SkillReducer, 2026)

Audit against public skill quality baselines:
- [ ] Description present and starts with trigger phrase (26.4% of public skills fail this)
- [ ] Body content >40% actionable instructions — not preamble, examples, or documentation
- [ ] Description activates on 3+ realistic user phrasings, not documentation language
