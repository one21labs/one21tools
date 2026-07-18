# ep-partition build spec (issue #244) — orchestrator's partition ruling, 2026-07-18

Pre-registered rule (issue #244): sentence-level — imperative/trigger/when-to content ->
OPERATIONAL; definitional/attributional content (what a principle IS, origins, citations,
why-it-matters claims) -> CONCEPTUAL. Partition applies to EXACTLY the arm-B treatment content
(07-09 construction: stripped SKILL.md body + references/{ssot-enforcement,design-review,
root-cause-analysis}.md). Clarification recorded: references/ENGINEERING_PRINCIPLES.md was never
part of the 07-09 treatment, so the issue's "strip it wholesale" clause is vacuous here.

TOC blocks: navigation, not content — DROP from both C and D variants (record in metadata).
Section headings: retained in whichever variant keeps the section's content (or the retained
sentence-slice); a section whose content is entirely in the other class is dropped headline+body.

## SKILL.md body (frontmatter already stripped by prep)
- Intro line "Foundational meta-skill: TPS/Lean principles adapted... Provides the 'why' behind other skills' 'how.'" -> CONCEPTUAL
- "## Quick Decision Guide" (whole table) -> OPERATIONAL
- "## Core Decision Heuristics" (whole table) -> OPERATIONAL
- "## When to Read References" (all subsections) -> OPERATIONAL
- "## Lean Applicability by Domain" (whole table) -> CONCEPTUAL
- "## Cross-References" (whole table) -> OPERATIONAL
- "## Foundational Role" (paragraph) -> CONCEPTUAL

## references/design-review.md
- Intro line sentence 1 "Checklists to verify design completeness before implementation." -> OPERATIONAL; sentence 2 "Fixing design is cheap; fixing implementation is expensive." -> CONCEPTUAL
- "## Core Principle": bold line "**Design before implementation.** Outline before draft. Architecture before code. Spec before build." -> OPERATIONAL; "The parent-child relationship:" + its 4 bullets -> CONCEPTUAL
- "## When to Use" table -> OPERATIONAL
- All four checklist sections (Software/Documentation/Process/Feature-Product) -> OPERATIONAL
- "## Review Process" (Self-Review, Peer Review, Go/No-Go incl. "Approval is not completeness" paragraph) -> OPERATIONAL
- "## Anti-Patterns" table -> OPERATIONAL

## references/root-cause-analysis.md
- Intro line "Methodology for finding and fixing the actual cause of problems, not just symptoms." -> CONCEPTUAL
- "## When to Use" table -> OPERATIONAL
- "## 5 Whys Method" (structure, stopping criteria, example, common mistakes) -> OPERATIONAL
- "## Branching Analysis" -> OPERATIONAL
- "## Facilitation Guide" -> OPERATIONAL
- "## Output Template" -> OPERATIONAL
- "## Deming's Insight" (quote + closing paragraph) -> CONCEPTUAL

## references/ssot-enforcement.md
- Intro line: sentence 1 "Single Source of Truth: each fact has ONE canonical location." -> CONCEPTUAL; sentence 2 "Reference, don't duplicate." -> OPERATIONAL
- "## Core Principle": the blockquote ("Every piece of knowledge must have a single, unambiguous, authoritative representation within a system.") -> CONCEPTUAL; "**Time pressure is not an exemption.**..." paragraph -> OPERATIONAL; "When information exists in multiple places:" + 3 bullets -> CONCEPTUAL
- "## Violation Indicators" table -> OPERATIONAL
- "## Common SSoT Violations by Domain" (all four tables) -> OPERATIONAL
- "## Audit Process" (all 5 steps incl. grep patterns) -> OPERATIONAL
- "## SSoT Registry" -> OPERATIONAL
- "## Edge Cases" -> OPERATIONAL
- "## Verification Questions" -> OPERATIONAL

## Arm treatment definitions
- A `without`: no treatment file (harness handles).
- B `with-full`: 07-09 construction verbatim: stripped body + the 3 refs, each block prefixed
  "=== references/<name> ===". Built from the SAME source files at the SAME commit.
- C `with-operational`: same construction, each source replaced by its OPERATIONAL variant.
- D `with-conceptual`: same construction, each source replaced by its CONCEPTUAL variant. A file
  whose conceptual variant is empty is omitted from the join entirely.
