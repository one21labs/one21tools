# Output Patterns

Read this when designing skill outputs (reports, messages, generated content).

## Table of Contents

1. [Default with Escape Hatch](#default-with-escape-hatch)
2. [Template Pattern](#template-pattern)
3. [Examples Pattern](#examples-pattern)

---

## Default with Escape Hatch

Provide one default approach. Don't overwhelm with options.

**Bad**:
```
You can use pypdf, or pdfplumber, or PyMuPDF, or pdf2image...
```

**Good**:
```
Use pdfplumber for text extraction:

```python
import pdfplumber
```

For scanned PDFs requiring OCR, use pdf2image with pytesseract instead.
```

---

## Template Pattern

Provide templates for output format. Match strictness to needs.

### Strict (API responses, data formats)

```markdown
## Report structure

ALWAYS use this exact template:

# [Analysis Title]

## Executive summary
[One-paragraph overview]

## Key findings
- Finding 1 with data
- Finding 2 with data

## Recommendations
1. Specific action
2. Specific action
```

For token efficiency when the output is structured/tabular data (not prose), see optimizing-context's [token-format-efficiency.md](../../optimizing-context/references/token-format-efficiency.md).

### Flexible (when adaptation useful)

```markdown
## Report structure

Sensible default - use judgment:

# [Analysis Title]

## Executive summary
[Overview]

## Key findings
[Adapt based on discoveries]

## Recommendations
[Tailor to context]
```

---

## Examples Pattern

For quality-dependent outputs, provide input/output pairs:

```markdown
## Commit message format

**Example 1:**
Input: Added user authentication with JWT tokens
Output:
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware

**Example 2:**
Input: Fixed bug where dates displayed incorrectly
Output:
fix(reports): correct date formatting in timezone conversion

Use UTC timestamps consistently
```

Examples teach style better than descriptions.
