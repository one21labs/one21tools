#!/usr/bin/env python3
"""
Skill Initialization Script

Creates valid skill directory structure with TODO placeholders.
Validates name immediately using same rules as validate.py.

Evidence Sources:
- agentskills.io spec: Field constraints, max lengths
- platform.claude.com best practices: No XML chars
- Reserved words (anthropic, claude): Confirmed by upload testing

Usage:
    python init.py <skill-name> [output-directory]
    python init.py my-skill ./skills

Creates:
    <output-directory>/<skill-name>/
    └── SKILL.md (with valid frontmatter + TODO placeholders)
"""
import sys
import re
import argparse
from pathlib import Path

# Same constants as validate.py
NAME_MAX = 64
NAME_PATTERN = re.compile(r'^[a-z0-9-]+$')
RESERVED_WORDS = ["anthropic", "claude"]

# The body cap is validate.py's (the SSoT) — imported so the scaffold can't drift from the gate.
from validate import BODY_MAX_CHARS

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


def validate_name(name: str) -> tuple[bool, str]:
    """Validate skill name. Returns (valid, error_message)."""
    if not name:
        return False, "Name is empty"
    
    if '<' in name or '>' in name:
        return False, "Name cannot contain XML characters (< or >)"
    
    if len(name) > NAME_MAX:
        return False, f"Name exceeds {NAME_MAX} chars ({len(name)} chars)"
    
    if not NAME_PATTERN.match(name):
        return False, f"Name must be lowercase kebab-case (a-z, 0-9, hyphens). Got: '{name}'"
    
    if name.startswith('-'):
        return False, "Name cannot start with hyphen"
    
    if name.endswith('-'):
        return False, "Name cannot end with hyphen"
    
    if '--' in name:
        return False, "Name cannot have consecutive hyphens (--)"
    
    if name in RESERVED_WORDS:
        return False, f"'{name}' is a reserved word"
    
    return True, ""


def main():
    parser = argparse.ArgumentParser(
        prog="init.py",
        description="Initialize new skill with valid structure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
NAME RULES
==========
  - Max 64 chars, kebab-case (a-z, 0-9, hyphens)
  - No leading/trailing/consecutive hyphens
  - No reserved words: 'anthropic', 'claude'

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
