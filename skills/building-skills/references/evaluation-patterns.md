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

Author test cases as `evals/evals.json` in the skill folder; `validate.py` gates the shape.
Schema SSoT, live example, and authorship discipline (fresh Claude B writes the `expectations`,
not the skill's author): empirical-evals.md's "Authoring evals" section — **skill-bench
plugin**, `bench` skill (a separate plugin; no relative link survives an install).

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
skill-bench plugin's cost-per-benefit verdict (`scripts/eval_verdict.py`) — lives in the
skill-bench plugin's empirical-evals.md (ADR 0013). No skill-creator installed = the manual
baseline steps above suffice. Method writeup:
https://agentskills.io/skill-creation/evaluating-skills

Caveats when crossing over:
- validate.py stays authoritative for skills in this repo: its description-trigger rule is
  stricter than skill-creator's own conventions (skill-creator's own description would fail it).
- Grading disciplines (fresh grader, blind the arm, mechanize first) live in the skill-bench
  plugin's empirical-evals.md, "Running the benchmark" section.
