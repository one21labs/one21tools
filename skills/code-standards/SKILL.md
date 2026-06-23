---
name: code-standards
description: Invoke when writing, reviewing, or auditing code for quality, style, readability, or correctness. Apply these standards before presenting any code. Check header comments, naming, error handling, and structure.
---

# Code Standards

## Principles

| Principle | Application |
|-----------|-------------|
| **Clear over clever** | Readable code prevents bugs. If it needs explanation to understand, rewrite it. |
| **SRP** | Functions do one thing. Modules have one reason to change. |
| **Quality built in** | Validate at boundaries. Catch errors at source, not downstream. |
| **SSoT** | Each fact exists in exactly one place. No duplicated logic or constants. |
| **Lean** | Only add what is needed. Every line must earn its place. Remove dead code immediately. |
| **Design first** | Understand the problem before writing code. Know what a function owns before implementing it. |
| **Poka-yoke** | Error-proof at boundaries. Validate external inputs at entry points, not deep in call chains. |

## File Headers

Apply two tests before including anything in a file header:

**SSoT**: Does this information already exist somewhere the reader can find it? Identifiers name what the code does. The code shows how. The header is the SSoT for architectural role, constraints, and design decisions — not a duplicate of either.

**Altitude**: Is this at the right level of abstraction? Headers belong at architectural altitude — role, constraints, non-obvious patterns. Implementation detail is the wrong altitude for a header; it belongs in the code or inline comments.

What passes both tests:
- What this module owns and explicitly does NOT own
- Constraints that must be preserved (e.g., "no I/O", "thread-safe", "stateless after init")
- Non-obvious usage contract or initialization sequence
- Navigation to related files (SEE ALSO)

What fails and should be excluded:
- What the code does — identifiers already say that (SSoT violation)
- Function lists, line counts — go stale, discoverable elsewhere (SSoT violation)
- Implementation details — wrong altitude

### Examples

**C — pure state machine:**

```c
/*
 * state.c - Backlight state machine
 *
 * ARCHITECTURE ROLE:
 *   Business logic only. Isolated from all I/O to enable unit testing
 *   without mocks.
 *
 * DESIGN CONSTRAINTS:
 *   - No I/O: no file access, no time calls, no system calls
 *   - Pure functions: all state passed as parameters; no globals written
 *   - Caller owns time: timestamps provided by caller, not read internally
 *
 * TESTING STRATEGY:
 *   No mocking needed — pass mock timestamps directly to functions.
 *
 * SEE ALSO:
 *   state.h - public API and preconditions
 */
```

**JavaScript — interchange module:**

```js
/*
 * csv.js - CSV import and export
 *
 * ARCHITECTURE ROLE:
 *   Interchange layer only. Delegates all persistence to storage.js.
 *
 * DESIGN CONSTRAINTS:
 *   - Feature gate enforced by caller before invoking; not re-checked here.
 *   - Both functions async: parser loaded on demand so all users don't pay
 *     the bundle cost. Callers must await.
 *   - Rows with invalid or missing required fields are silently skipped.
 *
 * KEY PATTERNS:
 *   merge=true (default): existing records overwritten on import.
 *   merge=false: existing records skipped — "add new only" mode.
 *
 * SEE ALSO:
 *   storage.js - persistence primitives
 */
```

**Bash scripts** use `#` comments with the same sections: PURPOSE, ARGUMENTS, WORKFLOW (numbered steps), EXIT CODES, SEE ALSO.

## Code Comments

Apply the same SSoT and altitude tests to inline comments.

**SSoT**: Does the code already say this? If a comment restates what the identifiers and logic make obvious, it is a duplicate — a SSoT violation that will go stale.

**Altitude**: Is this above the code's level of abstraction? A comment earns its place when it carries information the code cannot express: a constraint, an invariant, a deliberate trade-off, or a precondition the caller must satisfy.

Comment when:
- A non-obvious invariant must be preserved
- A constraint exists that the reader would otherwise break
- A deliberate trade-off or unconventional choice was made
- Preconditions on a function are not obvious from the signature

Do not comment:
- What the next line does — the code says that (SSoT violation)
- Implementation detail at the same altitude as the code itself

## Naming

- Descriptive over brief: `userSessionTimeoutMs` / `user_session_timeout_ms` over `t`
- Module or domain prefix for public APIs — casing follows language conventions (`config_parse` in C/Python, `configParse` in JS/TS)
- Consistent conventions within a codebase — pick one and enforce it
- Avoid abbreviations unless universally understood (`id`, `url`, `err`)
- Booleans read as assertions: `isValid` / `is_valid`, `hasPermission` / `has_permission`

## Error Handling

- Handle all error cases — never silently discard a failure
- Update state only on success; a failed operation must leave state unchanged
- Log failures with context: what failed, what the inputs were, what error was returned
- Validate external inputs (user data, API responses, file contents) at the boundary; trust validated data inside the system

## Logging

- Use structured log levels: `INFO`, `WARN`, `ERROR`, `DEBUG`
- Every error log includes enough context to diagnose without a debugger
- `DEBUG` logs must be suppressible in production
- Log decisions and state transitions at `INFO`; log unexpected conditions at `WARN` or `ERROR`
- Structured format for multi-module or distributed systems: `{timestamp (ISO 8601), level, correlation_id, message, context}` — correlation IDs enable tracing across module and service boundaries
- Prefer warn-and-recover over crash for recoverable conditions; crash is appropriate only for unrecoverable initialization failure

## Pre-Code Checklist

Before writing a function:
- [ ] What is its single responsibility?
- [ ] What does the caller guarantee (preconditions)?
- [ ] What are the error cases and how are they communicated?
- [ ] Does this belong here or in a different module?

Before submitting:
- [ ] File header describes role and constraints, not implementation
- [ ] All error cases are handled; no silent failures
- [ ] State updated only on success
- [ ] Named constants for all magic values
- [ ] Comments explain WHY, not WHAT
- [ ] Dead code removed (no commented-out blocks)
