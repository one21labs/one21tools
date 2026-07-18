# Root Cause Analysis

## When to Use

| Situation | Use RCA? |
|-----------|----------|
| Problem has recurred | **Yes** - pattern indicates systemic cause |
| Fix didn't work | **Yes** - addressed symptom, not cause |
| Critical system failure | **Yes** - prevent recurrence |
| First-time minor issue | **No** - fix and monitor |
| Obvious typo/mistake | **No** - just fix it |

## 5 Whys Method

Ask "Why?" iteratively until you reach a cause you can actually fix.

### Structure

```
Problem: [Observable symptom]
↓ Why?
Cause 1: [First-level cause]
↓ Why?
Cause 2: [Deeper cause]
↓ Why?
Cause 3: [Deeper still]
↓ Why?
Cause 4: [Getting to system level]
↓ Why?
Root Cause: [Actionable systemic issue]
→ Countermeasure: [Fix that prevents recurrence]
```

### Stopping Criteria

Stop when you reach a cause that is:
1. **Actionable** - you can actually change it
2. **Systemic** - fixing it prevents the class of problem, not just this instance
3. **Within control** - you have authority to address it

### Example: Bug in Production

```
Problem: Customer saw error page
↓ Why?
Null pointer exception in payment module
↓ Why?
User object was null when accessed
↓ Why?
Session expired but code assumed valid session
↓ Why?
No session validation before accessing user data
↓ Why?
Root Cause: No standard pattern for session handling across modules

Countermeasure: Create session validation middleware, 
               add to coding standards, retrofit existing endpoints
```

### Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Stopping at first cause | Addresses symptom | Keep asking "Why?" |
| Blaming people | "Because John made a mistake" | Ask why the system allowed the mistake |
| Accepting "human error" | Not actionable | What system change prevents this error? |
| Going too deep | Reaches causes outside control | Stop at actionable level |
| Single-threaded | Misses multiple contributing causes | Branch when multiple causes exist |
| Verification = "we'll monitor going forward" | Doesn't prove the fix works | State how you'll actively trigger the failure condition and confirm the safeguard catches it |

## Branching Analysis

When multiple causes contribute, branch the analysis:

```
Problem: Deployment failed
├─ Why? Config was wrong
│  └─ Why? Manual config step
│     └─ Root: No config automation
│        → Countermeasure: Automate config generation
│
└─ Why? No one caught it in review
   └─ Why? Reviewer didn't have checklist
      └─ Root: No deployment review checklist
         → Countermeasure: Create and enforce checklist
```

## Facilitation Guide

When leading a team through 5 Whys:

1. **State the problem factually** - observable behavior, not interpretation
2. **One question at a time** - don't skip levels
3. **Write it down** - visible to all participants
4. **Challenge "human error"** - always ask what system allowed it
5. **Seek multiple branches** - rarely one single cause
6. **End with countermeasure** - analysis without action is waste

## Output Template

```markdown
## Root Cause Analysis: [Problem Title]

**Date:** [Date]
**Participants:** [Names]

### Problem Statement
[Factual description of what happened]

### Analysis
1. Why? [Cause 1]
2. Why? [Cause 2]
3. Why? [Cause 3]
4. Why? [Cause 4]
5. Why? [Root Cause]

### Root Cause
[Summary of systemic issue]

### Countermeasure
[Specific action to prevent recurrence]

### Verification
[A concrete test that proves the fix works — inject the failure condition and confirm the safeguard fires (e.g., run the job against a query that returns zero rows and confirm the alert triggers). Not "we'll monitor going forward" and not a restatement of the countermeasure's intended properties.]
```