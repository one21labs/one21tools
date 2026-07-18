#!/usr/bin/env python3
"""Partition engineering-principles SKILL.md + 3 refs into OPERATIONAL / CONCEPTUAL variants
(issue #244 partition ruling). Reads the working tree, writes partition/SPEC.md (audit-trail copy
of the pre-registered ruling this script implements) and partition/{operational,conceptual}/*.md.

Method: section-heading (H2) dispatch against a hardcoded table mirroring SPEC.md, plus a small
number of named sentence/paragraph-level splits for content mixed within one section (Core
Principle in design-review.md and ssot-enforcement.md; the file-level intro line in design-review.md
and ssot-enforcement.md). TOC blocks (navigation, not content) are dropped from both variants.
A section's heading travels with whichever variant retains its content; a SPLIT section's heading
is emitted into BOTH variants, once each, ahead of that variant's retained slice.

FAILS LOUDLY (nonzero exit): if a source file's H2 headings don't exactly match what this script's
dispatch table accounts for (extra heading -> exit 2, naming it; missing expected heading -> exit 2,
naming it), or if a named sentence/paragraph split's literal anchor text isn't found (content drifted
since the spec was written -> exit 2, naming the anchor). Never silently classifies unlisted content.

Deterministic, zero deps, python3. Run from anywhere; paths are relative to this file and the repo.
"""
import os
import re
import sys
import json

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(BASE, "..", ".."))
SKILL = "engineering-principles"
PART = os.path.join(BASE, "partition")
OP_DIR = os.path.join(PART, "operational")
CO_DIR = os.path.join(PART, "conceptual")
os.makedirs(OP_DIR, exist_ok=True)
os.makedirs(CO_DIR, exist_ok=True)

OPERATIONAL, CONCEPTUAL, SPLIT = "OPERATIONAL", "CONCEPTUAL", "SPLIT"


def fail(msg):
    sys.stderr.write(f"partition.py: FAIL: {msg}\n")
    sys.exit(2)


def read_repo_file(rel):
    path = os.path.join(REPO, "skills", SKILL, rel)
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def strip_frontmatter(text):
    return re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S).strip()


HEADING_RE = re.compile(r"^## (.+)$")


def real_heading_matches(text):
    """H2 headings ('^## ') outside fenced (```) code blocks -- root-cause-analysis.md's Output
    Template contains a literal '## Root Cause Analysis: [Problem Title]' inside a ```markdown
    fence (example text, not a real section) that a fence-naive scan would misfire on."""
    matches, in_fence, pos = [], False, 0
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        elif not in_fence:
            m = HEADING_RE.match(line)
            if m:
                matches.append((pos, pos + len(line.rstrip("\n")), m.group(1).strip()))
        pos += len(line)
    return matches


def split_sections(text):
    """Return (ordered list of (heading_text, content) pairs) for a text starting at the first
    real H2 heading. content = everything between this heading line and the next real H2 (or
    EOF), stripped."""
    matches = real_heading_matches(text)
    if not matches:
        return []
    out = []
    for i, (_s, e, heading) in enumerate(matches):
        start = e
        end = matches[i + 1][0] if i + 1 < len(matches) else len(text)
        out.append((heading, text[start:end].strip()))
    return out


def check_headings(filename, actual, expected):
    """actual, expected: ordered lists of heading text. Fail loud on any mismatch (extra or
    missing) -- never silently classify a heading the spec didn't name."""
    actual_set, expected_set = set(actual), set(expected)
    extra = [h for h in actual if h not in expected_set]
    missing = [h for h in expected if h not in actual_set]
    if extra:
        fail(f"{filename}: heading(s) not named in partition-spec.md: {extra!r} -- "
             f"refusing to silently classify unlisted content")
    if missing:
        fail(f"{filename}: expected heading(s) missing from source: {missing!r}")
    if actual != expected:
        fail(f"{filename}: heading order changed (expected {expected!r}, got {actual!r})")


def block(heading, content):
    return f"## {heading}\n\n{content}"


# --------------------------------------------------------------------------------------------
# SKILL.md
# --------------------------------------------------------------------------------------------
SKILL_EXPECTED = [
    ("Quick Decision Guide", OPERATIONAL),
    ("Core Decision Heuristics", OPERATIONAL),
    ("When to Read References", OPERATIONAL),
    ("Lean Applicability by Domain", CONCEPTUAL),
    ("Cross-References", OPERATIONAL),
    ("Foundational Role", CONCEPTUAL),
]


def process_skill():
    raw = strip_frontmatter(read_repo_file("SKILL.md"))
    m = re.match(r"^(# Engineering Principles)\n\n(.+?)\n\n(## .+)\Z", raw, re.S)
    if not m:
        fail("SKILL.md: preamble shape (H1 / intro / first heading) did not match -- content drifted")
    h1, intro, rest = m.group(1), m.group(2).strip(), m.group(3)

    sections = split_sections(rest)
    headings = [h for h, _ in sections]
    expected_headings = [h for h, _ in SKILL_EXPECTED]
    check_headings("SKILL.md", headings, expected_headings)
    content = dict(sections)

    op_parts, co_parts = [h1], [h1, intro]   # whole intro -> CONCEPTUAL (spec line 15)
    for heading, cls in SKILL_EXPECTED:
        b = block(heading, content[heading])
        (op_parts if cls == OPERATIONAL else co_parts).append(b)

    return {
        "name": "SKILL.md",
        "operational": "\n\n".join(op_parts),
        "conceptual": "\n\n".join(co_parts),
        "toc_dropped_chars": 0,
        "raw_full_chars": len(raw),
        "h1_chars": len(h1),
        "duplicated_headings": [],   # no SPLIT sections in SKILL.md
    }


# --------------------------------------------------------------------------------------------
# references/design-review.md
# --------------------------------------------------------------------------------------------
DESIGN_REVIEW_EXPECTED = [
    ("Core Principle", SPLIT),
    ("When to Use", OPERATIONAL),
    ("Software Design Checklist", OPERATIONAL),
    ("Documentation Design Checklist", OPERATIONAL),
    ("Process Design Checklist", OPERATIONAL),
    ("Feature/Product Design Checklist", OPERATIONAL),
    ("Review Process", OPERATIONAL),
    ("Anti-Patterns", OPERATIONAL),
]
DR_INTRO_OP = "Checklists to verify design completeness before implementation."
DR_INTRO_CO = "Fixing design is cheap; fixing implementation is expensive."
DR_CORE_OP = ("**Design before implementation.** Outline before draft. Architecture before code. "
              "Spec before build.")


def process_design_review():
    raw = read_repo_file("references/design-review.md")
    # H1, TOC (heading + bullet list), intro line (NOT part of the TOC section -- it falls
    # between the TOC list and "## Core Principle"), then the dispatched sections.
    m = re.match(
        r"^(# Design Review)\n\n(## Table of Contents\n\n(?:- \[.+\]\(#.+\)\n)+)\n(.+?)\n\n(## Core Principle.*)\Z",
        raw, re.S)
    if not m:
        fail("design-review.md: preamble shape (H1 / TOC / intro / Core Principle) did not match")
    h1, toc_block, intro, rest = m.group(1), m.group(2), m.group(3).strip(), m.group(4)

    if intro != f"{DR_INTRO_OP} {DR_INTRO_CO}":
        fail(f"design-review.md: intro-line anchor text drifted; got {intro!r}")

    sections = split_sections(rest)
    headings = [h for h, _ in sections]
    expected_headings = [h for h, _ in DESIGN_REVIEW_EXPECTED]
    check_headings("design-review.md", headings, expected_headings)
    content = dict(sections)

    core = content["Core Principle"]
    core_co = ("The parent-child relationship:\n- Design (parent) → Implementation (child)\n"
               "- Implementation follows from design\n- If design is wrong, implementation will be wrong\n"
               "- Rework is waste")
    if core != f"{DR_CORE_OP}\n\n{core_co}":
        fail(f"design-review.md: Core Principle anchor text drifted; got {core!r}")

    op_parts, co_parts = [h1, DR_INTRO_OP], [h1, DR_INTRO_CO]
    op_parts.append(block("Core Principle", DR_CORE_OP))
    co_parts.append(block("Core Principle", core_co))
    for heading, cls in DESIGN_REVIEW_EXPECTED:
        if heading == "Core Principle":
            continue
        b = block(heading, content[heading])
        (op_parts if cls == OPERATIONAL else co_parts).append(b)

    return {
        "name": "design-review.md",
        "operational": "\n\n".join(op_parts),
        "conceptual": "\n\n".join(co_parts),
        "toc_dropped_chars": len(toc_block),
        "raw_full_chars": len(raw.strip()),
        "h1_chars": len(h1),
        "duplicated_headings": ["Core Principle"],
    }


# --------------------------------------------------------------------------------------------
# references/root-cause-analysis.md
# --------------------------------------------------------------------------------------------
RCA_EXPECTED = [
    ("When to Use", OPERATIONAL),
    ("5 Whys Method", OPERATIONAL),
    ("Branching Analysis", OPERATIONAL),
    ("Facilitation Guide", OPERATIONAL),
    ("Output Template", OPERATIONAL),
    ("Deming's Insight", CONCEPTUAL),
]
RCA_INTRO = "Methodology for finding and fixing the actual cause of problems, not just symptoms."


def process_rca():
    raw = read_repo_file("references/root-cause-analysis.md")
    m = re.match(r"^(# Root Cause Analysis)\n\n(.+?)\n\n(## When to Use.*)\Z", raw, re.S)
    if not m:
        fail("root-cause-analysis.md: preamble shape (H1 / intro / first heading) did not match")
    h1, intro, rest = m.group(1), m.group(2).strip(), m.group(3)
    if intro != RCA_INTRO:
        fail(f"root-cause-analysis.md: intro-line anchor text drifted; got {intro!r}")

    sections = split_sections(rest)
    headings = [h for h, _ in sections]
    expected_headings = [h for h, _ in RCA_EXPECTED]
    check_headings("root-cause-analysis.md", headings, expected_headings)
    content = dict(sections)

    op_parts, co_parts = [h1], [h1, intro]   # whole intro -> CONCEPTUAL (spec line 32)
    for heading, cls in RCA_EXPECTED:
        b = block(heading, content[heading])
        (op_parts if cls == OPERATIONAL else co_parts).append(b)

    return {
        "name": "root-cause-analysis.md",
        "operational": "\n\n".join(op_parts),
        "conceptual": "\n\n".join(co_parts),
        "toc_dropped_chars": 0,
        "raw_full_chars": len(raw.strip()),
        "h1_chars": len(h1),
        "duplicated_headings": [],
    }


# --------------------------------------------------------------------------------------------
# references/ssot-enforcement.md
# --------------------------------------------------------------------------------------------
SSOT_EXPECTED = [
    ("Core Principle", SPLIT),
    ("Violation Indicators", OPERATIONAL),
    ("Common SSoT Violations by Domain", OPERATIONAL),
    ("Audit Process", OPERATIONAL),
    ("SSoT Registry", OPERATIONAL),
    ("Edge Cases", OPERATIONAL),
    ("Verification Questions", OPERATIONAL),
]
SSOT_INTRO_CO = "Single Source of Truth: each fact has ONE canonical location."
SSOT_INTRO_OP = "Reference, don't duplicate."


def process_ssot():
    raw = read_repo_file("references/ssot-enforcement.md")
    m = re.match(
        r"^(# SSoT Enforcement)\n\n(.+?)\n\n(## Table of Contents\n\n(?:\d+\. \[.+\]\(#.+\)\n)+)\n(## Core Principle.*)\Z",
        raw, re.S)
    if not m:
        fail("ssot-enforcement.md: preamble shape (H1 / intro / TOC / Core Principle) did not match")
    h1, intro, toc_block, rest = m.group(1), m.group(2).strip(), m.group(3), m.group(4)
    if intro != f"{SSOT_INTRO_CO} {SSOT_INTRO_OP}":
        fail(f"ssot-enforcement.md: intro-line anchor text drifted; got {intro!r}")

    sections = split_sections(rest)
    headings = [h for h, _ in sections]
    expected_headings = [h for h, _ in SSOT_EXPECTED]
    check_headings("ssot-enforcement.md", headings, expected_headings)
    content = dict(sections)

    core = content["Core Principle"]
    core_bq = ('> "Every piece of knowledge must have a single, unambiguous, authoritative '
               'representation within a system."')
    core_op = ('**Time pressure is not an exemption.** If a fix requires pasting the same value '
               'into N files, put it in one place and have all N reference it — one constant '
               'plus N imports is not slower than N literals, so declining it is not "cleverness." '
               'Defer only genuinely separate scope bundled into the same request (retry logic, '
               'logging, refactors); never defer the single-definition step itself.')
    core_bullets = ("When information exists in multiple places:\n"
                     "- Updates miss some locations → contradictions\n"
                     "- Contradictions cause bugs, confusion, wrong decisions\n"
                     "- Maintenance burden multiplies")
    if core != f"{core_bq}\n\n{core_op}\n\n{core_bullets}":
        fail(f"ssot-enforcement.md: Core Principle anchor text drifted; got {core!r}")
    core_co = f"{core_bq}\n\n{core_bullets}"

    op_parts, co_parts = [h1, SSOT_INTRO_OP], [h1, SSOT_INTRO_CO]
    op_parts.append(block("Core Principle", core_op))
    co_parts.append(block("Core Principle", core_co))
    for heading, cls in SSOT_EXPECTED:
        if heading == "Core Principle":
            continue
        b = block(heading, content[heading])
        (op_parts if cls == OPERATIONAL else co_parts).append(b)

    return {
        "name": "ssot-enforcement.md",
        "operational": "\n\n".join(op_parts),
        "conceptual": "\n\n".join(co_parts),
        "toc_dropped_chars": len(toc_block),
        "raw_full_chars": len(raw.strip()),
        "h1_chars": len(h1),
        "duplicated_headings": ["Core Principle"],
    }


CORE_PRINCIPLE_HEADING_CHARS = len("## Core Principle")

SPEC_TEXT = """# ep-partition build spec (issue #244) — orchestrator's partition ruling, 2026-07-18

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
"""


def main():
    with open(os.path.join(PART, "SPEC.md"), "w", encoding="utf-8", newline="") as fh:
        fh.write(SPEC_TEXT)

    results = [process_skill(), process_design_review(), process_rca(), process_ssot()]

    for r in results:
        with open(os.path.join(OP_DIR, r["name"]), "w", encoding="utf-8", newline="") as fh:
            fh.write(r["operational"])
        with open(os.path.join(CO_DIR, r["name"]), "w", encoding="utf-8", newline="") as fh:
            fh.write(r["conceptual"])

    chars = {
        r["name"]: {
            "operational_chars": len(r["operational"]),
            "conceptual_chars": len(r["conceptual"]),
            "toc_dropped_chars": r["toc_dropped_chars"],
            "raw_full_chars": r["raw_full_chars"],
            "h1_chars": r["h1_chars"],
            "duplicated_headings": r["duplicated_headings"],
            "duplicated_heading_chars": sum(
                CORE_PRINCIPLE_HEADING_CHARS for _ in r["duplicated_headings"]),
        }
        for r in results
    }
    with open(os.path.join(PART, "chars.json"), "w", encoding="utf-8", newline="") as fh:
        json.dump(chars, fh, indent=1)

    print("partitioned 4 files -> partition/{operational,conceptual}/*.md ; partition/SPEC.md written")
    for r in results:
        c = chars[r["name"]]
        # overlap = H1 duplicated across both variants (once extra) + any SPLIT heading duplicated
        overlap = c["h1_chars"] + c["duplicated_heading_chars"]
        gap = (c["operational_chars"] + c["conceptual_chars"] + c["toc_dropped_chars"]) - c["raw_full_chars"]
        print(f"  {r['name']}: op={c['operational_chars']} co={c['conceptual_chars']} "
              f"toc_dropped={c['toc_dropped_chars']} raw={c['raw_full_chars']} "
              f"gap={gap:+d} accounted_overlap={overlap} residual={gap - overlap:+d}")


if __name__ == "__main__":
    main()
