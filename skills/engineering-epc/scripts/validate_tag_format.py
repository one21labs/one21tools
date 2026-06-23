#!/usr/bin/env python3
r"""
Validate instrument tag naming conventions.

Checks:
- Tag format matches expected pattern (configurable regex)
- Tag prefixes follow ISA S5.1 conventions
- Sequence numbers are valid
- Suffixes are valid

Usage:
    python validate_tag_format.py instruments.csv
    python validate_tag_format.py instruments.csv --pattern "[A-Z]{2,4}-\d{3}[A-Z]?"
    python validate_tag_format.py instruments.csv --column "Instrument Tag"
"""

import argparse
import csv
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# ISA S5.1 first letter meanings (measured/initiating variable)
ISA_FIRST_LETTER = {
    "A": "Analysis",
    "B": "Burner/Combustion",
    "C": "User's Choice",
    "D": "User's Choice",
    "E": "Voltage",
    "F": "Flow",
    "G": "User's Choice",
    "H": "Hand",
    "I": "Current",
    "J": "Power",
    "K": "Time/Schedule",
    "L": "Level",
    "M": "User's Choice",
    "N": "User's Choice",
    "O": "User's Choice",
    "P": "Pressure/Vacuum",
    "Q": "Quantity",
    "R": "Radiation",
    "S": "Speed/Frequency",
    "T": "Temperature",
    "U": "Multivariable",
    "V": "Vibration",
    "W": "Weight/Force",
    "X": "Unclassified",
    "Y": "Event/State",
    "Z": "Position",
}

# ISA S5.1 succeeding letters (modifier/readout/output function)
ISA_SUCCEEDING_LETTERS = {
    "A": "Alarm",
    "B": "User's Choice",
    "C": "Controller",
    "D": "Differential",
    "E": "Element (Primary)",
    "F": "Ratio",
    "G": "Glass/Gauge",
    "H": "High",
    "I": "Indicate",
    "J": "Scan",
    "K": "Control Station",
    "L": "Low/Light",
    "M": "Middle/Intermediate",
    "N": "User's Choice",
    "O": "Orifice",
    "P": "Point",
    "Q": "Integrate/Totalize",
    "R": "Record",
    "S": "Switch/Safety",
    "T": "Transmit",
    "U": "Multifunction",
    "V": "Valve",
    "W": "Well",
    "X": "Unclassified",
    "Y": "Relay/Compute",
    "Z": "Driver/Actuator",
}

# Common instrument type patterns
COMMON_TAG_PATTERNS = {
    "standard": r"^[A-Z]{2,4}-\d{3,}[A-Z]?$",  # FIC-101, PT-101A
    "with_area": r"^[A-Z]{2,4}-\d{1,3}-\d{3,}[A-Z]?$",  # FIC-100-101
    "unit_area": r"^\d{2,3}-[A-Z]{2,4}-\d{3,}[A-Z]?$",  # 100-FIC-101
}


@dataclass
class TagIssue:
    """Represents a tag validation issue."""
    tag: str
    issue_type: str
    message: str
    source_file: str = ""
    row_num: int = 0  # 1-indexed row number
    severity: str = "warning"  # info, warning, error
    
    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "tag": self.tag,
            "source_file": self.source_file,
            "row_num": self.row_num if self.row_num > 0 else "",
            "issue_type": self.issue_type,
            "message": self.message,
        }


def parse_tag(tag: str) -> Optional[dict]:
    """
    Parse an instrument tag into components.
    Returns dict with prefix, number, suffix or None if unparseable.
    """
    # Try standard pattern: XX-NNN or XXX-NNNA
    match = re.match(r'^([A-Z]{2,4})-(\d+)([A-Z])?$', tag)
    if match:
        return {
            "prefix": match.group(1),
            "number": match.group(2),
            "suffix": match.group(3) or "",
            "pattern": "standard",
        }
    
    # Try with area: XX-AAA-NNN
    match = re.match(r'^([A-Z]{2,4})-(\d{1,3})-(\d+)([A-Z])?$', tag)
    if match:
        return {
            "prefix": match.group(1),
            "area": match.group(2),
            "number": match.group(3),
            "suffix": match.group(4) or "",
            "pattern": "with_area",
        }
    
    # Try unit-first: AAA-XX-NNN
    match = re.match(r'^(\d{2,3})-([A-Z]{2,4})-(\d+)([A-Z])?$', tag)
    if match:
        return {
            "area": match.group(1),
            "prefix": match.group(2),
            "number": match.group(3),
            "suffix": match.group(4) or "",
            "pattern": "unit_area",
        }
    
    return None


def validate_isa_prefix(prefix: str) -> list[TagIssue]:
    """Validate prefix against ISA S5.1 conventions."""
    issues = []
    
    if not prefix:
        return issues
    
    # First letter should be in ISA first letter table
    first = prefix[0]
    if first not in ISA_FIRST_LETTER:
        issues.append(TagIssue(
            tag=prefix,
            issue_type="invalid_first_letter",
            message=f"First letter '{first}' not in ISA S5.1 table",
            severity="warning",
        ))
    
    # Remaining letters should be in succeeding letters table
    for letter in prefix[1:]:
        if letter not in ISA_SUCCEEDING_LETTERS:
            issues.append(TagIssue(
                tag=prefix,
                issue_type="invalid_succeeding_letter",
                message=f"Succeeding letter '{letter}' not in ISA S5.1 table",
                severity="info",
            ))
    
    return issues


def validate_tag(tag: str, pattern: Optional[str] = None) -> list[TagIssue]:
    """Validate a single tag."""
    issues = []
    tag = tag.strip().upper()
    
    if not tag:
        return issues
    
    # Check against custom pattern if provided
    if pattern:
        if not re.match(pattern, tag):
            issues.append(TagIssue(
                tag=tag,
                issue_type="pattern_mismatch",
                message=f"Does not match pattern: {pattern}",
                severity="error",
            ))
            return issues
    
    # Try to parse the tag
    parsed = parse_tag(tag)
    
    if not parsed:
        issues.append(TagIssue(
            tag=tag,
            issue_type="unparseable",
            message="Could not parse tag format",
            severity="error",
        ))
        return issues
    
    # Validate ISA prefix
    issues.extend(validate_isa_prefix(parsed["prefix"]))
    
    # Check for common issues
    
    # Leading zeros in number
    number = parsed.get("number", "")
    if number.startswith("0") and len(number) > 3:
        issues.append(TagIssue(
            tag=tag,
            issue_type="leading_zeros",
            message=f"Number has unnecessary leading zeros: {number}",
            severity="info",
        ))
    
    # Suffix validation (should be A-Z, not numbers)
    suffix = parsed.get("suffix", "")
    if suffix and not suffix.isalpha():
        issues.append(TagIssue(
            tag=tag,
            issue_type="invalid_suffix",
            message=f"Suffix should be a letter, not '{suffix}'",
            severity="warning",
        ))
    
    return issues


def load_tags(path: Path, column: str = "tag") -> list[tuple[str, int]]:
    """
    Load tags from CSV or YAML file.
    Returns list of (tag, row_number) tuples.
    Row numbers are 1-indexed (header is row 1 for CSV).
    """
    suffix = path.suffix.lower()
    tags = []
    
    if suffix == '.csv':
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Find the tag column (case-insensitive)
            actual_column = column
            if reader.fieldnames:
                for field in reader.fieldnames:
                    if field.lower() == column.lower():
                        actual_column = field
                        break
            
            for row_num, row in enumerate(reader, start=2):  # Data starts at row 2
                tag = row.get(actual_column, "")
                if tag:
                    tags.append((tag.strip(), row_num))
    
    elif suffix in ['.yaml', '.yml']:
        if not YAML_AVAILABLE:
            sys.exit("Error: PyYAML required. Install with: pip install pyyaml")
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if isinstance(data, dict) and "instruments" in data:
                data = data["instruments"]
            for idx, item in enumerate(data, start=1):
                tag = item.get(column, "")
                if tag:
                    tags.append((str(tag).strip(), idx))
    
    else:
        sys.exit(f"Error: Unsupported file format: {suffix}")
    
    return tags


def print_issues(issues: list[TagIssue], verbose: bool = False):
    """Print validation issues."""
    if not issues:
        print("\n[OK] All tags valid!")
        return

    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    infos = [i for i in issues if i.severity == "info"]

    print(f"\n=== Tag Validation Results ===")
    print(f"Total issues: {len(issues)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    print(f"  Info: {len(infos)}")

    def format_location(issue: TagIssue) -> str:
        if issue.source_file and issue.row_num:
            return f" ({issue.source_file}:row {issue.row_num})"
        elif issue.row_num:
            return f" (row {issue.row_num})"
        return ""

    if errors:
        print(f"\n[ERROR] ERRORS ({len(errors)}):")
        for issue in errors[:20]:
            loc = format_location(issue)
            print(f"  [{issue.tag}] {issue.message}{loc}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more")

    if warnings:
        print(f"\n[WARN] WARNINGS ({len(warnings)}):")
        for issue in warnings[:20]:
            loc = format_location(issue)
            print(f"  [{issue.tag}] {issue.message}{loc}")
        if len(warnings) > 20:
            print(f"  ... and {len(warnings) - 20} more")

    if verbose and infos:
        print(f"\n[INFO] INFO ({len(infos)}):")
        for issue in infos[:10]:
            print(f"  [{issue.tag}] {issue.message}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate instrument tag naming conventions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python validate_tag_format.py instruments.csv
    python validate_tag_format.py instruments.csv --pattern "^[A-Z]{2,4}-\\d{3}[A-Z]?$"
    python validate_tag_format.py instruments.csv --column "Instrument Tag"
    python validate_tag_format.py instruments.csv -o issues.csv

Common patterns:
    Standard (FIC-101):     ^[A-Z]{2,4}-\\d{3,}[A-Z]?$
    With area (FIC-100-101): ^[A-Z]{2,4}-\\d{1,3}-\\d{3,}[A-Z]?$
    Unit first (100-FIC-101): ^\\d{2,3}-[A-Z]{2,4}-\\d{3,}[A-Z]?$
        """
    )
    parser.add_argument("input", nargs="?", help="Input file (CSV or YAML)")
    parser.add_argument("-c", "--column", default="tag", help="Column name containing tags (default: tag)")
    parser.add_argument("-p", "--pattern", help="Custom regex pattern for validation")
    parser.add_argument("-o", "--output", help="Output issues to CSV file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show all issues including info")
    parser.add_argument("--list-isa", action="store_true", help="List ISA S5.1 letter meanings")
    
    args = parser.parse_args()
    
    if args.list_isa:
        print("ISA S5.1 First Letters (Measured/Initiating Variable):")
        for letter, meaning in ISA_FIRST_LETTER.items():
            print(f"  {letter}: {meaning}")
        print("\nISA S5.1 Succeeding Letters (Modifier/Readout/Output):")
        for letter, meaning in ISA_SUCCEEDING_LETTERS.items():
            print(f"  {letter}: {meaning}")
        return
    
    if not args.input:
        parser.error("input file is required unless using --list-isa")
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        sys.exit(f"Error: File not found: {input_path}")
    
    # Load tags (now returns list of (tag, row_num) tuples)
    print(f"Loading tags from {input_path}...")
    tag_rows = load_tags(input_path, args.column)
    print(f"  Found {len(tag_rows)} tags")
    
    # Validate
    all_issues = []
    for tag, row_num in tag_rows:
        issues = validate_tag(tag, args.pattern)
        # Add source info to each issue
        for issue in issues:
            issue.source_file = input_path.name
            issue.row_num = row_num
        all_issues.extend(issues)
    
    # Print results
    print_issues(all_issues, args.verbose)
    
    # Write output if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ["severity", "tag", "source_file", "row_num", "issue_type", "message"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for issue in all_issues:
                writer.writerow(issue.to_dict())
        print(f"\nWrote issues to {output_path}")
    
    # Exit with error if errors found
    errors = [i for i in all_issues if i.severity == "error"]
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
