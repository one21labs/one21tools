#!/usr/bin/env python3
"""
Skill Initialization Script

Creates valid skill directory structure with TODO placeholders.
Validates the name immediately via validate.py's shared validate_name (ADR 0010).

Usage:
    python init.py <skill-name> [output-directory]
    python init.py my-skill ./skills

Creates:
    <output-directory>/<skill-name>/
    └── SKILL.md (with valid frontmatter + TODO placeholders)
"""
import sys
import argparse
from pathlib import Path

# The name rules and body cap are validate.py's (the SSoT) — imported so neither the check
# nor the scaffold can drift from the gate (ADR 0010).
from validate import BODY_MAX_CHARS, NAME_MAX, RESERVED_WORDS, validate_name

SKILL_TEMPLATE = """---
name: {name}
description: Invoke when [TODO: conditions]. Use for [TODO: tasks]. [TODO: immediate instructions].
---

# {title}

## Table of Contents

1. [Overview](#overview)
2. [TODO: Add sections](#todo)

---

## Overview

[TODO: Brief description of what this skill does]

---

## TODO

[TODO: Add skill content]

- Use imperative form ("Extract text", not "This extracts text")
- Reference files with "when to read" guidance
- Keep under {body_max:,} chars (move details to references/)
"""


def main():
    parser = argparse.ArgumentParser(
        prog="init.py",
        description="Initialize new skill with valid structure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
NAME RULES
==========
  - Max {NAME_MAX} chars, kebab-case (a-z, 0-9, hyphens)
  - No leading/trailing/consecutive hyphens
  - No reserved words: {', '.join(repr(w) for w in RESERVED_WORDS)}

EXAMPLE
=======
  python init.py pdf-processor ./my-skills
  
  Creates: ./my-skills/pdf-processor/SKILL.md

NEXT STEPS
==========
  1. Edit SKILL.md - replace TODO placeholders
  2. Add scripts/, references/, assets/ as needed
  3. Validate: python validate.py <skill-folder>
  4. Package: python package.py <skill-folder>
""")
    parser.add_argument("skill_name", help="Name for the skill (kebab-case)")
    parser.add_argument("output_directory", type=Path, nargs='?', default=Path('.'),
                       help="Where to create skill folder (default: current dir)")
    args = parser.parse_args()
    
    # Validate name first
    valid, error = validate_name(args.skill_name)
    if not valid:
        print(f"[FAIL] Invalid name: {error}")
        return 1

    # Create skill directory
    skill_dir = args.output_directory / args.skill_name
    if skill_dir.exists():
        print(f"[FAIL] Already exists: {skill_dir}")
        return 1

    skill_dir.mkdir(parents=True)

    # Create SKILL.md with template
    title = args.skill_name.replace('-', ' ').title()
    content = SKILL_TEMPLATE.format(name=args.skill_name, title=title, body_max=BODY_MAX_CHARS)
    (skill_dir / "SKILL.md").write_text(content)

    print(f"[OK] Created: {skill_dir}/")
    print(f"  +-- SKILL.md")
    print(f"\nNext: Edit SKILL.md, replace TODO placeholders")
    return 0


if __name__ == "__main__":
    sys.exit(main())
