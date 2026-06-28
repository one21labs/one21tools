# Creation Process

Read this for detailed skill creation workflow.

## Table of Contents

1. [Claude A/B Development](#claude-ab-development)
2. [Resource Planning](#resource-planning)
3. [Writing Scripts](#writing-scripts)
4. [Content Guidelines](#content-guidelines)
5. [Iteration](#iteration)

---

## Claude A/B Development

Use two Claude instances:
- **Claude A**: Author (helps design/refine the skill)
- **Claude B**: Tester (uses the skill on real tasks)

### Creating a New Skill

1. **Complete a task without a skill**: Work through a problem with Claude A. Notice what context you repeatedly provide.

2. **Identify reusable pattern**: What context would help future similar tasks?

3. **Ask Claude A to create skill**: "Create a skill capturing this pattern. Include the table schemas and filtering rules."

4. **Review for conciseness**: "Remove explanation of win rate - Claude knows that."

5. **Test with Claude B**: Give Claude B (fresh instance with skill loaded) real tasks.

6. **Iterate**: "Claude B forgot to filter test accounts. Should we add a section?"

### Iterating on Existing Skills

1. Use skill in real workflows with Claude B
2. Observe struggles: Where does it fail?
3. Return to Claude A: Share observations, ask for improvements
4. Apply and retest

---

## Resource Planning

| Type | Include When |
|------|--------------|
| `scripts/` | Same code rewritten repeatedly |
| `references/` | Domain knowledge to load as needed |
| `assets/` | Files used in output (templates, images) |

Don't create directories you won't use.

---

## Writing Scripts

Run `--help` on any script for usage and options.

### Solve, Don't Punt

Scripts should handle problems, not pass them to Claude.

**Bad** (punts to Claude):
```python
def process_file(path):
    return open(path).read()  # Just fails, Claude figures it out
```

**Good** (handles errors):
```python
def process_file(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        print(f"File {path} not found, creating default")
        with open(path, 'w') as f:
            f.write('')
        return ''
```

### Explicit Error Messages

Error messages should tell Claude exactly what's wrong and how to fix it.

**Bad**: `Error: invalid input`

**Good**: `Error: Field 'signature_date' not found. Available fields: customer_name, order_total, signature_date_signed`

### No Magic Constants

Justify all configuration values.

**Bad**:
```python
TIMEOUT = 47  # Why 47?
```

**Good**:
```python
# HTTP requests typically complete within 30 seconds
REQUEST_TIMEOUT = 30
```

### File Paths

Always use forward slashes, even on Windows.

```
✓ scripts/helper.py
✗ scripts\helper.py
```

### Dependencies

List install commands. Don't assume packages are available.

**Bad**: `Use the pdf library to process the file.`

**Good**:
```
Install required package: `pip install pypdf`

```python
from pypdf import PdfReader
```
```

---

## Content Guidelines

### Avoid Time-Sensitive Information

**Bad**:
```
If you're doing this before August 2025, use the old API.
```

**Good** (collapsible legacy section):
```markdown
## Current method

Use the v2 API endpoint.

<details>
<summary>Legacy v1 API (deprecated)</summary>
The v1 API is no longer supported.
</details>
```

### Consistent Terminology

Choose one term and use it throughout.

**Good**: Always "API endpoint", always "field", always "extract"

**Bad**: Mix "API endpoint" / "URL" / "route" / "path"

### What NOT to Include

Skills are for AI agents, not humans. Do NOT create:
- README.md
- CHANGELOG.md  
- CONTRIBUTING.md
- INSTALLATION_GUIDE.md

---

## Iteration

### Observe Navigation

Watch how Claude uses the skill:
- **Unexpected paths**: Structure may not be intuitive
- **Missed connections**: Links need prominence
- **Overreliance on sections**: Consider moving content to SKILL.md
- **Ignored files**: May be unnecessary or poorly signaled
