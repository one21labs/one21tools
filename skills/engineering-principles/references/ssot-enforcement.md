# SSoT Enforcement

Reference, don't duplicate.

## Table of Contents

1. [Core Principle](#core-principle)
2. [Violation Indicators](#violation-indicators)
3. [Common SSoT Violations by Domain](#common-ssot-violations-by-domain)
4. [Audit Process](#audit-process)
5. [SSoT Registry](#ssot-registry)
6. [Edge Cases](#edge-cases)
7. [Verification Questions](#verification-questions)

## Core Principle

**Time pressure is not an exemption.** If a fix requires pasting the same value into N files, put it in one place and have all N reference it — one constant plus N imports is not slower than N literals, so declining it is not "cleverness." Defer only genuinely separate scope bundled into the same request (retry logic, logging, refactors); never defer the single-definition step itself.

## Violation Indicators

| Symptom | Likely SSoT Violation |
|---------|----------------------|
| "Which one is correct?" | Same fact in multiple places |
| "I updated it but it's still wrong" | Duplicate not updated |
| Config values scattered in code | No canonical config location |
| Copy-paste between files | Reference not established |
| Conflicting documentation | No canonical doc |
| "It depends on which file you look at" | Multiple sources, no authority |
| Recurring appeal to an unstated premise across issues/PRs | Fact MISSING, not duplicated — write it once at its lowest-altitude home instead of re-deriving it ad hoc |

## Common SSoT Violations by Domain

### Code

| Violation | Example | Fix |
|-----------|---------|-----|
| Magic numbers repeated | `timeout = 30` in multiple files | Constants file, single definition |
| URLs hardcoded | API endpoint in multiple places | Config/environment variable |
| Business rules duplicated | Validation logic in frontend AND backend | Shared module or backend authority |
| Types redefined | Same interface in multiple files | Single type definition, import |
| Error messages scattered | Same error text in multiple places | Error constants/catalog |

### Configuration

| Violation | Example | Fix |
|-----------|---------|-----|
| Environment values in code | `if (env === 'prod')` scattered | Single config source |
| Secrets in multiple places | API key in code AND .env AND CI | Single secret manager |
| Feature flags duplicated | Flag checked inconsistently | Single flag service/config |
| Build config scattered | Same setting in multiple configs | Single source, derive others |

### Documentation

| Violation | Example | Fix |
|-----------|---------|-----|
| Same info in README and wiki | Setup instructions in both | One location, link from other |
| Process in multiple docs | Onboarding in 3 different places | Single canonical doc |
| API docs vs code comments | Both describe same thing | Code is SSoT, generate docs |
| Architecture described twice | Design doc AND wiki page | One location, deprecate other |
| Constraint in CLAUDE.md and source header | Same fact in two always/JIT locations | See `jit-documentation.md` for placement rules |
| Backstory narrated in docs | "Learned" changelog, retired/renumbered-ID notes, how-it-got-here prose | git history is the SSoT for backstory — state current truth, delete the story outright; never relocate or condense it into any other document (ADRs, comments, a CHANGELOG, a wiki page, a new "history" file) |
| Expiring status prose | "advisory today", "when wired", "until X ships" | Status lives in the artifact/config; docs point at it |
| Cross-reference restates what it points to | "see X" followed by X's content re-told | A cross-reference carries the ID/path only — zero restated content |

### Data

| Violation | Example | Fix |
|-----------|---------|-----|
| User name in multiple tables | Denormalized without sync | Single source, join or sync |
| Cache without invalidation | Stale data served | Clear invalidation strategy |
| Derived data stored | Calculated value persisted | Calculate on read, or clear sync |

## Audit Process

### Step 1: Identify Candidates

Look for these patterns:
- Constants (URLs, timeouts, limits, magic numbers)
- Configuration values
- Type/interface definitions
- Business rules and validation
- Error messages
- Documentation topics

### Step 2: Search for Duplicates

For each candidate:
1. Search codebase for the value/concept
2. Count occurrences
3. Check if they're references to canonical source or duplicates

**Search patterns:**
```
# URLs and endpoints
grep -r "api.example.com" --include="*.{js,ts,py,json,yaml}"

# Configuration constants
grep -rE "(MAX_|MIN_|DEFAULT_|TIMEOUT_)" --include="*.{js,ts,py}"

# Magic numbers with context
grep -rE "(port|PORT)\s*[=:]\s*\d+" --include="*.{js,ts,py,yaml}"
```

### Step 3: Establish Canonical Location

For each duplicate found:

| Type | Canonical Location |
|------|-------------------|
| Environment config | `.env` or config service |
| Application constants | `constants.{ext}` or `config.{ext}` |
| Type definitions | `types.{ext}` or `models.{ext}` |
| Business rules | Domain module |
| API contracts | OpenAPI spec or schema file |
| Error messages | Error catalog |
| Documentation topics | One file per topic, clear hierarchy |

### Step 4: Refactor to Reference

1. Create canonical source if not exists
2. Replace duplicates with imports/references
3. Add comment at canonical source indicating it's SSoT
4. Update any documentation pointing to old locations

### Step 5: Prevent Future Violations

- Search before stating: before writing a fact anywhere, search for its existing home — reference it if found; a duplicate starts as an innocent write
- Linting rules for hardcoded values
- PR review checklist item
- Documentation standards
- Onboarding training

## SSoT Registry

For larger systems, maintain a registry:

```markdown
## SSoT Registry

| Fact | Canonical Location | Consumers |
|------|-------------------|-----------|
| API base URL | `config/api.ts` | All API calls |
| User permissions | `auth/permissions.ts` | Frontend, backend |
| Error codes | `errors/catalog.ts` | All error handling |
| Feature flags | LaunchDarkly | All feature checks |
| DB schema | `prisma/schema.prisma` | All data access |
```

## Edge Cases

### Intentional Duplication

Sometimes duplication is correct (runtime only — never a doc copy of a code value kept in sync):
- **Caching** - Duplicate for performance, with clear invalidation
- **Denormalization** - Duplicate for query performance, with sync mechanism
- **Redundancy** - Duplicate for fault tolerance

For intentional duplication:
1. Document that it's intentional
2. Identify the authoritative source
3. Define sync/invalidation mechanism
4. Monitor for drift

### Cross-System SSoT

When fact spans multiple systems:
1. Designate one system as authority
2. Other systems sync from authority
3. Never update non-authoritative copies directly
4. Monitor sync health

## Verification Questions

For any piece of information, ask:
1. Where is the canonical source?
2. Is this a reference or a duplicate?
3. If I update the canonical source, will this update?
4. What happens if these diverge?

If you can't answer these clearly → SSoT violation likely.
