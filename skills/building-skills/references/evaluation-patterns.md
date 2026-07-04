# Evaluation Patterns

Read this when designing tests for your skill.

## Table of Contents

1. [Evaluation Structure](#evaluation-structure)
2. [Test Matrix](#test-matrix)
3. [Triggering Tests](#triggering-tests)
4. [Functional Tests](#functional-tests)
5. [Baseline Comparison](#baseline-comparison)
6. [Empirical Evaluation (Delegated)](#empirical-evaluation-delegated)

---

## Evaluation Structure

Illustrative shape for hand-authored test cases — NOT skill-creator's `evals.json` wire format,
which differs on every key (see [Empirical Evaluation](#empirical-evaluation-delegated)):

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

Authorship discipline — a delta on the Claude A/B split ([creation-process.md](creation-process.md)):
have fresh Claude B write the `expected_behavior` assertions, not the skill's author. An author
grades their own intent; a fresh instance grades the artifact.

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

---

## Empirical Evaluation (Delegated)

This skill owns authoring-time checks and the deterministic gate (validate.py). It does not own
quality measurement. If Anthropic's skill-creator skill is installed (anthropic agent-skills
marketplace — NOT bundled with Claude Code, NOT shipped by this marketplace), run its empirical
harness for with/without-skill baselines, graded assertions, and benchmark deltas; otherwise the
manual steps above suffice. Method writeup:
https://agentskills.io/skill-creation/evaluating-skills

Caveats when crossing over:
- skill-creator's `evals.json` schema differs from the illustrative shape above — author harness
  eval files against its `references/schemas.md`, not this page.
- validate.py stays authoritative for skills in this repo: its description-trigger rule is
  stricter than skill-creator's own conventions (skill-creator's own description would fail it).
- On the harness path, grade with a fresh, ideally different, model — the bundled grader
  otherwise inherits the session model.
