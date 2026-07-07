# Evaluation Patterns

Read this when designing tests for your skill.

## Table of Contents

1. [Evaluation Structure](#evaluation-structure)
2. [Test Matrix](#test-matrix)
3. [Triggering Tests](#triggering-tests)
4. [Functional Tests](#functional-tests)
5. [Baseline Comparison](#baseline-comparison)
6. [Empirical Evaluation](#empirical-evaluation)

---

## Evaluation Structure

Author test cases as `evals/evals.json` in the skill folder, in **skill-creator's schema** —
its `references/schemas.md` is the schema SSoT (don't restate it here; a mirror drifts).
Live example: `skills/code-standards/evals/evals.json`. `validate.py` gates the shape.

Authorship discipline — a delta on the Claude A/B split ([creation-process.md](creation-process.md)):
have fresh Claude B write the `expectations` assertions, not the skill's author. An author
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

## Empirical Evaluation

The full protocol — paired benchmark on skill-creator's harness, pressure cases, and the
owned cost-per-benefit verdict (`scripts/eval_verdict.py`) — lives in
[empirical-evals.md](empirical-evals.md) (ADR 0013). No skill-creator installed = the manual
baseline steps above suffice. Method writeup:
https://agentskills.io/skill-creation/evaluating-skills

Caveats when crossing over:
- validate.py stays authoritative for skills in this repo: its description-trigger rule is
  stricter than skill-creator's own conventions (skill-creator's own description would fail it).
- On the harness path, grade with a fresh, ideally different, model — the bundled grader
  otherwise inherits the session model.
