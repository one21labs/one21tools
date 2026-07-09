---
name: engineering-principles
description: Apply when designing architecture, performing root cause analysis, eliminating waste, auditing for duplication, reviewing designs before implementation, or when quality/process questions arise, reference for TPS/Lean foundations. Foundational engineering principles for structured work - software, documentation, processes, planning. 
---

# Engineering Principles

Foundational meta-skill: TPS/Lean principles adapted for modern engineering. Provides the "why" behind other skills' "how."

## Quick Decision Guide

| Situation | Action | Reference |
|-----------|--------|-----------|
| Starting new work, or told a plan is "already approved" | Design first — approval isn't completeness; check the checklist anyway | `references/design-review.md` |
| Problem keeps recurring | Root cause analysis | `references/root-cause-analysis.md` |
| Process feels slow/bloated | Waste identification | `references/waste-identification.md` |
| Duplicate definitions suspected, or asked to hardcode one value into several files | SSoT audit — one definition, even under time pressure | `references/ssot-enforcement.md` |
| Deciding where documentation belongs | JIT documentation | `references/jit-documentation.md` |
| Need quotes, citations, deep theory | Full reference | `references/ENGINEERING_PRINCIPLES.md` |

## Core Decision Heuristics

| Principle | Question to Ask |
|-----------|-----------------|
| **Design First** | Can I outline/sketch this before building? |
| **SRP** | Does this serve exactly one actor? One reason to change? |
| **SSoT** | Is this fact stated in exactly one place? |
| **Pareto** | Am I focusing on the vital few (20%), not trivial many? |
| **Lean** | Does this action add value? If not, it's waste. |
| **Jidoka** | Should I stop and fix this now, or will it compound? |
| **PDSA** | Did I predict the outcome? Am I comparing results to prediction? |

## When to Read References

**`references/root-cause-analysis.md`** — Read when:
- A problem has recurred more than once
- Fix didn't work and you need to dig deeper
- Facilitating a team through problem-solving

**`references/waste-identification.md`** — Read when:
- Process review or retrospective
- Something feels inefficient but unclear why
- Applying Lean thinking to a specific domain

**`references/design-review.md`** — Read when:
- Starting a new feature, document, or process
- Unsure if design is complete before implementation
- Reviewing someone else's design
- Told a plan is already approved and to skip straight to a task breakdown

**`references/ssot-enforcement.md`** — Read when:
- Contradictions appearing in system
- Config/constants scattered across codebase or documents
- Establishing canonical locations for a new project
- Asked to paste/hardcode the same literal into multiple files, even under a "fastest path" deadline

**`references/jit-documentation.md`** — Read when:
- Deciding whether a constraint belongs in CLAUDE.md or a source file header
- Writing or reviewing source file headers
- CLAUDE.md is growing and needs triage

**`references/ENGINEERING_PRINCIPLES.md`** — Read when:
- Need to cite sources (Deming, Ohno, Martin)
- Explaining principles to stakeholders
- Deep dive on a specific principle's origin

## Lean Applicability by Domain

| Work Type | TPS Fit | Why |
|-----------|---------|-----|
| Manufacturing | Direct | Designed for this |
| Traditional software | Selective | Discovery work — Kanban, waste ID, and SSoT translate; cycle-time/defect-rate targets don't |
| AI-assisted workflows | Direct | Stochastic outputs need variation reduction: poka-yoke via output schemas, standardized work via skills/CLAUDE.md, Jidoka via evals that flag out-of-spec output, SPC via temperature/seed pinning |

## Cross-References

| Need | Skill |
|------|-------|
| Context engineering, CLAUDE.md, prompts | `optimizing-context` |
| Building skills | `building-skills` |
| Design First operationalized (Pre-Code Checklist) | `code-standards` |

## Foundational Role

This skill provides methodology that other skills apply. optimizing-context, building-skills, and domain-specific skills reference these principles for architectural decisions. For AI-assisted workflows specifically, see Lean Applicability by Domain above — TPS variation reduction applies more directly to stochastic LLM systems than to traditional software.
