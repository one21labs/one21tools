---
name: engineering-principles
description: Apply when designing architecture, performing root cause analysis, eliminating waste, auditing for duplication, reviewing designs before implementation, or when quality/process questions arise, reference for TPS/Lean foundations. Foundational engineering principles for structured work - software, documentation, processes, planning. 
---

# Engineering Principles

Foundational meta-skill: TPS/Lean principles adapted for modern engineering. Provides the "why" behind other skills' "how."

## Quick Decision Guide

| Situation | Action | Reference |
|-----------|--------|-----------|
| Starting new work | Design first, then implement | `references/design-review.md` |
| Problem keeps recurring | Root cause analysis | `references/root-cause-analysis.md` |
| Process feels slow/bloated | Waste identification | `references/waste-identification.md` |
| Duplicate definitions suspected | SSoT audit | `references/ssot-enforcement.md` |
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

**`references/ssot-enforcement.md`** — Read when:
- Contradictions appearing in system
- Config/constants scattered across codebase or documents
- Establishing canonical locations for a new project

**`references/jit-documentation.md`** — Read when:
- Deciding whether a constraint belongs in CLAUDE.md or a source file header
- Writing or reviewing source file headers
- CLAUDE.md is growing and needs triage

**`references/ENGINEERING_PRINCIPLES.md`** — Read when:
- Need to cite sources (Deming, Ohno, Martin)
- Explaining principles to stakeholders
- Deep dive on a specific principle's origin

## Lean Applicability by Domain

TPS principles apply differently depending on whether work is repetitive or exploratory:

| Work Type | Variation Reduction | TPS Fit | Notes |
|-----------|---------------------|---------|-------|
| Manufacturing | Essential | Direct | Designed for this |
| Traditional software | Partial | Selective | Discovery work; cycle time targets don't translate |
| AI-assisted workflows | Essential | Direct | Stochastic outputs require variation reduction |

**Traditional software caveat**: Software development is primarily discovery work (Poppendieck, Fowler). The goal is not to reduce cycle time variation — it is to solve novel problems. Kanban, pull systems, waste identification, and SSoT translate well. Standardized production rates and defect-per-unit targets borrowed from manufacturing miss the point. DORA (2025) reflects this: its seven team archetypes combine delivery metrics with human factors (burnout, friction, perceived value).

**AI workflow exception — TPS applies more directly than to software**: LLM outputs are stochastic; the same prompt can produce different outputs on each run. Variation reduction becomes essential infrastructure:

- **Poka-yoke** → Constrained decoding and output schemas prevent malformed outputs before they occur (constrained decoding masks invalid tokens at generation time — zero format failures)
- **Standardized work** → Skills and CLAUDE.md are standardized work instructions; they reduce behavioral variation across agent runs
- **Jidoka** → Trust scoring and automated evals flag out-of-spec outputs for human review in real time; first two Jidoka steps (detect, alert) automate; fix + root cause require human judgment
- **SPC** → Temperature and seed pinning statistically control output variance (as of June 2026, no major hosted LLM guarantees bitwise determinism — best-effort only)
- **Yield engineering** → Multi-step agent reliability compounds: 95% per-step accuracy = 59% success over 10 steps; 0.6% over 100 steps — the same yield arithmetic semiconductor fabs engineer against

Context engineering — curating what reaches the LLM at inference time — IS variation reduction. This is not a metaphor: it is the primary mechanism by which skills, CLAUDE.md, and structured prompts produce reliable behavior.

## Cross-References

| Need | Skill |
|------|-------|
| Context engineering, CLAUDE.md, prompts | `optimizing-context` |
| Building skills | `building-skills` |
| Design First operationalized (Pre-Code Checklist) | `code-standards` |

## Foundational Role

This skill provides methodology that other skills apply. optimizing-context, building-skills, and domain-specific skills reference these principles for architectural decisions. For AI-assisted workflows specifically, see Lean Applicability by Domain above — TPS variation reduction applies more directly to stochastic LLM systems than to traditional software.
