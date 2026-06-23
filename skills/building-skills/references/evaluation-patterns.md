# Evaluation Patterns

Read this when designing tests for your skill.

## Table of Contents

1. [Evaluation Structure](#evaluation-structure)
2. [Test Matrix](#test-matrix)
3. [Triggering Tests](#triggering-tests)
4. [Functional Tests](#functional-tests)

---

## Evaluation Structure

```json
{
  "skills": ["skill-name"],
  "query": "User request that should trigger the skill",
  "files": ["test-files/input.pdf"],
  "expected_behavior": [
    "Specific observable outcome 1",
    "Specific observable outcome 2",
    "Specific observable outcome 3"
  ]
}
```

---

## Test Matrix

Create at least 3 tests covering:

| Type | Purpose | Example Query |
|------|---------|---------------|
| Normal | Core functionality | "Extract text from this PDF" |
| Edge case | Unusual inputs | PDF with no text, corrupted file |
| Out-of-scope | Should NOT trigger | "View this PDF" (different skill) |

---

## Triggering Tests

### Does Skill Activate When Expected?

Test with explicit requests:
```
"Use the pdf-processing skill to extract tables"
```

Test with natural requests:
```
"Help me get the text from this document"
```

### Does Skill Stay Inactive When Irrelevant?

Test similar but distinct requests:
```
"Convert this image to PDF"  # Different operation
"Open this Word document"     # Different file type
```

---

## Functional Tests

| Test Type | What to Check |
|-----------|---------------|
| Output consistency | Multiple runs produce comparable results |
| Usability | Unfamiliar user can succeed |
| Documentation accuracy | Examples match actual behavior |
| Error handling | Graceful failure with helpful messages |

---

## Baseline Comparison

1. Run test queries WITHOUT skill
2. Document failures/gaps
3. Run same queries WITH skill
4. Compare:
   - Success rate
   - Output quality
   - Error recovery

Skill is effective only if it measurably improves baseline.
