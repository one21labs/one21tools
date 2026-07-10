# Progressive Disclosure Patterns

Read this when organizing skills with multiple domains or conditional loading.

## Table of Contents

1. [High-Level Guide with References](#pattern-1-high-level-guide-with-references)
2. [Domain-Specific Organization](#pattern-2-domain-specific-organization)
3. [Conditional Details](#pattern-3-conditional-details)
4. [Reference File Guidelines](#reference-file-guidelines)

---

## Pattern 1: High-Level Guide with References

```markdown
# PDF Processing

## Quick start

Extract text with pdfplumber:

```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

## Advanced features

- **Form filling**: See [FORMS.md](FORMS.md)
- **API reference**: See [REFERENCE.md](REFERENCE.md)
- **Examples**: See [EXAMPLES.md](EXAMPLES.md)
```

Claude loads FORMS.md, REFERENCE.md, or EXAMPLES.md only when needed.

---

## Pattern 2: Domain-Specific Organization

For skills with multiple domains, organize by domain:

```
bigquery-skill/
├── SKILL.md (overview and navigation)
└── references/
    ├── finance.md (revenue, billing metrics)
    ├── sales.md (opportunities, pipeline)
    ├── product.md (API usage, features)
    └── marketing.md (campaigns, attribution)
```

When user asks about sales metrics, Claude only reads sales.md.

For framework variants:

```
cloud-deploy/
├── SKILL.md (workflow + provider selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

---

## Pattern 3: Conditional Details

Show basic content, link to advanced:

```markdown
# DOCX Processing

## Creating documents

Use docx-js for new documents. See [DOCX-JS.md](DOCX-JS.md).

## Editing documents

For simple edits, modify XML directly.

**For tracked changes**: See [REDLINING.md](REDLINING.md)
**For OOXML details**: See [OOXML.md](OOXML.md)
```

Claude reads REDLINING.md or OOXML.md only when needed.

---

## Reference File Guidelines

Keep references one level deep. Claude may partially read deeply nested files.

**Bad** (too deep):
```
# SKILL.md → advanced.md → details.md
```

**Good** (flat):
```
# SKILL.md
**Basic**: [instructions here]
**Advanced**: See [advanced.md](advanced.md)
**API**: See [reference.md](reference.md)
```

Embed references inline at point of need, not in tables.

**Bad** (disconnected):
```markdown
## References
| Reference | When to Read |
|-----------|--------------|
| forms.md | Form filling |
```

**Good** (contextual):
```markdown
## Form Processing
Extract fields first. For complex forms, see [forms.md](forms.md).
```

| Guideline | Reason |
|-----------|--------|
| One level deep from SKILL.md | Claude may partially read nested files |
| ToC past the length gate `validate.py` enforces (owns the number) | Helps Claude navigate long content |
| Descriptive names | `form_validation_rules.md` not `doc2.md` |
