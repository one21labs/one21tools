#!/usr/bin/env python3
"""
Cross-check consistency between SSoT files.

Compares:
- Instrument list ↔ Setpoint list (tag presence, value consistency)
- Instrument list ↔ IO list (tag presence, IO type consistency)
- Instrument list ↔ Control narrative (tag presence)
- Any two files sharing common columns

Usage:
    python validate_consistency.py instruments.csv setpoints.csv
    python validate_consistency.py instruments.csv io_list.csv --key tag
    python validate_consistency.py instruments.csv setpoints.csv -o discrepancies.csv
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class Discrepancy:
    """Represents a single discrepancy between files."""
    tag: str
    field: str
    issue_type: str  # missing_in_file1, missing_in_file2, value_mismatch, unit_mismatch
    file1_name: str = ""
    file2_name: str = ""
    file1_row: int = 0  # 1-indexed row number (0 = not found)
    file2_row: int = 0
    file1_value: str = ""
    file2_value: str = ""
    severity: str = "warning"  # info, warning, error
    
    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "tag": self.tag,
            "field": self.field,
            "issue_type": self.issue_type,
            "file1_name": self.file1_name,
            "file1_row": self.file1_row if self.file1_row > 0 else "",
            "file1_value": self.file1_value,
            "file2_name": self.file2_name,
            "file2_row": self.file2_row if self.file2_row > 0 else "",
            "file2_value": self.file2_value,
        }


def load_file(path: Path) -> list[dict]:
    """
    Load CSV or YAML file into list of dicts.
    Adds _row_num field (1-indexed, header is row 1, data starts at row 2).
    """
    suffix = path.suffix.lower()
    
    if suffix == '.csv':
        with open(path, 'r', encoding='utf-8') as f:
            records = []
            for row_num, row in enumerate(csv.DictReader(f), start=2):  # Header is row 1
                row['_row_num'] = row_num
                row['_source_file'] = path.name
                records.append(row)
            return records
    
    elif suffix in ['.yaml', '.yml']:
        if not YAML_AVAILABLE:
            sys.exit("Error: PyYAML required for YAML files. Install with: pip install pyyaml")
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            # Handle nested structure
            if isinstance(data, dict) and "instruments" in data:
                items = data["instruments"]
            elif isinstance(data, list):
                items = data
            else:
                sys.exit(f"Error: Unexpected YAML structure in {path}")
            # Add row tracking (approximate for YAML)
            for i, item in enumerate(items, start=1):
                item['_row_num'] = i
                item['_source_file'] = path.name
            return items
    
    elif suffix == '.json':
        import json
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and "instruments" in data:
                items = data["instruments"]
            else:
                items = data
            for i, item in enumerate(items, start=1):
                item['_row_num'] = i
                item['_source_file'] = path.name
            return items
    
    else:
        sys.exit(f"Error: Unsupported file format: {suffix}")


def normalize_value(value) -> str:
    """Normalize a value for comparison."""
    if value is None:
        return ""
    
    # Convert to string and clean
    s = str(value).strip().lower()
    
    # Normalize numeric values
    try:
        # Try to parse as float and round for comparison
        f = float(s.replace(',', ''))
        # Return with reasonable precision
        if f == int(f):
            return str(int(f))
        return f"{f:.2f}".rstrip('0').rstrip('.')
    except (ValueError, TypeError):
        pass
    
    return s


def normalize_unit(unit: str) -> str:
    """Normalize unit for comparison."""
    if not unit:
        return ""
    
    unit = str(unit).strip().lower()
    
    # Common normalizations
    normalizations = {
        "psig": ["psi g", "psi(g)", "psig"],
        "kpag": ["kpa g", "kpa(g)", "kpag"],
        "degc": ["deg c", "°c", "c"],
        "degf": ["deg f", "°f", "f"],
        "%": ["percent", "pct", "%"],
    }
    
    for canonical, aliases in normalizations.items():
        if unit in aliases:
            return canonical
    
    return unit


def find_common_columns(records1: list[dict], records2: list[dict]) -> list[str]:
    """Find columns present in both record sets."""
    if not records1 or not records2:
        return []
    
    cols1 = set(records1[0].keys())
    cols2 = set(records2[0].keys())
    
    return list(cols1.intersection(cols2))


def compare_files(
    records1: list[dict], 
    records2: list[dict], 
    key_column: str = "tag",
    compare_columns: Optional[list[str]] = None,
    file1_name: str = "file1",
    file2_name: str = "file2",
) -> list[Discrepancy]:
    """
    Compare two record sets.
    Returns list of discrepancies with row numbers and file names.
    """
    discrepancies = []
    
    # Build lookup by key, preserving row info
    lookup1 = {}
    for r in records1:
        if r.get(key_column):
            key = normalize_value(r.get(key_column))
            lookup1[key] = r
    
    lookup2 = {}
    for r in records2:
        if r.get(key_column):
            key = normalize_value(r.get(key_column))
            lookup2[key] = r
    
    all_keys = set(lookup1.keys()).union(set(lookup2.keys()))
    
    # Determine columns to compare (exclude internal tracking fields)
    internal_fields = {'_row_num', '_source_file'}
    if compare_columns:
        cols_to_check = [c for c in compare_columns if c not in internal_fields]
    else:
        cols_to_check = find_common_columns(records1, records2)
        cols_to_check = [c for c in cols_to_check if c not in internal_fields]
        # Remove the key column
        if key_column in cols_to_check:
            cols_to_check.remove(key_column)
    
    for key in sorted(all_keys):
        # Check presence
        in_file1 = key in lookup1
        in_file2 = key in lookup2
        
        if not in_file1:
            r2 = lookup2[key]
            discrepancies.append(Discrepancy(
                tag=key,
                field=key_column,
                issue_type="missing_in_file1",
                file1_name=file1_name,
                file2_name=file2_name,
                file1_row=0,
                file2_row=r2.get('_row_num', 0),
                file2_value=key,
                severity="warning",
            ))
            continue
        
        if not in_file2:
            r1 = lookup1[key]
            discrepancies.append(Discrepancy(
                tag=key,
                field=key_column,
                issue_type="missing_in_file2",
                file1_name=file1_name,
                file2_name=file2_name,
                file1_row=r1.get('_row_num', 0),
                file2_row=0,
                file1_value=key,
                severity="warning",
            ))
            continue
        
        # Compare common columns
        record1 = lookup1[key]
        record2 = lookup2[key]
        row1 = record1.get('_row_num', 0)
        row2 = record2.get('_row_num', 0)
        
        for col in cols_to_check:
            val1 = record1.get(col)
            val2 = record2.get(col)
            
            norm1 = normalize_value(val1)
            norm2 = normalize_value(val2)
            
            # Skip if both empty
            if not norm1 and not norm2:
                continue
            
            # Check for unit column special handling
            if col in ["unit", "units", "eng_unit"]:
                unit1 = normalize_unit(val1 or "")
                unit2 = normalize_unit(val2 or "")
                if unit1 and unit2 and unit1 != unit2:
                    discrepancies.append(Discrepancy(
                        tag=key,
                        field=col,
                        issue_type="unit_mismatch",
                        file1_name=file1_name,
                        file2_name=file2_name,
                        file1_row=row1,
                        file2_row=row2,
                        file1_value=str(val1),
                        file2_value=str(val2),
                        severity="error",
                    ))
            elif norm1 != norm2:
                # Value mismatch
                severity = "error" if col in ["setpoint", "alarm_high", "alarm_low", "range_high", "range_low"] else "warning"
                discrepancies.append(Discrepancy(
                    tag=key,
                    field=col,
                    issue_type="value_mismatch",
                    file1_name=file1_name,
                    file2_name=file2_name,
                    file1_row=row1,
                    file2_row=row2,
                    file1_value=str(val1) if val1 else "(empty)",
                    file2_value=str(val2) if val2 else "(empty)",
                    severity=severity,
                ))
    
    return discrepancies


def print_discrepancies(discrepancies: list[Discrepancy], file1_name: str, file2_name: str):
    """Print discrepancies in a readable format."""
    if not discrepancies:
        print("\n[OK] No discrepancies found!")
        return

    # Group by severity
    errors = [d for d in discrepancies if d.severity == "error"]
    warnings = [d for d in discrepancies if d.severity == "warning"]
    infos = [d for d in discrepancies if d.severity == "info"]

    print(f"\n=== Consistency Check Results ===")
    print(f"Comparing: {file1_name} <-> {file2_name}")
    print(f"Total discrepancies: {len(discrepancies)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    print(f"  Info: {len(infos)}")

    def format_location(d: Discrepancy) -> str:
        """Format row location info."""
        parts = []
        if d.file1_row:
            parts.append(f"{d.file1_name}:row {d.file1_row}")
        if d.file2_row:
            parts.append(f"{d.file2_name}:row {d.file2_row}")
        return " | ".join(parts) if parts else ""

    # Print errors first
    if errors:
        print(f"\n[ERROR] ERRORS ({len(errors)}):")
        for d in errors[:20]:
            loc = format_location(d)
            if "missing" in d.issue_type:
                print(f"  [{d.tag}] {d.issue_type} ({loc})")
            else:
                print(f"  [{d.tag}] {d.field}: '{d.file1_value}' vs '{d.file2_value}' ({loc})")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors")

    if warnings:
        print(f"\n[WARN] WARNINGS ({len(warnings)}):")
        for d in warnings[:20]:
            loc = format_location(d)
            if "missing" in d.issue_type:
                print(f"  [{d.tag}] {d.issue_type} ({loc})")
            else:
                print(f"  [{d.tag}] {d.field}: '{d.file1_value}' vs '{d.file2_value}' ({loc})")
        if len(warnings) > 20:
            print(f"  ... and {len(warnings) - 20} more warnings")


def write_discrepancies(discrepancies: list[Discrepancy], output_path: Path):
    """Write discrepancies to CSV with full location information."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            "severity", "tag", "field", "issue_type",
            "file1_name", "file1_row", "file1_value",
            "file2_name", "file2_row", "file2_value",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for d in discrepancies:
            writer.writerow(d.to_dict())


def main():
    parser = argparse.ArgumentParser(
        description="Cross-check consistency between SSoT files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python validate_consistency.py instruments.csv setpoints.csv
    python validate_consistency.py instruments.csv io_list.csv --key tag
    python validate_consistency.py inst.yaml setpoints.yaml -o discrepancies.csv
    python validate_consistency.py file1.csv file2.csv --columns setpoint,alarm_high,alarm_low
        """
    )
    parser.add_argument("file1", help="First file (CSV, YAML, or JSON)")
    parser.add_argument("file2", help="Second file (CSV, YAML, or JSON)")
    parser.add_argument("-k", "--key", default="tag", help="Key column for matching (default: tag)")
    parser.add_argument("-c", "--columns", help="Specific columns to compare (comma-separated)")
    parser.add_argument("-o", "--output", help="Output discrepancies to CSV file")
    parser.add_argument("--strict", action="store_true", help="Treat all discrepancies as errors")
    
    args = parser.parse_args()
    
    file1_path = Path(args.file1)
    file2_path = Path(args.file2)
    
    if not file1_path.exists():
        sys.exit(f"Error: File not found: {file1_path}")
    if not file2_path.exists():
        sys.exit(f"Error: File not found: {file2_path}")
    
    # Load files
    print(f"Loading {file1_path.name}...")
    records1 = load_file(file1_path)
    print(f"  Loaded {len(records1)} records")
    
    print(f"Loading {file2_path.name}...")
    records2 = load_file(file2_path)
    print(f"  Loaded {len(records2)} records")
    
    # Parse columns if specified
    compare_columns = None
    if args.columns:
        compare_columns = [c.strip() for c in args.columns.split(",")]
    
    # Compare
    discrepancies = compare_files(
        records1, records2,
        key_column=args.key,
        compare_columns=compare_columns,
        file1_name=file1_path.name,
        file2_name=file2_path.name,
    )
    
    # Upgrade severity if strict mode
    if args.strict:
        for d in discrepancies:
            d.severity = "error"
    
    # Output results
    print_discrepancies(discrepancies, file1_path.name, file2_path.name)
    
    if args.output:
        output_path = Path(args.output)
        write_discrepancies(discrepancies, output_path)
        print(f"\nWrote discrepancies to {output_path}")
    
    # Exit with error code if errors found
    errors = [d for d in discrepancies if d.severity == "error"]
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
