# Engineering Principles

## Table of Contents

[Foundations](#foundations) | [Key Quotes](#key-quotes) | [Seven Wastes](#seven-wastes-software) | [Quality](#quality-principles) | [5 Whys](#root-cause-analysis-5-whys) | [Design First](#design-first-implementation-second) | [Process](#process-principles) | [Pareto](#pareto-application-guide) | [5S](#5s-applied-to-software) | [Docs for AI](#documentation-for-ai-consumption) | [Application Hierarchy](#application-hierarchy) | [References](#references)

Manufacturing engineering principles for all work - software, documentation, processes, and physical workspaces. They synthesize Lean and Agile foundations for modern software development and engineering workflows.

## Foundations

| Principle | Origin | Core Insight |
|-----------|--------|--------------|
| **PDSA** | Shewhart/Deming | Plan → Do (experiment) → Study (understand why) → Act (adjust/adopt/abandon) |
| **5S** | TPS (Ohno) | Sort (Seiri), Set in Order (Seiton), Shine (Seiso), Standardize (Seiketsu), Sustain (Shitsuke) |
| **Pareto** | Pareto/Juran | Vital few vs useful many. Focus effort on 20% that produces 80% of results. |
| **SRP** | Robert C. Martin | Each unit responsible to one actor. One reason to change. |
| **SSoT** | DRY principle | Single Source of Truth. Each fact has one canonical location. |
| **Lean** | Ohno/Poppendieck | Eliminate waste (muda). Every action must add value. |
| **MVP** | Blank/Ries | Build smallest increment that validates assumptions. |
| **Value Prop** | Osterwalder | Does this relieve a real pain? If not, don't build it. |
| **Kaizen** | TPS | Continuous small improvements. Learn from every cycle. |
| **Design First** | Engineering | Design before implementation. Outline before draft. Spec before build. |
| **Jidoka** | TPS | Automation with human judgment. Stop and fix problems immediately. |
| **5 Whys** | Sakichi Toyoda/TPS | Ask "Why?" iteratively to find root cause, not symptoms. |
| **A3** | Toyota | One-page constraint forces clarity and prioritization. |
| **Taguchi/DOE** | Taguchi | Maximize learning with minimum experiments. |

## Key Quotes

> "94% of problems are management's responsibility (system), not worker's." — W. Edwards Deming

> "A module should be responsible to one, and only one, actor." — Robert C. Martin

> "Gather together the things that change for the same reasons. Separate those things that change for different reasons." — Robert C. Martin

> "Study the results to understand the system better. Compare with your prediction...learn from the difference." — W. Edwards Deming

## Seven Wastes (Software)

| Waste | Manufacturing | Software | Mitigation |
|-------|--------------|----------|------------|
| Overproduction | Excess inventory | Extra features (YAGNI) | Build only what's needed |
| Waiting | Idle time | Delays for approvals, builds | Fast CI/CD, async reviews |
| Transportation | Moving materials | Handoffs between teams | Cross-functional teams |
| Overprocessing | Excess refinement | Unnecessary complexity | Keep it simple |
| Inventory | WIP stockpiles | Partially done work, branches | WIP limits, complete before starting new |
| Motion | Worker movement | Task switching | Focus, single responsibility |
| Defects | Rework | Bugs | Test-first, catch early |

## Quality Principles

| Principle | Application |
|-----------|-------------|
| **Build quality in** | Tests, linting, type checking at source - don't inspect it in later |
| **Common vs special cause** | Recurring issues → fix system; One-offs → investigate root cause |
| **DMAIC** | Define → Measure → Analyze → Improve → Control (for major projects) |
| **Taguchi/DOE** | Orthogonal arrays reduce test explosion while maintaining coverage |
| **Poka-yoke** | Error-proofing. Make the error impossible by design (delete the mirror, derive don't duplicate, compute don't assert) over merely detecting it; detection (a guard/test) is the fallback when prevention can't be designed in. Validate at source. |

## Root Cause Analysis (5 Whys)

**When to apply**: CRITICAL issues, recurring problems, systemic patterns.

**When NOT to apply**: Minor issues, obvious typos, first-time occurrences.

**Key insight**: If the fix only addresses the immediate cause, the problem will recur. Effective fixes target root causes.

## Design First, Implementation Second

Foundational workflow: get design right before implementing. Rework is waste.

| Domain | Design (Parent) | Implementation (Child) |
|--------|-----------------|------------------------|
| Software | Architecture, pseudocode, diagrams | Code |
| Writing | Outline, structure | Draft, prose |
| Product | Spec, wireframes | Build |
| Planning | Design artifacts for approval | Execution |

**Why design first:**
- Fixing design is cheap; fixing implementation is expensive
- Implementation follows from design (parent-child); prevents rework
- "Plan" in PDSA means design, not jump to "Do"

**In documentation:** docs show design intent (pseudocode, diagrams); code shows implementation. Code is SSoT for "how"; design docs are SSoT for "what/why".

**Anti-pattern:** Implement first, fix later - causes rework, wasted effort, and in AI contexts, token waste.

## Process Principles

| Principle | Application |
|-----------|-------------|
| **100% review** | Every character in code and docs is intentional. Review all changes. |
| **Batch editing** | Plan all changes, combine into single operations, re-read between edits |
| **Ask when uncertain** | If unclear where something belongs, ask rather than guess |
| **A3 presentation** | Constrain to one page; forces prioritization |
| **Drive out fear** | Blameless retrospectives, safe-to-fail experiments |

## Pareto Application Guide

**Where Pareto applies:**
- Testing prioritization (focus more tests on high-risk modules)
- Feature prioritization (which 20% delivers 80% of value)
- Bug triage (fix high-impact bugs first)
- Time/effort allocation (spend time on vital few activities)

**Where Pareto does NOT apply:**
- Code review → 100% of changes reviewed
- Documentation review → 100% of content reviewed
- SSoT enforcement → Every duplicate is a violation

## 5S Applied to Software

| S | Japanese | Physical | Code | Documentation |
|---|----------|----------|------|---------------|
| 1 | Seiri (Sort) | Remove unused tools | Delete dead code, unused imports | Remove obsolete docs |
| 2 | Seiton (Set in Order) | Place for everything | Consistent file structure, naming | SSoT - one home per topic |
| 3 | Seiso (Shine) | Clean workspace daily | Regular refactoring, code review | Keep docs current |
| 4 | Seiketsu (Standardize) | Standard procedures | Linting, coding standards | Doc templates, formats |
| 5 | Shitsuke (Sustain) | Maintain discipline | CI/CD enforcement, audits | Regular review cycles |

## Documentation for AI Consumption

LLM context windows impose constraints analogous to A3's one-page limit. Context engineering applies TPS principles to AI-consumed documentation.

### Context Windows as Physical Constraints

| Constraint | A3 (Physical) | LLM Context (Virtual) |
|------------|---------------|-----------------------|
| **Physical limit** | One printed page | Context window (tokens) |
| **Resource** | Paper space | Token budget |
| **Consumer** | Human reader | AI + Human |
| **Forcing function** | Forces prioritization | Forces precision |
| **Result** | Clarity through constraint | Efficiency through constraint |

### Context Engineering Principles (Anthropic)

| Context Principle | TPS/Lean Mapping | Application |
|-------------------|------------------|-------------|
| **Context quality determines output** | Build quality in (Deming) | Quality at source - write clear context, don't fix output |
| **Structure matters** | 5S/Seiton (Set in Order) | Consistent file structure, clear hierarchy, predictable locations |
| **Frontload critical info** | A3 (one-page constraint) | Most important facts first - LLMs can lose track in long contexts |
| **Be explicit, not implicit** | Poka-yoke (error-proofing) | State requirements directly - prevent LLM from guessing wrong |
| **Show examples** | Genchi Genbutsu (go and see) | Demonstrate desired output - examples > descriptions |
| **Context windows are scarce** | Lean (eliminate waste) | Every token must add value - no redundancy |
| **Avoid contradictions** | SSoT (Single Source of Truth) | One canonical fact per topic - contradictions degrade output |
| **Human + AI judgment** | Jidoka (automation with human touch) | AI accelerates, human validates |

### AI vs Human Consumption

| Aspect | Human Reader | AI Consumer |
|--------|--------------|-------------|
| **Needs** | Narrative flow, whitespace, examples | Dense structure, explicit rules, SSoT |
| **Tolerance** | Handles ambiguity well | Requires explicit instruction |
| **Processing** | Can skip/skim sections | Processes sequentially, can't skip effectively |
| **Memory** | Remembers context across sessions | No memory between sessions |
| **Cost** | Time (human labor) | Tokens (computational resource) |

### CLAUDE.md Files: AI-First, Human-Maintainable

CLAUDE.md loads into the system prompt. Primary consumer: AI; secondary: humans maintaining it.

**For AI (optimize first):**
- Frontload critical facts (constraints, principles, conventions)
- Explicit rules ("Do X" not "Consider X")
- SSoT - reference canonical sources, no contradictions
- Token efficient - tables for dense info, no redundancy
- Structured sections; examples demonstrating desired behavior

**For humans (maintainability):**
- Clear headers, predictable structure (know where to add info)
- Version control friendly (meaningful diffs), understandable for validation

**Exclude:** Narrative about why CLAUDE.md exists, tutorials, marketing language.

### Token Efficiency (Lean for LLMs)

| Waste Type | Documentation Waste | Mitigation |
|------------|---------------------|------------|
| **Overproduction** | Verbose explanations, redundant sections | Write precisely - every token has purpose |
| **Overprocessing** | Flowery language, unnecessary adjectives | Direct, technical language |
| **Inventory** | Duplicate information in multiple places | SSoT - reference, don't duplicate |
| **Defects** | Contradictions, outdated info | 100% review - validate all statements |
| **Motion** | Poor organization, hard to find info | 5S/Seiton - predictable structure |

### Actionable Guidance

1. **Structure first**: Design hierarchy before writing content
2. **Frontload**: Critical facts in first 50 lines (high-value real estate)
3. **Reference > Duplicate**: Link to canonical sources
4. **Be explicit**: "Do X" not "Consider doing X"
5. **Examples over description**: Show desired output format
6. **Tables for density**: Lower token cost than prose for structured info
7. **Version control**: Context files are code - review with same rigor
8. **Measure usage**: Track token consumption, optimize high-cost sections

## Application Hierarchy

1. **Code**: Functions do one thing. Modules have one reason to change.
2. **Documentation**: Each file serves one reader journey. SSoT enforced.
3. **Testing**: Taguchi-efficient design. Automated where possible.
4. **Review**: 100% coverage. A3-structured findings. Iterative discussion.
5. **Process**: PDSA cycles for learning. Kaizen for improvement.

## References

- Shewhart, W.A. (1939). *Statistical Method from the Viewpoint of Quality Control*
- Deming, W.E. (1986). *Out of the Crisis*
- Ohno, T. (1988). *Toyota Production System: Beyond Large-Scale Production*
- Poppendieck, M. & T. (2003). *Lean Software Development: An Agile Toolkit*
- Martin, R.C. (2003). *Agile Software Development, Principles, Patterns, and Practices*
- Blank, S. & Dorf, B. (2012). *The Startup Owner's Manual*
- Osterwalder, A. et al. (2014). *Value Proposition Design*
- Ries, E. (2011). *The Lean Startup*
- DORA (2025). *State of AI-assisted Software Development* — dora.dev
