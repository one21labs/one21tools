#!/usr/bin/env python3
"""
Compare P&ID extracted tags against SSoT instrument/equipment lists.

Finds:
- Tags in P&ID but not in instrument list (potentially undocumented)
- Tags in instrument list but not in P&ID (potentially missing from drawing)
- Tag format inconsistencies

Usage:
    python compare_pid_to_ssot.py pid_tags.csv instruments.csv
    python compare_pid_to_ssot.py pid_tags.csv instruments.csv -o discrepancies.csv
    python compare_pid_to_ssot.py pid_tags.csv instruments.csv --pid-column tag --ssot-column "Tag No"
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


@dataclass
class Discrepancy:
    """Represents a discrepancy between P&ID and SSoT."""
    tag: str
    issue_type: str  # in_pid_not_ssot, in_ssot_not_pid, format_mismatch
    pid_source: str  # filename where tag appears
    ssot_source: str  # SSoT filename
    pid_row: int = 0  # row number in P&ID file (0 if not found)
    ssot_row: int = 0  # row number in SSoT file
    details: str = ""
    severity: str = "warning"  # error, warning, info
    
    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "tag": self.tag,
            "issue_type": self.issue_type,
            "pid_source": self.pid_source,
            "pid_row": self.pid_row if self.pid_row > 0 else "",
            "ssot_source": self.ssot_source,
            "ssot_row": self.ssot_row if self.ssot_row > 0 else "",
            "details": self.details,
        }


def normalize_tag(tag: str) -> str:
    """Normalize tag for comparison."""
    if not tag:
        return ""
    
    # Uppercase
    tag = str(tag).upper().strip()
    
    # Standardize separators to hyphen
    tag = re.sub(r'[-_\s]+', '-', tag)
    
    # Remove trailing/leading hyphens
    tag = tag.strip('-')
    
    return tag


def load_tags_from_csv(
    filepath: Path, 
    tag_column: str = "tag",
    source_column: Optional[str] = None,
) -> dict[str, dict]:
    """
    Load tags from CSV file.
    Returns dict of {normalized_tag: {original_tag, source, row_num, row_data}}
    Row numbers are 1-indexed (header is row 1, data starts at row 2).
    """
    tags = {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Find tag column (case-insensitive)
        fieldnames = reader.fieldnames or []
        actual_tag_col = None
        for field in fieldnames:
            if field.lower() == tag_column.lower():
                actual_tag_col = field
                break
        
        if not actual_tag_col:
            # Try common variations
            for field in fieldnames:
                if any(v in field.lower() for v in ['tag', 'item', 'inst']):
                    actual_tag_col = field
                    break
        
        if not actual_tag_col:
            raise ValueError(f"Could not find tag column '{tag_column}' in {filepath}")
        
        for row_num, row in enumerate(reader, start=2):  # Data starts at row 2
            original_tag = row.get(actual_tag_col, "").strip()
            if not original_tag:
                continue
            
            normalized = normalize_tag(original_tag)
            source = row.get(source_column, filepath.name) if source_column else filepath.name
            
            tags[normalized] = {
                "original": original_tag,
                "source": source,
                "row_num": row_num,
                "row": row,
            }
    
    return tags


def load_tags_from_yaml(filepath: Path, tag_key: str = "tag") -> dict[str, dict]:
    """Load tags from YAML file with row tracking."""
    if not YAML_AVAILABLE:
        raise ImportError("PyYAML required for YAML files")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    tags = {}
    
    # Handle nested structure
    if isinstance(data, dict) and "instruments" in data:
        items = data["instruments"]
    elif isinstance(data, list):
        items = data
    else:
        items = []
    
    for idx, item in enumerate(items, start=1):
        if isinstance(item, dict) and tag_key in item:
            original_tag = str(item[tag_key]).strip()
            normalized = normalize_tag(original_tag)
            tags[normalized] = {
                "original": original_tag,
                "source": filepath.name,
                "row_num": idx,
                "row": item,
            }
    
    return tags


def load_file(filepath: Path, tag_column: str = "tag") -> dict[str, dict]:
    """Load tags from CSV or YAML file."""
    suffix = filepath.suffix.lower()
    
    if suffix == '.csv':
        return load_tags_from_csv(filepath, tag_column)
    elif suffix in ['.yaml', '.yml']:
        return load_tags_from_yaml(filepath, tag_column)
    else:
        # Try CSV
        return load_tags_from_csv(filepath, tag_column)


def compare_tags(
    pid_tags: dict[str, dict],
    ssot_tags: dict[str, dict],
    pid_source: str,
    ssot_source: str,
) -> list[Discrepancy]:
    """Compare P&ID tags against SSoT tags."""
    discrepancies = []
    
    # Tags in P&ID but not in SSoT
    for normalized, pid_info in pid_tags.items():
        if normalized not in ssot_tags:
            # Check for close matches (format variations)
            close_match = find_close_match(normalized, ssot_tags)
            
            if close_match:
                ssot_match = ssot_tags[close_match]
                discrepancies.append(Discrepancy(
                    tag=pid_info["original"],
                    issue_type="format_mismatch",
                    pid_source=pid_info.get("source", pid_source),
                    ssot_source=ssot_source,
                    pid_row=pid_info.get("row_num", 0),
                    ssot_row=ssot_match.get("row_num", 0),
                    details=f"P&ID has '{pid_info['original']}', SSoT has '{ssot_match['original']}'",
                    severity="warning",
                ))
            else:
                discrepancies.append(Discrepancy(
                    tag=pid_info["original"],
                    issue_type="in_pid_not_ssot",
                    pid_source=pid_info.get("source", pid_source),
                    ssot_source=ssot_source,
                    pid_row=pid_info.get("row_num", 0),
                    ssot_row=0,
                    details="Tag appears on P&ID but not in instrument list",
                    severity="warning",
                ))
    
    # Tags in SSoT but not in P&ID
    for normalized, ssot_info in ssot_tags.items():
        if normalized not in pid_tags:
            # Check if close match already found
            close_match = find_close_match(normalized, pid_tags)
            
            if not close_match:  # Don't duplicate format mismatch warnings
                discrepancies.append(Discrepancy(
                    tag=ssot_info["original"],
                    issue_type="in_ssot_not_pid",
                    pid_source=pid_source,
                    ssot_source=ssot_source,
                    pid_row=0,
                    ssot_row=ssot_info.get("row_num", 0),
                    details="Tag in instrument list but not found on P&ID",
                    severity="warning",
                ))
    
    return discrepancies


def find_close_match(tag: str, tag_dict: dict[str, dict]) -> Optional[str]:
    """Find close match for tag (handles minor format variations)."""
    # Try without suffix letter
    base = re.sub(r'[A-Z]$', '', tag)
    if base != tag and base in tag_dict:
        return base
    
    # Try with common suffixes
    for suffix in ['A', 'B', 'C', '1', '2', '3']:
        with_suffix = tag + suffix
        if with_suffix in tag_dict:
            return with_suffix
    
    # Try number variations (001 vs 1)
    match = re.match(r'^([A-Z]+)-?0*(\d+)([A-Z]?)$', tag)
    if match:
        prefix, num, suffix = match.groups()
        # Try with leading zeros
        for width in [3, 4]:
            padded = f"{prefix}-{num.zfill(width)}{suffix}"
            if padded in tag_dict and padded != tag:
                return padded
        # Try without leading zeros
        stripped = f"{prefix}-{num.lstrip('0')}{suffix}"
        if stripped in tag_dict and stripped != tag:
            return stripped
    
    return None


def print_discrepancies(discrepancies: list[Discrepancy]):
    """Print discrepancy summary with row locations."""
    if not discrepancies:
        print("\n[OK] No discrepancies found - P&ID matches SSoT")
        return

    in_pid = [d for d in discrepancies if d.issue_type == "in_pid_not_ssot"]
    in_ssot = [d for d in discrepancies if d.issue_type == "in_ssot_not_pid"]
    format_issues = [d for d in discrepancies if d.issue_type == "format_mismatch"]

    print(f"\n=== P&ID vs SSoT Comparison ===")
    print(f"Total discrepancies: {len(discrepancies)}")
    print(f"  Tags in P&ID not in SSoT: {len(in_pid)}")
    print(f"  Tags in SSoT not in P&ID: {len(in_ssot)}")
    print(f"  Format mismatches: {len(format_issues)}")

    def format_loc(d: Discrepancy) -> str:
        parts = []
        if d.pid_row:
            parts.append(f"{d.pid_source}:row {d.pid_row}")
        if d.ssot_row:
            parts.append(f"{d.ssot_source}:row {d.ssot_row}")
        return " | ".join(parts) if parts else d.pid_source

    if in_pid:
        print(f"\n[PID-ONLY] In P&ID but not in SSoT ({len(in_pid)}):")
        for d in sorted(in_pid, key=lambda x: x.tag)[:15]:
            print(f"  {d.tag} ({format_loc(d)})")
        if len(in_pid) > 15:
            print(f"  ... and {len(in_pid) - 15} more")

    if in_ssot:
        print(f"\n[SSOT-ONLY] In SSoT but not in P&ID ({len(in_ssot)}):")
        for d in sorted(in_ssot, key=lambda x: x.tag)[:15]:
            loc = f"{d.ssot_source}:row {d.ssot_row}" if d.ssot_row else d.ssot_source
            print(f"  {d.tag} ({loc})")
        if len(in_ssot) > 15:
            print(f"  ... and {len(in_ssot) - 15} more")

    if format_issues:
        print(f"\n[WARN] Format mismatches ({len(format_issues)}):")
        for d in sorted(format_issues, key=lambda x: x.tag)[:10]:
            print(f"  {d.details}")
        if len(format_issues) > 10:
            print(f"  ... and {len(format_issues) - 10} more")


def write_csv(discrepancies: list[Discrepancy], output_path: Path):
    """Write discrepancies to CSV with full location information."""
    fieldnames = [
        "severity", "tag", "issue_type", 
        "pid_source", "pid_row", 
        "ssot_source", "ssot_row", 
        "details"
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for d in discrepancies:
            writer.writerow(d.to_dict())


def main():
    parser = argparse.ArgumentParser(
        description="Compare P&ID tags against SSoT instrument list",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python compare_pid_to_ssot.py pid_tags.csv instruments.csv
    python compare_pid_to_ssot.py extracted_tags.csv setpoints.csv -o discrepancies.csv
    python compare_pid_to_ssot.py tags.csv "Instrument List.csv" --ssot-column "Tag No"
    
Workflow:
    1. Extract tags from DXF: python extract_dxf_tags.py drawing.dxf -o pid_tags.csv
    2. Compare to SSoT: python compare_pid_to_ssot.py pid_tags.csv instruments.csv
        """
    )
    parser.add_argument("pid_tags", help="CSV/YAML with tags extracted from P&ID")
    parser.add_argument("ssot", help="CSV/YAML with SSoT instrument list")
    parser.add_argument("-o", "--output", help="Output discrepancies to CSV")
    parser.add_argument("--pid-column", default="tag", help="Column name for tags in P&ID file")
    parser.add_argument("--ssot-column", default="tag", help="Column name for tags in SSoT file")
    parser.add_argument("--instruments-only", action="store_true",
                        help="Only compare instrument tags (exclude equipment)")
    
    args = parser.parse_args()
    
    pid_path = Path(args.pid_tags)
    ssot_path = Path(args.ssot)
    
    if not pid_path.exists():
        sys.exit(f"Error: P&ID tags file not found: {pid_path}")
    if not ssot_path.exists():
        sys.exit(f"Error: SSoT file not found: {ssot_path}")
    
    # Load files
    print(f"Loading P&ID tags from {pid_path}...")
    pid_tags = load_file(pid_path, args.pid_column)
    print(f"  Loaded {len(pid_tags)} tags")
    
    print(f"Loading SSoT from {ssot_path}...")
    ssot_tags = load_file(ssot_path, args.ssot_column)
    print(f"  Loaded {len(ssot_tags)} tags")
    
    # Filter to instruments only if requested
    if args.instruments_only:
        pid_tags = {k: v for k, v in pid_tags.items() 
                    if len(re.match(r'^[A-Z]+', k).group()) >= 2}
        ssot_tags = {k: v for k, v in ssot_tags.items() 
                     if len(re.match(r'^[A-Z]+', k).group()) >= 2}
    
    # Compare
    discrepancies = compare_tags(
        pid_tags, ssot_tags,
        pid_source=pid_path.name,
        ssot_source=ssot_path.name,
    )
    
    # Output
    print_discrepancies(discrepancies)
    
    if args.output:
        output_path = Path(args.output)
        write_csv(discrepancies, output_path)
        print(f"\nWrote discrepancies to {output_path}")
    
    # Exit with error if discrepancies found
    if discrepancies:
        sys.exit(1)


if __name__ == "__main__":
    main()
