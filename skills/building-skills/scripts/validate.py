#!/usr/bin/env python3
"""
Skill Validation Module

Validates Claude skill structure against documented requirements.

Evidence Sources:
- agentskills.io spec: Field constraints, max lengths
  https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx
- platform.claude.com best practices: No XML chars, third person
  https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- GitHub issues #9954, #11266: Trigger phrase required for activation
- Reserved words (anthropic, claude): Confirmed by upload testing

Usage:
    python validate.py <skill-folder>
    python validate.py --help
"""
import re
import sys
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


import re


NAME_MAX = 64
DESC_MAX = 1024
BODY_MAX_CHARS = 6000           # SKILL.md body char cap (ADR 0009; ungameable by long lines, cf. line caps)
TOC_THRESHOLD = 150             # SKILL.md body: TOC required past this many LINES (a sub-cap readability aid)
REFERENCE_MAX_CHARS = 12000     # skill references/*.md char cap (ADR 0009; the progressive-disclosure tier)
REFERENCE_TOC_THRESHOLD = 6000  # a reference past this many CHARS must carry a TOC
NAME_PATTERN = re.compile(r'^[a-z0-9-]+$')
RESERVED_WORDS = ["anthropic", "claude"]
VALID_TRIGGERS = ["invoke when", "use when", "use for", "apply when"]
TOC_MARKERS = ["## table of contents", "## toc", "## contents"]

# Emoji detection pattern - matches most emoji ranges
# Covers: emoticons, dingbats, symbols, pictographs, transport, flags, etc.
EMOJI_PATTERN = re.compile(
    r'['
    r'\U0001F300-\U0001F9FF'  # Miscellaneous Symbols and Pictographs, Emoticons, etc.
    r'\U00002700-\U000027BF'  # Dingbats
    r'\U00002600-\U000026FF'  # Miscellaneous Symbols
    r'\U00002B50-\U00002B55'  # Stars, circles
    r'\U0000FE00-\U0000FE0F'  # Variation Selectors
    r'\U0001FA00-\U0001FAFF'  # Chess, symbols
    r'\u2713\u2714\u2717\u2718'  # Checkmarks and X marks
    r'\u26a0'  # Warning sign
    r']'
)


def contains_emoji(text: str) -> bool:
    """Check if text contains any emoji characters."""
    return bool(EMOJI_PATTERN.search(text))


@dataclass
class ValidationResult:
    valid: bool
    error: str = ""
    warnings: List[str] = field(default_factory=list)


def validate_skill(skill_path: Path) -> ValidationResult:
    """Validate skill directory."""
    skill_path = Path(skill_path)
    folder_name = skill_path.name
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        return ValidationResult(False, "SKILL.md not found")

    content = skill_md.read_text(encoding="utf-8")

    # R5: No emojis in SKILL.md
    if contains_emoji(content):
        return ValidationResult(False, "SKILL.md contains emoji characters (emojis are prohibited)")
    
    if not content.startswith("---"):
        return ValidationResult(False, "SKILL.md must start with --- (YAML frontmatter)")
    
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return ValidationResult(False, "YAML frontmatter missing closing ---")
    
    # Parse frontmatter lines
    frontmatter = match.group(1).strip()
    lines = frontmatter.split('\n')
    
    # R2.1: name must be first
    if not lines or not lines[0].startswith('name:'):
        return ValidationResult(False, "'name:' must be first field in frontmatter")
    
    # R3.1: description must be second
    if len(lines) < 2 or not lines[1].startswith('description:'):
        return ValidationResult(False, "'description:' must be second field in frontmatter")
    
    name = lines[0].split(':', 1)[1].strip() if ':' in lines[0] else ''
    description = lines[1].split(':', 1)[1].strip() if ':' in lines[1] else ''
    
    # R2.2: non-empty name
    if not name:
        return ValidationResult(False, "Name is empty")
    
    # R2.8: no XML chars (check before kebab-case for clearer error)
    if '<' in name or '>' in name:
        return ValidationResult(False, "Name cannot contain XML characters (< or >)")
    
    # R2.3: max length
    if len(name) > NAME_MAX:
        return ValidationResult(False, f"Name exceeds {NAME_MAX} chars ({len(name)} chars)")
    
    # R2.4: kebab-case
    if not NAME_PATTERN.match(name):
        return ValidationResult(False, f"Name must be lowercase kebab-case (a-z, 0-9, hyphens). Got: '{name}'")
    
    # R2.5: no edge hyphens
    if name.startswith('-'):
        return ValidationResult(False, "Name cannot start with hyphen")
    if name.endswith('-'):
        return ValidationResult(False, "Name cannot end with hyphen")
    
    # R2.6: no consecutive hyphens
    if '--' in name:
        return ValidationResult(False, "Name cannot have consecutive hyphens (--)")
    
    # R2.7: no reserved words
    if name in RESERVED_WORDS:
        return ValidationResult(False, f"'{name}' is a reserved word")
    
    # R2.9: match folder
    if name != folder_name:
        return ValidationResult(False, f"Name '{name}' must match folder name '{folder_name}'")
    
    # R3.2: non-empty description
    if not description:
        return ValidationResult(False, "Description is empty")
    
    # R3.4: no XML chars
    if '<' in description or '>' in description:
        return ValidationResult(False, "Description cannot contain XML characters (< or >)")
    
    # R3.3: max length
    if len(description) > DESC_MAX:
        return ValidationResult(False, f"Description exceeds {DESC_MAX} chars ({len(description)} chars)")
    
    # R3.5 & R3.6: trigger at start
    desc_lower = description.lower()
    starts_with_trigger = any(desc_lower.startswith(t) for t in VALID_TRIGGERS)
    
    if not starts_with_trigger:
        has_trigger = any(t in desc_lower for t in VALID_TRIGGERS)
        if has_trigger:
            return ValidationResult(False, "Trigger phrase must be at start of description")
        return ValidationResult(False, "Description must start with trigger: 'Invoke when', 'Use when', 'Use for', or 'Apply when'")
    
    # R3.7: first/second person (warning)
    warnings = []
    if re.search(r'\b(I can|I will|you can|you should)\b', description, re.IGNORECASE):
        warnings.append("Description uses first/second person. Use third person.")
    
    # R4: Body validation (ADR 0009 — char cap, not a gameable line cap)
    body = content[match.end():]
    body_norm = body.replace('\r\n', '\n').strip()
    # Frontmatter keys beyond name/description (which have their own caps) count toward the body
    # budget too — else a `details: |` block scalar would smuggle unbounded prose past the cap.
    extra_fm = "\n".join(l for l in lines if not (l.startswith("name:") or l.startswith("description:")))
    body_chars = len(body_norm) + len(extra_fm.strip())
    line_count = len(body_norm.split('\n')) if body_norm else 0

    # R4.1: max chars
    if body_chars > BODY_MAX_CHARS:
        return ValidationResult(False, f"Body exceeds {BODY_MAX_CHARS} chars ({body_chars} chars)")

    # R4.2: ToC past the readability line threshold (a sub-cap navigation aid)
    if line_count > TOC_THRESHOLD:
        body_lower = body.lower()
        has_toc = any(m in body_lower for m in TOC_MARKERS)
        if not has_toc:
            return ValidationResult(False, f"Body has {line_count} lines (>{TOC_THRESHOLD}). Add '## Table of Contents'")

    # R5.2: No emojis in script files
    scripts_dir = skill_path / "scripts"
    if scripts_dir.exists():
        for script_file in scripts_dir.rglob("*.py"):
            try:
                script_content = script_file.read_text(encoding="utf-8")
                if contains_emoji(script_content):
                    rel_path = script_file.relative_to(skill_path)
                    return ValidationResult(False, f"Script {rel_path} contains emoji characters (emojis are prohibited)")
            except Exception:
                pass  # Skip files that can't be read

    # R6: references/*.md — no emoji (skill content, per CLAUDE.md), char cap + TOC past the threshold (ADR 0009)
    refs_dir = skill_path / "references"
    if refs_dir.exists():
        for ref in sorted(refs_dir.glob("*.md")):
            ref_text = ref.read_text(encoding="utf-8")
            ref_chars = len(ref_text.replace('\r\n', '\n'))
            rel = ref.relative_to(skill_path)
            if contains_emoji(ref_text):
                return ValidationResult(False, f"Reference {rel} contains emoji characters (emojis are prohibited)")
            if ref_chars > REFERENCE_MAX_CHARS:
                return ValidationResult(False, f"Reference {rel} exceeds {REFERENCE_MAX_CHARS} chars ({ref_chars} chars)")
            if ref_chars > REFERENCE_TOC_THRESHOLD and not any(m in ref_text.lower() for m in TOC_MARKERS):
                return ValidationResult(False, f"Reference {rel} has {ref_chars} chars (>{REFERENCE_TOC_THRESHOLD}). Add '## Table of Contents'")

    return ValidationResult(True, "", warnings)


def main():
    parser = argparse.ArgumentParser(
        prog="validate.py",
        description="Validate Claude skill structure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
RULES
=====
Name (FIRST field):
  - Max {NAME_MAX} chars, kebab-case (a-z, 0-9, hyphens)
  - Must match folder name
  - No leading/trailing/consecutive hyphens
  - No reserved words: 'anthropic', 'claude'

Description (SECOND field):
  - Max {DESC_MAX} chars
  - Must START with: 'Invoke when', 'Use when', 'Use for', 'Apply when'

Body:
  - Max {BODY_MAX_CHARS} chars
  - If >{TOC_THRESHOLD} lines, must have '## Table of Contents'

References (references/*.md):
  - Max {REFERENCE_MAX_CHARS} chars
  - If >{REFERENCE_TOC_THRESHOLD} chars, must have '## Table of Contents'

NEXT STEP
=========
  python package.py <skill-folder> [output-dir]
""")
    parser.add_argument("skill_directory", type=Path)
    args = parser.parse_args()
    
    if not args.skill_directory.exists():
        print(f"[FAIL] Not found: {args.skill_directory}")
        return 1

    result = validate_skill(args.skill_directory)

    if result.valid:
        print("[OK] Valid")
        for w in result.warnings:
            print(f"  [WARN] {w}")
        print(f"\nNext: python package.py {args.skill_directory}")
        return 0
    else:
        print(f"[FAIL] {result.error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
