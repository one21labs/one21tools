#!/usr/bin/env python3
r"""
Extract instrument and equipment tags from DXF P&ID files.

Parses TEXT and MTEXT entities, filters by ISA tag patterns,
extracts drawing metadata from title blocks, and outputs 
structured CSV for comparison against instrument lists.

Features:
- Extracts instrument tags (ISA S5.1 format)
- Extracts equipment tags (V-xxx, P-xxx, etc.)
- Extracts drawing metadata (number, revision, date) from title blocks
- Supports batch processing of multiple DXF files
- Filters by layer name

Usage:
    python extract_dxf_tags.py input.dxf -o tags.csv
    python extract_dxf_tags.py *.dxf -o all_tags.csv
    python extract_dxf_tags.py input.dxf --layer INSTRUMENTS
    python extract_dxf_tags.py input.dxf --pattern "^[A-Z]{2,4}-\d{3}"
    python extract_dxf_tags.py input.dxf --show-metadata
"""

import argparse
import csv
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

try:
    import ezdxf
except ImportError:
    sys.exit("Error: ezdxf required. Install with: pip install ezdxf")


# ISA S5.1 instrument tag pattern: 2-4 letters, separator, 3+ digits, optional suffix
DEFAULT_TAG_PATTERN = r'\b([A-Z]{2,4}[-_]?\d{3,}[A-Z]?)\b'

# Equipment tag patterns (vessels, pumps, etc.)
EQUIPMENT_PATTERNS = [
    r'\b([VPCTEHKF][-_]?\d{3,}[A-Z]?)\b',  # V-101, P-101A, C-201
    r'\b(\d{2,3}[-_][VPCTEHKF][-_]?\d{3,}[A-Z]?)\b',  # 100-V-101
]

# Common layers containing instruments/equipment
INSTRUMENT_LAYERS = [
    'instruments', 'instrument', 'inst', 'instr',
    'tags', 'tag', 'text', 'annotation', 'annotations',
    'equipment', 'equip', 'process',
]

# Title block attribute tags to search for (case-insensitive)
TITLE_BLOCK_ATTRS = {
    'drawing_number': ['DWG_NO', 'DRAWING_NUMBER', 'DWG-NO', 'DWGNO', 'DWG_NUM', 
                       'DRAWING_NO', 'DOC_NO', 'DOCUMENT_NO', 'DRG_NO', 'NUMBER'],
    'revision': ['REV', 'REVISION', 'REV_NO', 'REVNO', 'REV_NUM', 'REVISION_NO'],
    'date': ['DATE', 'DWG_DATE', 'REV_DATE', 'DRAWING_DATE', 'ISSUE_DATE', 
             'REVISION_DATE', 'DATED'],
    'title': ['TITLE', 'DRAWING_TITLE', 'DWG_TITLE', 'DESCRIPTION'],
    'sheet': ['SHEET', 'SHEET_NO', 'SHEET_NUM', 'SH_NO', 'SHEET_OF'],
    'project': ['PROJECT', 'PROJECT_NO', 'PROJECT_NUM', 'JOB_NO', 'JOB'],
}

# Common title block names
TITLE_BLOCK_NAMES = [
    'title', 'titleblock', 'title_block', 'title-block',
    'border', 'a1_title', 'a0_title', 'a3_title',
    'drawing_border', 'dwg_border', 'sheet_border',
]


@dataclass
class DrawingMetadata:
    """Metadata extracted from drawing title block."""
    drawing_number: str = ""
    revision: str = ""
    date: str = ""
    title: str = ""
    sheet: str = ""
    project: str = ""
    source_file: str = ""
    extraction_method: str = ""  # 'block_attrib', 'text_pattern', 'header', 'none'
    
    def to_dict(self) -> dict:
        return {
            "drawing_number": self.drawing_number,
            "revision": self.revision,
            "date": self.date,
            "title": self.title,
            "sheet": self.sheet,
            "project": self.project,
        }


@dataclass
class ExtractedTag:
    """Represents an extracted tag from DXF."""
    tag: str
    tag_type: str  # instrument, equipment, unknown
    source_file: str
    drawing_number: str  # From title block
    drawing_revision: str  # From title block
    drawing_date: str  # From title block
    layer: str
    x: float
    y: float
    text_content: str  # full text (may include description)
    entity_type: str  # TEXT, MTEXT
    
    def to_dict(self) -> dict:
        return {
            "tag": self.tag,
            "tag_type": self.tag_type,
            "drawing_number": self.drawing_number,
            "drawing_revision": self.drawing_revision,
            "drawing_date": self.drawing_date,
            "source_file": self.source_file,
            "layer": self.layer,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "text_content": self.text_content,
            "entity_type": self.entity_type,
        }


def classify_tag(tag: str) -> str:
    """Classify tag as instrument or equipment."""
    # Equipment prefixes (single letter typically)
    equipment_prefixes = ['V', 'P', 'C', 'T', 'E', 'H', 'K', 'F', 'D', 'R', 'S']
    
    # Instrument prefixes (2+ letters, first is measured variable)
    # Per ISA S5.1: F=Flow, L=Level, P=Pressure, T=Temperature, etc.
    
    if not tag:
        return "unknown"
    
    # Extract prefix (letters before numbers)
    match = re.match(r'^([A-Z]+)', tag)
    if not match:
        return "unknown"
    
    prefix = match.group(1)
    
    # Single letter = likely equipment
    if len(prefix) == 1 and prefix in equipment_prefixes:
        return "equipment"
    
    # 2+ letters = likely instrument
    if len(prefix) >= 2:
        return "instrument"
    
    return "unknown"


def extract_drawing_metadata(doc, filepath: Path) -> DrawingMetadata:
    """
    Extract drawing metadata from DXF file.
    
    Tries multiple methods:
    1. Block attributes in title block
    2. Text patterns in lower-right area (title block location)
    3. DXF header variables
    4. Filename parsing as fallback
    """
    metadata = DrawingMetadata(source_file=filepath.name)
    
    # Method 1: Try block attributes first (most reliable)
    metadata = _extract_from_block_attribs(doc, metadata)
    if metadata.drawing_number:
        metadata.extraction_method = "block_attrib"
        return metadata
    
    # Method 2: Try text pattern matching in title block area
    metadata = _extract_from_text_patterns(doc, metadata)
    if metadata.drawing_number:
        metadata.extraction_method = "text_pattern"
        return metadata
    
    # Method 3: Try DXF header variables
    metadata = _extract_from_header(doc, metadata)
    if metadata.drawing_number:
        metadata.extraction_method = "header"
        return metadata
    
    # Method 4: Parse filename as fallback
    metadata = _extract_from_filename(filepath, metadata)
    metadata.extraction_method = "filename" if metadata.drawing_number else "none"
    
    return metadata


def _extract_from_block_attribs(doc, metadata: DrawingMetadata) -> DrawingMetadata:
    """Extract metadata from block INSERT attributes."""
    msp = doc.modelspace()
    
    # Also check paperspace layouts for title blocks
    layouts_to_check = [msp]
    try:
        for layout in doc.layouts:
            if layout.name != 'Model':
                layouts_to_check.append(layout)
    except Exception:
        pass
    
    for layout in layouts_to_check:
        # Find INSERT entities (block references)
        for insert in layout.query('INSERT'):
            block_name = insert.dxf.name.lower()
            
            # Check if this might be a title block
            is_title_block = any(tb in block_name for tb in TITLE_BLOCK_NAMES)
            
            # Also check any INSERT with attributes
            if insert.attribs:
                for attrib in insert.attribs:
                    tag_upper = attrib.dxf.tag.upper()
                    value = attrib.dxf.text.strip()
                    
                    if not value:
                        continue
                    
                    # Match against known attribute tags
                    for field_name, patterns in TITLE_BLOCK_ATTRS.items():
                        if any(p in tag_upper for p in patterns):
                            if field_name == 'drawing_number' and not metadata.drawing_number:
                                metadata.drawing_number = value
                            elif field_name == 'revision' and not metadata.revision:
                                metadata.revision = value
                            elif field_name == 'date' and not metadata.date:
                                metadata.date = _normalize_date(value)
                            elif field_name == 'title' and not metadata.title:
                                metadata.title = value[:100]  # Truncate long titles
                            elif field_name == 'sheet' and not metadata.sheet:
                                metadata.sheet = value
                            elif field_name == 'project' and not metadata.project:
                                metadata.project = value
    
    return metadata


def _extract_from_text_patterns(doc, metadata: DrawingMetadata) -> DrawingMetadata:
    """Extract metadata by pattern matching text in title block area."""
    msp = doc.modelspace()
    
    # Collect all text entities
    texts = []
    for entity in msp.query('TEXT MTEXT'):
        try:
            if entity.dxftype() == 'TEXT':
                text = entity.dxf.text
                x, y = entity.dxf.insert.x, entity.dxf.insert.y
            else:  # MTEXT
                text = entity.text
                x, y = entity.dxf.insert.x, entity.dxf.insert.y
            texts.append({'text': text, 'x': x, 'y': y})
        except Exception:
            continue
    
    if not texts:
        return metadata
    
    # Find extents to identify title block area (typically lower-right)
    max_x = max(t['x'] for t in texts) if texts else 0
    min_y = min(t['y'] for t in texts) if texts else 0
    
    # Filter to title block area (lower-right quadrant, approximate)
    title_area_texts = [t for t in texts 
                       if t['x'] > max_x * 0.6 and t['y'] < min_y + (max(t['y'] for t in texts) - min_y) * 0.3]
    
    # Drawing number patterns (common formats)
    dwg_patterns = [
        r'(\d{4,}-[A-Z]{2,4}-\d{3,}-\d{3,})',  # 2611-PROC-PID-001
        r'([A-Z]{2,4}-\d{3,}-[A-Z]?\d*)',       # PID-001-A
        r'(P&ID[- ]\d+)',                        # P&ID-001
        r'(PID[- ]\d+)',                         # PID-001
        r'(\d{6,})',                             # Long numeric
    ]
    
    # Revision patterns
    rev_patterns = [
        r'REV[ISION]*\.?\s*:?\s*([A-Z0-9]+)',
        r'R([0-9]+)',
        r'^([A-Z])$',  # Single letter revision
    ]
    
    # Date patterns
    date_patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        r'([A-Z]{3}\s+\d{1,2},?\s+\d{4})',
    ]
    
    for t in title_area_texts:
        text = t['text'].upper()
        
        # Try drawing number patterns
        if not metadata.drawing_number:
            for pattern in dwg_patterns:
                match = re.search(pattern, text)
                if match:
                    metadata.drawing_number = match.group(1)
                    break
        
        # Try revision patterns
        if not metadata.revision:
            for pattern in rev_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    metadata.revision = match.group(1)
                    break
        
        # Try date patterns
        if not metadata.date:
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    metadata.date = _normalize_date(match.group(1))
                    break
    
    return metadata


def _extract_from_header(doc, metadata: DrawingMetadata) -> DrawingMetadata:
    """Extract metadata from DXF header variables."""
    try:
        # Try custom variables first
        if hasattr(doc.header, 'custom_vars'):
            for name, value in doc.header.custom_vars:
                name_upper = name.upper()
                if 'DWG' in name_upper or 'DRAWING' in name_upper:
                    if not metadata.drawing_number:
                        metadata.drawing_number = str(value)
                elif 'REV' in name_upper:
                    if not metadata.revision:
                        metadata.revision = str(value)
        
        # Try standard header variables for dates
        if not metadata.date:
            try:
                # $TDUPDATE is Julian date of last update
                julian = doc.header.get('$TDUPDATE')
                if julian:
                    # Convert Julian to date (approximate)
                    metadata.date = "from_header"
            except Exception:
                pass
    except Exception:
        pass
    
    return metadata


def _extract_from_filename(filepath: Path, metadata: DrawingMetadata) -> DrawingMetadata:
    """Extract metadata from filename as fallback."""
    stem = filepath.stem.upper()
    
    # Common filename patterns:
    # PID-001_REV2.dxf
    # 2611-PROC-PID-001-A.dxf
    # Drawing_001_R3.dxf
    
    # Try to extract drawing number (everything before _REV or _R)
    match = re.match(r'^(.+?)(?:_REV|_R)(\d+|[A-Z]).*$', stem, re.IGNORECASE)
    if match:
        metadata.drawing_number = match.group(1).replace('_', '-')
        metadata.revision = match.group(2)
        return metadata
    
    # Try pattern with revision at end
    match = re.match(r'^(.+?)[-_]([A-Z]|\d+)$', stem)
    if match:
        # Check if last part looks like revision
        potential_rev = match.group(2)
        if len(potential_rev) <= 2:
            metadata.drawing_number = match.group(1).replace('_', '-')
            metadata.revision = potential_rev
            return metadata
    
    # Use whole filename as drawing number
    metadata.drawing_number = stem.replace('_', '-')
    
    return metadata


def _normalize_date(date_str: str) -> str:
    """Normalize date string to ISO format if possible."""
    if not date_str:
        return ""
    
    date_str = date_str.strip()
    
    # Try common formats
    formats = [
        '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d',
        '%d-%m-%Y', '%m-%d-%Y', '%Y-%m-%d',
        '%d.%m.%Y', '%m.%d.%Y',
        '%b %d, %Y', '%B %d, %Y',
        '%d %b %Y', '%d %B %Y',
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # Return as-is if can't parse
    return date_str


def extract_tags_from_text(
    text: str, 
    pattern: str = DEFAULT_TAG_PATTERN
) -> list[str]:
    """Extract all tags matching pattern from text."""
    # Normalize text
    text = text.upper().replace('\\P', ' ')  # MTEXT paragraph separator
    
    # Find all matches
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    # Normalize separators
    normalized = []
    for match in matches:
        # Standardize to hyphen separator
        tag = re.sub(r'[-_\s]', '-', match.upper())
        # Remove double hyphens
        tag = re.sub(r'-+', '-', tag)
        normalized.append(tag)
    
    return list(set(normalized))  # Remove duplicates


def get_entity_position(entity) -> tuple[float, float]:
    """Get position of TEXT or MTEXT entity."""
    try:
        if entity.dxftype() == 'TEXT':
            insert = entity.dxf.insert
            return (insert.x, insert.y)
        elif entity.dxftype() == 'MTEXT':
            insert = entity.dxf.insert
            return (insert.x, insert.y)
    except Exception:
        pass
    return (0.0, 0.0)


def extract_from_dxf(
    filepath: Path,
    pattern: str = DEFAULT_TAG_PATTERN,
    layers: Optional[list[str]] = None,
    include_equipment: bool = True,
) -> tuple[list[ExtractedTag], DrawingMetadata]:
    """
    Extract tags from a single DXF file.
    Returns tuple of (tags, metadata).
    """
    extracted = []
    metadata = DrawingMetadata(source_file=filepath.name)
    
    try:
        doc = ezdxf.readfile(str(filepath))
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return [], metadata
    
    # Extract drawing metadata first
    metadata = extract_drawing_metadata(doc, filepath)
    
    msp = doc.modelspace()
    
    # Process TEXT entities
    for entity in msp.query("TEXT"):
        layer = entity.dxf.layer.lower()
        
        # Filter by layer if specified
        if layers:
            if not any(l.lower() in layer for l in layers):
                continue
        
        text = entity.dxf.text
        tags = extract_tags_from_text(text, pattern)
        
        # Also try equipment patterns if enabled
        if include_equipment:
            for eq_pattern in EQUIPMENT_PATTERNS:
                tags.extend(extract_tags_from_text(text, eq_pattern))
        
        x, y = get_entity_position(entity)
        
        for tag in set(tags):
            extracted.append(ExtractedTag(
                tag=tag,
                tag_type=classify_tag(tag),
                source_file=filepath.name,
                drawing_number=metadata.drawing_number,
                drawing_revision=metadata.revision,
                drawing_date=metadata.date,
                layer=entity.dxf.layer,
                x=x,
                y=y,
                text_content=text.strip(),
                entity_type="TEXT",
            ))
    
    # Process MTEXT entities
    for entity in msp.query("MTEXT"):
        layer = entity.dxf.layer.lower()
        
        if layers:
            if not any(l.lower() in layer for l in layers):
                continue
        
        text = entity.text  # Use .text property for MTEXT
        tags = extract_tags_from_text(text, pattern)
        
        if include_equipment:
            for eq_pattern in EQUIPMENT_PATTERNS:
                tags.extend(extract_tags_from_text(text, eq_pattern))
        
        x, y = get_entity_position(entity)
        
        for tag in set(tags):
            extracted.append(ExtractedTag(
                tag=tag,
                tag_type=classify_tag(tag),
                source_file=filepath.name,
                drawing_number=metadata.drawing_number,
                drawing_revision=metadata.revision,
                drawing_date=metadata.date,
                layer=entity.dxf.layer,
                x=x,
                y=y,
                text_content=text.strip()[:100],  # Truncate long MTEXT
                entity_type="MTEXT",
            ))
    
    return extracted, metadata


def deduplicate_tags(tags: list[ExtractedTag]) -> list[ExtractedTag]:
    """Remove duplicate tags (same tag from same file)."""
    seen = set()
    unique = []
    
    for tag in tags:
        key = (tag.tag, tag.source_file)
        if key not in seen:
            seen.add(key)
            unique.append(tag)
    
    return unique


def write_csv(tags: list[ExtractedTag], output_path: Path):
    """Write extracted tags to CSV."""
    if not tags:
        print("Warning: No tags to write", file=sys.stderr)
        return
    
    fieldnames = ["tag", "tag_type", "source_file", "layer", "x", "y", "text_content", "entity_type"]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for tag in sorted(tags, key=lambda t: t.tag):
            writer.writerow(tag.to_dict())


def print_summary(tags: list[ExtractedTag]):
    """Print extraction summary."""
    if not tags:
        print("No tags extracted")
        return
    
    instruments = [t for t in tags if t.tag_type == "instrument"]
    equipment = [t for t in tags if t.tag_type == "equipment"]
    
    print(f"\n=== Extraction Summary ===")
    print(f"Total tags: {len(tags)}")
    print(f"  Instruments: {len(instruments)}")
    print(f"  Equipment: {len(equipment)}")
    
    # Group by file
    files = set(t.source_file for t in tags)
    print(f"Files processed: {len(files)}")
    
    # Show sample tags
    print(f"\nSample instrument tags:")
    for tag in sorted(instruments, key=lambda t: t.tag)[:10]:
        print(f"  {tag.tag}")
    
    if equipment:
        print(f"\nSample equipment tags:")
        for tag in sorted(equipment, key=lambda t: t.tag)[:10]:
            print(f"  {tag.tag}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract instrument and equipment tags from DXF P&ID files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python extract_dxf_tags.py drawing.dxf -o tags.csv
    python extract_dxf_tags.py *.dxf -o all_tags.csv
    python extract_dxf_tags.py drawing.dxf --layer INSTRUMENTS --layer TAGS
    python extract_dxf_tags.py drawing.dxf --pattern "^[A-Z]{3}-\\d{4}"
    python extract_dxf_tags.py drawing.dxf --no-equipment
    
Default tag pattern matches: FIC-101, PT-201A, LT-1001, TIC-100
Equipment pattern matches: V-101, P-201A, C-301
        """
    )
    parser.add_argument("input", nargs="+", help="Input DXF file(s)")
    parser.add_argument("-o", "--output", help="Output CSV file")
    parser.add_argument("--layer", action="append", dest="layers",
                        help="Filter by layer name (can specify multiple)")
    parser.add_argument("--pattern", default=DEFAULT_TAG_PATTERN,
                        help=f"Regex pattern for instrument tags (default: {DEFAULT_TAG_PATTERN})")
    parser.add_argument("--no-equipment", action="store_true",
                        help="Exclude equipment tags (V-xxx, P-xxx, etc.)")
    parser.add_argument("--list-layers", action="store_true",
                        help="List all layers in the DXF file(s) and exit")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose output")
    
    args = parser.parse_args()
    
    # Collect input files
    input_files = []
    for pattern in args.input:
        path = Path(pattern)
        if path.exists():
            input_files.append(path)
        else:
            # Try glob
            input_files.extend(Path('.').glob(pattern))
    
    if not input_files:
        sys.exit("Error: No input files found")
    
    # List layers mode
    if args.list_layers:
        for filepath in input_files:
            print(f"\n{filepath.name}:")
            try:
                doc = ezdxf.readfile(str(filepath))
                for layer in doc.layers:
                    # Count entities in layer
                    msp = doc.modelspace()
                    count = len(list(msp.query(f"*[layer=='{layer.dxf.name}']")))
                    print(f"  {layer.dxf.name}: {count} entities")
            except Exception as e:
                print(f"  Error: {e}")
        return
    
    # Extract tags
    all_tags = []
    for filepath in input_files:
        if args.verbose:
            print(f"Processing {filepath}...")
        
        tags = extract_from_dxf(
            filepath,
            pattern=args.pattern,
            layers=args.layers,
            include_equipment=not args.no_equipment,
        )
        all_tags.extend(tags)
        
        if args.verbose:
            print(f"  Found {len(tags)} tags")
    
    # Deduplicate
    all_tags = deduplicate_tags(all_tags)
    
    # Output
    print_summary(all_tags)
    
    if args.output:
        output_path = Path(args.output)
        write_csv(all_tags, output_path)
        print(f"\nWrote {len(all_tags)} tags to {output_path}")
    else:
        print("\nUse -o/--output to save to CSV")


if __name__ == "__main__":
    main()
