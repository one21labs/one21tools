# Validation Rules

Read this when validating skill structure or debugging validation failures.

## Table of Contents

1. [Running Validation](#running-validation)
2. [YAML Frontmatter](#yaml-frontmatter)
3. [Name Constraints](#name-constraints)
4. [Description Constraints](#description-constraints)
5. [Body Constraints](#body-constraints)
6. [Valid Trigger Phrases](#valid-trigger-phrases)
7. [Emoji Prohibition](#emoji-prohibition)
8. [Test the Consumer Surface](#test-the-consumer-surface)

---

## Running Validation

```bash
python scripts/validate.py <skill-folder>
python scripts/validate.py --help
```

---

## YAML Frontmatter

```yaml
---
name: skill-name             # MUST be FIRST field
description: Invoke when...  # MUST be SECOND field
---
```

| Field | Required | Position | Max Length |
|-------|----------|----------|------------|
| `name` | Yes | FIRST | 64 chars |
| `description` | Yes | SECOND | 1024 chars |

---

## Name Constraints

| Constraint | Type | Source |
|------------|------|--------|
| FIRST field in frontmatter | Error | Claude convention |
| Match folder name | Error | Packaging requirement |
| Max 64 chars | Error | agentskills.io spec |
| Kebab-case only (`a-z`, `0-9`, `-`) | Error | agentskills.io spec |
| No leading/trailing hyphens | Error | agentskills.io spec |
| No consecutive hyphens (`--`) | Error | Kebab-case standard |
| No reserved words (`anthropic`, `claude`) | Error | Upload testing |
| No XML chars (`<`, `>`) | Error | platform.claude.com |
| Gerund form preferred | Convention | platform.claude.com |

### Naming Convention

Use gerund form (verb + -ing) to describe capability:

**Preferred**:
```
processing-pdfs
analyzing-spreadsheets
building-skills
```

**Acceptable alternatives**:
```
pdf-processing
spreadsheet-analysis
```

**Avoid**:
```
helper
utils
pdf-stuff
```

### Valid Names

```
pdf-processor
skill-v2
my-great-skill
```

### Invalid Names

```
PDF-Processor     # uppercase
pdf_processor     # underscore
-pdf-processor    # leading hyphen
pdf-processor-    # trailing hyphen
pdf--processor    # consecutive hyphens
claude            # reserved
anthropic         # reserved
```

---

## Description Constraints

| Constraint | Type | Source |
|------------|------|--------|
| SECOND field in frontmatter | Error | Claude convention |
| Trigger at START | Error | GitHub issues #9954, #11266 |
| Max 1024 chars | Error | agentskills.io spec |
| No XML chars (`<`, `>`) | Error | platform.claude.com |
| Third person preferred | Warning | platform.claude.com |

### Valid Descriptions

```
Invoke when processing PDFs. Extract with pdfplumber.
Use when working with spreadsheets. Read schema first.
Use for code review tasks. Check style guide.
Apply when generating reports. Use template from assets/.
```

### Invalid Descriptions

```
A great skill that does stuff.           # No trigger
Helps with PDF processing.               # No trigger
This skill is for PDFs. Use when needed. # Trigger not at start
```

---

## Body Constraints

| Constraint | Type | Source |
|------------|------|--------|
| Max 6,000 chars | Error | Char budget (a line cap is gameable by long lines) |
| ToC required if >150 lines | Error | Best practice |
| References: max 12,000 chars each | Error | Char budget (progressive-disclosure tier) |
| References: ToC required if >6,000 chars | Error | Best practice |

Draft to a margin (~5,000 body / ~10,000 reference) and measure once before finalizing — a file
at the cap edge taxes every future one-line fix. (Same convention as the ADR template's margin.)
Measure with `validate.py` itself, not a re-derivation: the gate folds frontmatter lines beyond
`name`/`description` into the body count, which a hand count silently misses.

### Table of Contents Formats

Any of these headers are recognized:
```
## Table of Contents
## ToC
## Contents
```

---

## Valid Trigger Phrases

Case-insensitive. Must be at START of description.

| Phrase | Example |
|--------|---------|
| `Invoke when` | Invoke when designing architecture... |
| `Use when` | Use when working with PDF files... |
| `Use for` | Use for code review tasks... |
| `Apply when` | Apply when generating reports... |

### Pattern

```
[Trigger phrase] [conditions]. [Immediate instructions]. [What to check/read].
```

---

## Emoji Prohibition

**Emojis are prohibited in all skill files.**

| Location | Rule | Type |
|----------|------|------|
| SKILL.md (frontmatter) | No emojis | Error |
| SKILL.md (body) | No emojis | Error |
| scripts/*.py | No emojis | Error |
| references/*.md | No emojis | Error |

### Why Emojis Are Prohibited

1. **Terminal compatibility**: Many terminals render emojis inconsistently or not at all
2. **Encoding issues**: Emojis can cause encoding problems across platforms
3. **Professionalism**: ASCII alternatives are clearer and more portable

### ASCII Alternatives

Use these instead of emojis:

| Instead of | Use |
|------------|-----|
| Checkmark emoji | `[OK]` or `[PASS]` |
| X mark emoji | `[FAIL]` or `[ERROR]` |
| Warning emoji | `[WARN]` or `Warning:` |
| Info emoji | `[INFO]` or `Note:` |
| Arrow emoji | `->` or `-->` |

### Valid Output Examples

```python
# Good - ASCII indicators
print("[OK] Validation passed")
print("[FAIL] Missing required field")
print("[WARN] Description uses first person")

# Bad - Emoji indicators (will fail validation)
print("X Validation passed")  # checkmark emoji
print("X Missing field")      # X emoji
print("X Warning")            # warning emoji
```

## Test the Consumer Surface

A shipped artifact's test must exercise it the way its consumer invokes it: a hook via its
hooks.json command line (not a direct `bash script.sh` call), a vendored script from a
consumer-shaped layout, a CLI via its argv entry point. A test that calls internals the
consumer never touches can stay green while the shipped surface is broken.
