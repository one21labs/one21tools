# Design Review

Checklists to verify design completeness before implementation. Fixing design is cheap; fixing implementation is expensive.

## Core Principle

**Design before implementation.** Outline before draft. Architecture before code. Spec before build.

The parent-child relationship:
- Design (parent) → Implementation (child)
- Implementation follows from design
- If design is wrong, implementation will be wrong
- Rework is waste

## When to Use

| Situation | Use Design Review? |
|-----------|-------------------|
| Starting new feature/project | **Yes** - before any code |
| Significant change to existing system | **Yes** - before modifying |
| Writing substantial document | **Yes** - outline first |
| Quick bug fix | **No** - just fix it |
| Exploratory spike | **No** - spike is the design phase |

## Software Design Checklist

### Problem Definition
- [ ] Problem statement is clearly articulated
- [ ] Success criteria are defined and measurable
- [ ] Scope boundaries are explicit (what's NOT included)
- [ ] Stakeholders/actors are identified
- [ ] Constraints are documented (time, budget, technical)

### Architecture
- [ ] High-level components are identified
- [ ] Component responsibilities follow SRP (one reason to change)
- [ ] Data flow between components is mapped
- [ ] External dependencies are identified
- [ ] Integration points are defined
- [ ] Failure modes are considered

### Interface Design
- [ ] Public APIs/interfaces are specified
- [ ] Input/output contracts are defined
- [ ] Error handling strategy is documented
- [ ] Versioning approach is considered (if applicable)

### Data Design
- [ ] Data models/schemas are defined
- [ ] Data flow and transformations are mapped
- [ ] Storage requirements are identified
- [ ] SSoT for each data type is designated
- [ ] Migration strategy exists (if changing existing data)

### Quality Attributes
- [ ] Performance requirements are specified
- [ ] Security considerations are addressed
- [ ] Scalability approach is defined
- [ ] Testability is designed in
- [ ] Observability is planned (logging, metrics, tracing)

### Risk Assessment
- [ ] Technical risks are identified
- [ ] Unknowns are acknowledged
- [ ] Fallback approaches exist for high-risk items
- [ ] Dependencies on external factors are noted

## Documentation Design Checklist

### Audience
- [ ] Target reader is identified
- [ ] Reader's prior knowledge is understood
- [ ] Reader's goal/task is defined
- [ ] Success criteria for reader is clear

### Structure
- [ ] Outline/hierarchy is complete
- [ ] Each section has clear purpose
- [ ] Information flows logically (no forward references)
- [ ] SSoT is maintained (no duplication)
- [ ] Entry points are identified

### Content Planning
- [ ] Key concepts are listed
- [ ] Examples/illustrations are planned
- [ ] Cross-references are mapped
- [ ] What to exclude is defined

### Maintenance
- [ ] Update triggers are identified
- [ ] Ownership is assigned
- [ ] Review cadence is set

## Process Design Checklist

### Purpose
- [ ] Process goal is clearly defined
- [ ] Success metrics are measurable
- [ ] Scope/boundaries are explicit
- [ ] Triggers (when process starts) are defined
- [ ] Completion criteria (when process ends) are defined

### Flow
- [ ] Steps are sequenced logically
- [ ] Decision points are identified
- [ ] Handoffs are minimized
- [ ] Parallel paths are identified where possible
- [ ] Cycle time is estimated

### Roles
- [ ] Responsibilities are assigned
- [ ] Each step has clear ownership
- [ ] Escalation paths are defined
- [ ] No step has ambiguous ownership

### Waste Check
- [ ] No unnecessary waiting built in
- [ ] No overprocessing (gold plating)
- [ ] Minimal handoffs/transportation
- [ ] No inventory buildup points
- [ ] No redundant approvals

### Quality
- [ ] Validation/check points are included
- [ ] Error recovery is defined
- [ ] Feedback loops exist
- [ ] Improvement mechanism is planned

## Feature/Product Design Checklist

### Value Proposition
- [ ] User problem is validated (not assumed)
- [ ] Solution addresses actual pain point
- [ ] Value is measurable
- [ ] MVP scope is defined (smallest thing that validates)

### User Experience
- [ ] User journey is mapped
- [ ] Entry/exit points are clear
- [ ] Error states are designed
- [ ] Edge cases are considered

### Technical Feasibility
- [ ] Technical approach is validated
- [ ] Dependencies are identified
- [ ] Risks are assessed
- [ ] Effort estimate is reasonable

### Success Criteria
- [ ] Metrics are defined
- [ ] Measurement approach exists
- [ ] Rollback criteria are set
- [ ] Learning goals are explicit

## Review Process

### Self-Review
Before sharing design with others:
1. Walk through each checklist item
2. Mark incomplete items
3. Fill gaps or document as "intentionally deferred"
4. Identify highest-risk items

### Peer Review
When reviewing someone else's design:
1. Start with problem definition - is the problem clear?
2. Check SRP - does each component have one reason to change?
3. Look for missing error handling
4. Identify unstated assumptions
5. Ask "what could go wrong?"

### Go/No-Go Decision

**Ready to implement if:**
- All checklist items are addressed (completed or intentionally deferred)
- High-risk items have fallback plans
- Stakeholders have reviewed and approved
- No blocking unknowns remain

**Not ready if:**
- Problem statement is unclear
- Success criteria are undefined
- Critical risks are unmitigated
- Major unknowns are unresolved

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| "We'll figure it out as we go" | Rework, wasted effort | Design first, even briefly |
| "The code is the design" | No separation of concerns | Document design intent separately |
| "We don't have time for design" | You'll spend 3x on rework | Design is faster than rework |
| "It's obvious, no need to write it down" | Assumptions diverge | Write it down, verify alignment |
| Perfect design paralysis | Never ship | Timebox design, accept uncertainty |
