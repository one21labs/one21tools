# SSoT Normalization Workflow

Guide for normalizing messy engineering spreadsheets and documents into clean SSoT format.

## Workflow Overview

```
Input (messy xlsx/docx)
    ↓
Step 1: Claude reviews, normalizes, asks about ambiguities
    ↓
Clean intermediate CSV (normalized)
    ↓
Step 2: Scripts validate (consistency, tag format)
    ↓
Exception list (CSV/xlsx)
    ↓
Step 3: Claude generates corrected output in original format
    ↓
Output (corrected xlsx/docx matching input format)
```

## Step 1: Review & Normalize

### 1.1 Initial Assessment

Open the file and identify:
- **Structure issues**: Merged cells, multi-row headers, hidden rows/columns
- **Header issues**: Inconsistent names, abbreviations, missing headers
- **Data issues**: Mixed types, units in values, text numbers, blanks vs zeros
- **Format issues**: Highlighting, comments, conditional formatting (may carry meaning)

Ask user if unclear:
- "Row 3 has merged cells spanning A3:D3 with 'PRESSURE INSTRUMENTS'. Is this a section header to preserve as a category, or should I ignore it?"
- "Column F is labeled 'SP' - is this Setpoint or Service Point?"

### 1.2 Structure Normalization

**Merged cells** → Unmerge and fill:
- Horizontal merge: Copy value to all cells in range
- Vertical merge: Fill down to all rows in range
- Section headers in merged cells: Add a `category` or `section` column

**Multi-row headers** → Combine into single header row:
```
Before:                          After:
| Alarm    |      |              | alarm_high | alarm_low |
| High     | Low  |              
```

**Hidden rows/columns** → Unhide and review:
- May contain superseded data (ask user)
- May contain calculations (preserve or extract)

### 1.3 Header Normalization

Map to canonical names. Common mappings:

| Input Variations | Canonical |
|------------------|-----------|
| Tag, Tag No, Tag No., Tag Number, Inst Tag, Item, Item No | `tag` |
| Desc, Desc., Description, Service, Service Description | `description` |
| Type, Inst Type, Device Type | `type` |
| SP, Setpoint, Set Point, Normal, Operating | `setpoint` |
| Hi Alarm, HA, HAH, Alarm High, Hi Al | `alarm_high` |
| Lo Alarm, LA, LAL, Alarm Low, Lo Al | `alarm_low` |
| HH, HiHi, HAHH, Alarm High High, Hi Hi | `alarm_high_high` |
| LL, LoLo, LALL, Alarm Low Low, Lo Lo | `alarm_low_low` |
| Range, Span, LRV-URV | `range` (or split to `range_low`, `range_high`) |
| Unit, Units, Eng Unit, Eng Units, UOM | `unit` |
| I/O, IO, I/O Type, Signal Type | `io_type` |
| PLC Addr, I/O Address, Address | `io_address` |
| P&ID, PID, Dwg, Drawing, Drawing Ref | `pid_ref` |
| Mfr, Manufacturer, Vendor, Make | `manufacturer` |
| Notes, Remarks, Comments | `notes` |

If header is ambiguous, ask:
- "Column G is labeled 'Range'. Should I split this into `range_low` and `range_high`, or keep as single field?"

### 1.4 Data Normalization

**Text numbers → Numbers**:
- "150" → 150
- "1,234.56" → 1234.56
- "-" or "N/A" or blank → (empty)

**Units in values → Separate**:
- "150 GPM" → value: 150, unit: GPM
- "800 kPag" → value: 800, unit: kPag

**Unit standardization**:

| Input Variations | Canonical |
|------------------|-----------|
| psig, PSI G, psi(g), PSI (G) | psig |
| psia, PSI A, psi(a) | psia |
| kPag, kPa g, kPa(g), KPA G | kPag |
| kPaa, kPa a, kPa(a) | kPaa |
| degC, Deg C, °C, deg c, C | degC |
| degF, Deg F, °F, deg f, F | degF |
| %, percent, Percent, PCT | % |
| m3/h, M3/H, m³/h, CMH | m3/h |
| GPM, gpm, USGPM, gal/min | GPM |
| mm, MM, millimeter | mm |

**Boolean/status values**:
- Open, OPEN, O, 1 → OPEN
- Closed, CLOSED, C, 0 → CLOSED
- Yes, YES, Y, 1 → YES
- No, NO, N, 0 → NO

**Tag format normalization**:
- Ensure uppercase: `fic-101` → `FIC-101`
- Consistent separators: `FIC 101` or `FIC.101` → `FIC-101`
- Remove trailing/leading spaces

### 1.5 Preserve Semantic Data

Highlights, comments, and conditional formatting often carry meaning:

| Visual Indicator | Possible Meaning | Action |
|------------------|------------------|--------|
| Yellow highlight | Needs review | Add `review_flag` column |
| Red highlight | Error/issue | Add `issue_flag` column |
| Strikethrough | Superseded | Add `status` column = "superseded" |
| Cell comment | Reviewer note | Add `notes` column, append comment |
| Bold text | Emphasis | Usually ignore, but ask if unclear |

Ask user: "Several cells have yellow highlighting. Should I add a `review_flag` column to preserve this, or ignore it?"

### 1.6 Output Clean CSV

After normalization, output to CSV with:
- Single header row with canonical names
- `tag` as first column
- Consistent data types per column
- No merged cells, no formatting
- UTF-8 encoding

Example output structure:
```csv
tag,description,type,setpoint,unit,range_low,range_high,alarm_low,alarm_high,alarm_low_low,alarm_high_high,io_type,io_address,pid_ref,notes
FIC-101,Feed Flow Controller,Flow Controller,150,GPM,0,200,125,175,100,190,AI,AI-101,PID-001-A,
PT-101,Separator Pressure,Pressure Transmitter,800,kPag,0,1500,600,1200,500,1350,AI,AI-102,PID-001-A,Verify with operations
```

## Step 2: Script Validation

Run validation scripts on clean CSV:

```bash
# Check tag format
python scripts/validate_tag_format.py normalized.csv

# Compare against other SSoT files
python scripts/validate_consistency.py normalized.csv setpoints.csv
python scripts/validate_consistency.py normalized.csv io_list.csv
```

Scripts output exception list (CSV) with:
- `tag`: Instrument tag
- `field`: Column with issue
- `issue_type`: missing, mismatch, format_error
- `file1_value`: Value in first file
- `file2_value`: Value in second file
- `severity`: error, warning, info

## Step 3: Generate Corrected Output

### 3.1 Review Exceptions

Present exception list to user:
- Group by severity (errors first)
- For each discrepancy, show both values
- Ask user which value is correct, or if both need correction

### 3.2 Apply Corrections

Update the normalized CSV with user-confirmed corrections.

### 3.3 Generate Output in Original Format

**If input was xlsx**:
- Create new xlsx matching original structure
- Preserve original column order and names (use mapping in reverse)
- Apply original formatting if specified
- Add revision note in document properties or header

**If input was docx**:
- Update tables in-place
- Preserve narrative text
- Track changes if requested

### 3.4 Output Files

| File | Purpose |
|------|---------|
| `[original]_normalized.csv` | Clean SSoT (for scripts, version control) |
| `[original]_exceptions.csv` | Discrepancies found |
| `[original]_corrected.xlsx` | Corrected file in original format |

## Common Patterns by Document Type

### Instrument List
Primary key: `tag`
Required: tag, description, type
Common: range, unit, location, pid_ref, manufacturer, model

### Setpoint List
Primary key: `tag`
Required: tag, setpoint, unit
Common: alarm_low, alarm_high, alarm_low_low, alarm_high_high, trip_low, trip_high

### IO List
Primary key: `tag` + `io_type` (may have multiple IOs per instrument)
Required: tag, io_type, io_address
Common: description, signal_type, plc, rack, slot, channel

### Control Narrative (tables)
Primary key: `tag`
Required: tag, description
Common: type, range, setpoint, alarm conditions, control logic

## Ambiguity Resolution

When encountering ambiguity, ask user with specific options:

**Column name ambiguity**:
> "Column E is labeled 'Limit'. This could be:
> 1. `alarm_high` (high alarm limit)
> 2. `range_high` (upper range limit)  
> 3. `trip_high` (shutdown trip point)
> Which interpretation is correct?"

**Value ambiguity**:
> "Cell E15 contains '150/175'. This could be:
> 1. Range: 150 to 175
> 2. Setpoint 150, Alarm 175
> 3. Something else
> How should I parse this?"

**Unit ambiguity**:
> "Column F has mixed units: some rows show 'psig', others 'kPag'. Should I:
> 1. Keep as-is (different instruments, different units)
> 2. Convert all to kPag
> 3. Convert all to psig
> 4. Flag for review"

**Missing data**:
> "Rows 23-27 have no setpoint values. Should I:
> 1. Leave blank
> 2. Mark as 'TBD'
> 3. Flag for review"
