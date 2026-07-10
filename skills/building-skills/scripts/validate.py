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
import json
import re
import sys
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


NAME_MAX = 64
DESC_MAX = 1024
BODY_MAX_CHARS = 6000           # SKILL.md body char cap (ADR 0009; ungameable by long lines, cf. line caps)
TOC_THRESHOLD = 150             # SKILL.md body: TOC required past this many LINES (a sub-cap readability aid)
REFERENCE_MAX_CHARS = 12000     # skill references/*.md char cap (ADR 0009; the progressive-disclosure tier)
REFERENCE_TOC_THRESHOLD = 6000  # a reference past this many CHARS must carry a TOC
NAME_PATTERN = re.compile(r'^[a-z0-9-]+$')
RESERVED_WORDS = ["anthropic", "claude"]
VALID_TRIGGERS = ["invoke when", "use when", "use for", "apply when"]
# Recognized TOC headings, anchored at line start (see validation-rules.md "Table of Contents
# Formats") — prose or a code block merely QUOTING a marker does not satisfy the gate.
TOC_RE = re.compile(r'(?im)^##\s*(table of contents|toc|contents)\b')

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


# R6.2 (ADR 0044): info-strings treated as runnable commands; a ```text/tree-diagram/bare fence
# is not linted, and this inline marker suppresses a deliberate worked example on its line.
RUNNABLE_INFO_STRINGS = {"bash", "sh", "shell", "console"}
SELF_PATH_ALLOW_MARKER = "validate:allow-self-path"


def find_self_referential_script_paths(text: str, folder_name: str) -> List[int]:
    """R6.2 (ADR 0044): line numbers of runnable fenced commands anchored at the skill's OWN
    folder (skills/<folder>/scripts/... or <folder>/scripts/...) -- that prefix exists only in
    the source repo, so the command breaks in an installed plugin. Own-name anchoring means a
    cross-skill reference (a different folder) never matches."""
    pattern = re.compile(r"(?:^|[\s'\"=(`])(?:skills/)?" + re.escape(folder_name) + r"/scripts/")
    offenders = []
    in_block = runnable = False
    for lineno, line in enumerate(text.split("\n"), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_block:
                in_block = runnable = False
            else:
                in_block = True
                runnable = stripped[3:].strip().lower() in RUNNABLE_INFO_STRINGS
            continue
        if (in_block and runnable and pattern.search(line)
                and SELF_PATH_ALLOW_MARKER not in line):
            offenders.append(lineno)
    return offenders


def validate_name(name: str) -> tuple[bool, str]:
    """R2.2-R2.8: the name rules, shared with init.py (ADR 0010). Excludes the folder-match
    check (R2.9), which needs an existing folder and stays in validate_skill."""
    # R2.2: non-empty name
    if not name:
        return False, "Name is empty"

    # R2.8: no XML chars (check before kebab-case for clearer error)
    if '<' in name or '>' in name:
        return False, "Name cannot contain XML characters (< or >)"

    # R2.3: max length
    if len(name) > NAME_MAX:
        return False, f"Name exceeds {NAME_MAX} chars ({len(name)} chars)"

    # R2.4: kebab-case
    if not NAME_PATTERN.match(name):
        return False, f"Name must be lowercase kebab-case (a-z, 0-9, hyphens). Got: '{name}'"

    # R2.5: no edge hyphens
    if name.startswith('-'):
        return False, "Name cannot start with hyphen"
    if name.endswith('-'):
        return False, "Name cannot end with hyphen"

    # R2.6: no consecutive hyphens
    if '--' in name:
        return False, "Name cannot have consecutive hyphens (--)"

    # R2.7: no reserved words
    if name in RESERVED_WORDS:
        return False, f"'{name}' is a reserved word"

    return True, ""


@dataclass
class ValidationResult:
    valid: bool
    error: str = ""
    warnings: List[str] = field(default_factory=list)


def validate_evals_json(skill_path: Path, folder_name: str) -> str:
    """R7: evals/evals.json, when present, matches skill-creator's schema (its
    references/schemas.md is the schema SSoT; this gate pins the shape the harness and
    eval_verdict.py consume — ADR 0013). Absent file = OK (evals are encouraged, not forced).
    Returns "" when valid, else the error."""
    evals_file = skill_path / "evals" / "evals.json"
    if not evals_file.exists():
        return ""
    try:
        data = json.loads(evals_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return f"evals/evals.json is not valid JSON: {e}"
    if not isinstance(data, dict):
        return "evals/evals.json must be an object with 'skill_name' and 'evals'"
    if data.get("skill_name") != folder_name:
        return f"evals/evals.json skill_name '{data.get('skill_name')}' must match folder '{folder_name}'"
    evals = data.get("evals")
    if not isinstance(evals, list) or not evals:
        return "evals/evals.json 'evals' must be a non-empty array"
    seen_ids = set()
    for i, ev in enumerate(evals):
        where = f"evals[{i}]"
        if not isinstance(ev, dict):
            return f"{where} must be an object"
        if not isinstance(ev.get("id"), int):
            return f"{where}: 'id' must be an integer"
        if ev["id"] in seen_ids:
            return f"{where}: duplicate id {ev['id']}"
        seen_ids.add(ev["id"])
        for key in ("prompt", "expected_output"):
            if not isinstance(ev.get(key), str) or not ev[key].strip():
                return f"{where}: '{key}' must be a non-empty string"
        exps = ev.get("expectations")
        if (not isinstance(exps, list) or not exps
                or not all(isinstance(x, str) and x.strip() for x in exps)):
            return f"{where}: 'expectations' must be a non-empty array of strings"
        files = ev.get("files", [])
        if not isinstance(files, list) or not all(isinstance(f, str) for f in files):
            return f"{where}: 'files' must be an array of paths"
    return ""


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
    
    # R2.2-R2.8: the shared name rules (validate_name above; init.py imports it too, ADR 0010)
    ok, err = validate_name(name)
    if not ok:
        return ValidationResult(False, err)

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
    
    # R4: Body validation (ADR 0009 — char cap, not a gameable line cap). read_text() already
    # normalizes newlines to \n (universal newlines), so counts are checkout-agnostic like charLen.
    body = content[match.end():]
    body_norm = body.strip()
    # Everything in the frontmatter beyond the first two lines (name/description, which carry their
    # own caps) counts toward the body budget — else a `details: |` block scalar or a DUPLICATED
    # name:/description: key would smuggle unbounded prose past the cap.
    extra_fm = "\n".join(lines[2:])
    body_chars = len(body_norm) + len(extra_fm.strip())
    line_count = len(body_norm.split('\n')) if body_norm else 0

    # R4.1: max chars
    if body_chars > BODY_MAX_CHARS:
        return ValidationResult(False, f"Body exceeds {BODY_MAX_CHARS} chars ({body_chars} chars)")

    # R4.2: ToC past the readability line threshold (a sub-cap navigation aid)
    if line_count > TOC_THRESHOLD and not TOC_RE.search(body):
        return ValidationResult(False, f"Body has {line_count} lines (>{TOC_THRESHOLD}). Add '## Table of Contents'")

    # R6.2 (ADR 0044): no self-referential repo-anchored script paths in runnable fences
    offenders = find_self_referential_script_paths(content, folder_name)
    if offenders:
        return ValidationResult(False, (
            f"SKILL.md:{offenders[0]}: runnable command anchored at the skill's own folder "
            f"('[skills/]{folder_name}/scripts/...') breaks in an installed plugin -- use a bare "
            f"scripts/... path, or mark a deliberate example with '{SELF_PATH_ALLOW_MARKER}'"))

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
            ref_text = ref.read_text(encoding="utf-8")  # newline-normalized by text mode, like the body
            ref_chars = len(ref_text)
            rel = ref.relative_to(skill_path)
            if contains_emoji(ref_text):
                return ValidationResult(False, f"Reference {rel} contains emoji characters (emojis are prohibited)")
            if ref_chars > REFERENCE_MAX_CHARS:
                return ValidationResult(False, f"Reference {rel} exceeds {REFERENCE_MAX_CHARS} chars ({ref_chars} chars)")
            if ref_chars > REFERENCE_TOC_THRESHOLD and not TOC_RE.search(ref_text):
                return ValidationResult(False, f"Reference {rel} has {ref_chars} chars (>{REFERENCE_TOC_THRESHOLD}). Add '## Table of Contents'")
            ref_offenders = find_self_referential_script_paths(ref_text, folder_name)
            if ref_offenders:
                return ValidationResult(False, (
                    f"Reference {rel}:{ref_offenders[0]}: runnable command anchored at the "
                    f"skill's own folder ('[skills/]{folder_name}/scripts/...') breaks in an "
                    f"installed plugin -- use a bare scripts/... path, or mark a deliberate "
                    f"example with '{SELF_PATH_ALLOW_MARKER}'"))

    # R7: evals/evals.json shape, when present (skill-creator schema; ADR 0013)
    evals_error = validate_evals_json(skill_path, folder_name)
    if evals_error:
        return ValidationResult(False, evals_error)

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

Evals (evals/evals.json, optional):
  - skill-creator schema: skill_name matches folder; unique integer ids;
    non-empty prompt/expected_output; non-empty expectations array

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
