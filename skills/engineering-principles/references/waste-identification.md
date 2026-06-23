# Waste Identification

Framework for identifying and eliminating non-value-adding activities.

## Core Principle

**Every action must add value.** If it doesn't add value from the customer/user perspective, it's waste (muda). Eliminate it.

## Seven Wastes by Domain

### Software Development

| Waste | Manifestation | Questions to Ask | Mitigation |
|-------|---------------|------------------|------------|
| **Overproduction** | Features no one uses, YAGNI violations, speculative generalization | Is this needed *right now*? Who requested this? | Build only what's validated |
| **Waiting** | Blocked on review, slow CI/CD, waiting for decisions, environment access | Where are the queues? What's the cycle time? | Async reviews, fast pipelines, decision rights |
| **Transportation** | Handoffs between teams, ticket shuffling, information relay chains | How many handoffs? Who touches this? | Cross-functional teams, reduce handoffs |
| **Overprocessing** | Unnecessary abstraction, premature optimization, gold-plating | Is this complexity necessary? What's simplest solution? | YAGNI, simplicity, defer optimization |
| **Inventory** | Large backlogs, many open PRs, unmerged branches, unreleased code | How much WIP? What's oldest unfinished item? | WIP limits, finish before starting |
| **Motion** | Context switching, searching for information, poor tooling | How often do people switch tasks? Is info findable? | Focus time, documentation, better tools |
| **Defects** | Bugs, rework, unclear requirements causing wrong implementation | Where do errors enter? What's rework rate? | Shift left, test-first, clear specs |

### Documentation

| Waste | Manifestation | Questions to Ask | Mitigation |
|-------|---------------|------------------|------------|
| **Overproduction** | Docs no one reads, excessive detail, documenting the obvious | Who will read this? Is this already known? | Write for specific reader journey |
| **Waiting** | Blocked on SME review, approval queues | Who's blocking? Can they async review? | Clear ownership, async process |
| **Transportation** | Info scattered across systems, copy-paste between docs | Where does this live canonically? | SSoT enforcement |
| **Overprocessing** | Flowery language, unnecessary formatting, over-designed templates | Is this adding clarity or noise? | Direct technical language |
| **Inventory** | Outdated docs, draft pile, "we should document this" list | When was this last updated? Is it accurate? | Regular review cycles, delete stale |
| **Motion** | Searching for docs, unclear where things live | Can people find this? Is structure predictable? | 5S organization, clear hierarchy |
| **Defects** | Contradictions, outdated info, wrong instructions | Does this match reality? Any conflicts? | 100% review, SSoT |

### Process/Workflow

| Waste | Manifestation | Questions to Ask | Mitigation |
|-------|---------------|------------------|------------|
| **Overproduction** | Reports no one uses, meetings without outcomes, excessive status updates | Who consumes this output? What decision does it inform? | Output-driven, cut unused |
| **Waiting** | Approval bottlenecks, sequential when could be parallel | What's blocking flow? Can this be async? | Parallel paths, delegation |
| **Transportation** | Excessive handoffs, information passing through intermediaries | How many people touch this? Why? | Direct communication, fewer handoffs |
| **Overprocessing** | Unnecessary steps, redundant approvals, ceremony without value | What would happen if we skipped this? | Eliminate, simplify |
| **Inventory** | Backlog of requests, queued work, "someday" lists | How old is oldest item? Is this actually happening? | WIP limits, say no, clear queues |
| **Motion** | Meetings that could be async, travel for things that could be remote | Does this require synchronous/in-person? | Async default, purposeful sync |
| **Defects** | Rework from miscommunication, errors from unclear process | Where do mistakes happen? Why? | Clear process, error-proofing |

### Context/Prompts (AI-specific)

| Waste | Manifestation | Questions to Ask | Mitigation |
|-------|---------------|------------------|------------|
| **Overproduction** | Verbose prompts, including unused context, over-explaining | Does Claude need this? Is this already known? | Minimal high-signal tokens |
| **Waiting** | Long inference times from bloated context | Can this be shorter? | Compress, progressive disclosure |
| **Transportation** | Same info in multiple places in context | Is this duplicated? Where's canonical? | SSoT in context |
| **Overprocessing** | Elaborate formatting for AI that doesn't need it | Is this structure adding value? | Dense, explicit, minimal |
| **Inventory** | Stale context, outdated instructions still present | Is this current? Does this still apply? | Regular context review |
| **Motion** | Claude searching through disorganized context | Is structure predictable? | 5S organization |
| **Defects** | Contradictions in context causing wrong outputs | Any conflicts? Is there one truth? | 100% review, SSoT |

## Audit Process

### Quick Scan (5 minutes)
For each waste type, rate 0-3:
- 0 = Not present
- 1 = Minor
- 2 = Moderate
- 3 = Severe

Focus improvement on highest-rated wastes.

### Deep Audit (30-60 minutes)

1. **Map the value stream** - What are all the steps from request to delivery?
2. **Identify value-add vs non-value-add** - Which steps does the customer care about?
3. **Categorize waste** - Which of the seven wastes is each non-value-add step?
4. **Prioritize** - Which waste has highest impact if eliminated?
5. **Countermeasure** - What specific change eliminates or reduces this waste?

### Value Stream Questions

For each step in a process:
1. Does this step transform the work toward completion?
2. Would the customer pay for this step?
3. Is this step done right the first time?

If no to all three → pure waste, eliminate.
If no to first two but yes to third → necessary waste, minimize.

## Common Patterns

| Pattern | Likely Wastes | First Action |
|---------|---------------|--------------|
| "It takes forever to ship" | Waiting, Inventory | Map cycle time, find queues |
| "We keep rebuilding things" | Defects, Overprocessing | Root cause on rework |
| "No one can find anything" | Motion, Transportation | 5S organization |
| "We're always busy but nothing ships" | Inventory, Motion | WIP limits |
| "Requirements keep changing" | Defects, Overproduction | Smaller batches, faster feedback |

## Ohno's Insight

> "The most dangerous kind of waste is the waste we do not recognize."

Waste becomes invisible when it's "how we've always done it." Question every step.
