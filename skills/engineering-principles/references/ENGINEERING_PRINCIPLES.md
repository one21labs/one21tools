# Engineering Principles

## Table of Contents

[Foundations](#foundations) | [Key Quotes](#key-quotes) | [Seven Wastes](#seven-wastes-software) | [Quality](#quality-principles) | [5 Whys](#root-cause-analysis-5-whys) | [Design First](#design-first-implementation-second) | [Process](#process-principles) | [Pareto](#pareto-application-guide) | [5S](#5s-applied-to-software) | [Lean by Domain](#lean-applicability-by-domain) | [Docs for AI](#documentation-for-ai-consumption) | [Application Hierarchy](#application-hierarchy) | [References](#references)

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

> "Every piece of knowledge must have a single, unambiguous, authoritative representation within a system." — Andy Hunt & Dave Thomas (DRY)

## Seven Wastes (Software)

Manufacturing-origin mapping and per-domain breakdown: [waste-identification.md](waste-identification.md).

## Quality Principles

| Principle | Application |
|-----------|-------------|
| **Build quality in** | Tests, linting, type checking at source - don't inspect it in later |
| **Common vs special cause** | Recurring issues → fix system; One-offs → investigate root cause |
| **DMAIC** | Define → Measure → Analyze → Improve → Control (for major projects) |
| **Taguchi/DOE** | Orthogonal arrays reduce test explosion while maintaining coverage |
| **Poka-yoke** | Error-proofing. Make the error impossible by design (delete the mirror, derive don't duplicate, compute don't assert) over merely detecting it; detection (a guard/test) is the fallback when prevention can't be designed in. Validate at source. Rank the enforcement surface on the detection-latency ladder below. |

### Detection-Latency Ladder (Poka-yoke, Ranked)

Enforcement surfaces ranked by how early they catch a defect — earlier is stronger:

| Rung | Stage | Surface |
|------|-------|---------|
| 1 | Prevent | Blocking pre-action check (e.g. a deny hook) — the error cannot happen |
| 2 | Detect at creation | Post-edit check, immediately after the change is made |
| 3 | Detect at commit | Pre-commit check |
| 4 | Detect at PR | CI gate |
| 5 | Prose / human review | Guidance and reviewer judgment — the fallback, never the home for a decidable rule |

**Executable-home rule.** A machine-decidable requirement is never homed in prose where an executable surface exists — a tool-call moment at which a check can fire. Prose holds judgment calls, and serves only as an interim home until a surface is available.

- **Choosing the rung**: default to the cheapest rung that catches the defect; promoting a rule to an earlier rung requires scar tissue (a cited recurring miss) plus favorable economics — earlier rungs cost more to build and keep honest.
- **Full coverage deletes the mirror**: once a mechanism fully enforces a rule, its prose restatement is waste — cut it (a later-rung backstop such as CI may remain).
- **Faithful predicate**: the mechanism must test the rule it claims to enforce; a partial predicate ships with its residue recorded.
- **Undecidable intent warns, never denies**: when a check cannot separate violation from legitimate use, it warns — false blocks train users to bypass the guard.

### Process-Level Poka-yoke (Guard the Process, Not Just the Product)

Doctrine (owner, 18-Jul-2026): **prevention outranks detection, as a ladder — and the guards
apply to the process itself, not just the product.**

- **Gates on gates**: no gating script ships without a decision-logic test; exit codes must
  not be maskable (the pipe guard denies piped gate invocations, rung 1).
- **The knowledge base is guarded like code**: decision records are linted (char budgets,
  amendment back-pointers, version-agnosticism); cross-file restatement of a fact fails CI;
  budgeted docs block over-cap edits at authoring time (rung 2), not review time.
- **Why**: a self-improving loop's characteristic failure is silent self-degradation — a stale
  hook enforcing retired policy, a gamed metric, an unsourced claim. Product guards never
  notice loop-drift; process guards make it loud.
- **Trust corollary**: metrics are gates, period — never optimization targets. A gameable
  metric invites optimizing the number instead of the work (a gamed line cap became a char
  cap), and gaming or misreporting is a catastrophic, possibly unrecoverable, trust failure.

## Root Cause Analysis (5 Whys)

When to apply, method, and stopping criteria: [root-cause-analysis.md](root-cause-analysis.md).
If a root cause reads "person X made a mistake," it is not the root cause — ask what about the
system allowed or encouraged that mistake.

## Design First, Implementation Second

Foundational workflow: fixing design is cheap; fixing implementation is expensive. The
parent-child relationship:

- Design (parent) → Implementation (child)
- Implementation follows from design
- If design is wrong, implementation will be wrong
- Rework is waste

Per-domain checklists and review process: [design-review.md](design-review.md).

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

## Lean Applicability by Domain

| Work Type | TPS Fit | Why |
|-----------|---------|-----|
| Manufacturing | Direct | Designed for this |
| Traditional software | Selective | Discovery work — Kanban, waste ID, and SSoT translate; cycle-time/defect-rate targets don't |
| AI-assisted workflows | Direct | Stochastic outputs need variation reduction: poka-yoke via output schemas, standardized work via skills/CLAUDE.md, Jidoka via evals that flag out-of-spec output, SPC via temperature/seed pinning |

## Documentation for AI Consumption

LLM context windows impose constraints analogous to A3's one-page limit. Context engineering applies TPS principles to AI-consumed documentation.

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

### CLAUDE.md Files and Token Efficiency

Applying the constraints above to CLAUDE.md authoring (constitution-not-manual philosophy, what to
include, token allocation) is optimizing-context territory, not duplicated here:
[claude-md.md](../../optimizing-context/references/claude-md.md). Token-efficiency waste mapping
(Overproduction, Overprocessing, Inventory, Defects, Motion for documentation and context/prompts):
[waste-identification.md](waste-identification.md).

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
- Hunt, A. & Thomas, D. (1999). *The Pragmatic Programmer*
- Poppendieck, M. & T. (2003). *Lean Software Development: An Agile Toolkit*
- Martin, R.C. (2003). *Agile Software Development, Principles, Patterns, and Practices*
- Blank, S. & Dorf, B. (2012). *The Startup Owner's Manual*
- Osterwalder, A. et al. (2014). *Value Proposition Design*
- Ries, E. (2011). *The Lean Startup*
- DORA (2025). *State of AI-assisted Software Development* — dora.dev
