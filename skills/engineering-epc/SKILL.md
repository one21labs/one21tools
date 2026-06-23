---
name: engineering-epc
description: Use for Shutdown keys, IO lists, Instrument lists, cause-and-effect matrices, commissioning loop checks, document control, and other engineering spreadsheets and SSoT extraction from messy spreadsheets. Cross-check instrument lists against setpoint lists, IO lists, and control narratives. Flag inconsistencies for human review.
---

# Oil & Gas EPC Engineering

## Table of Contents

1. [Dependencies](#dependencies)
2. [SSoT Normalization Workflow](#ssot-normalization-workflow)
3. [Scripts](#scripts)
4. [Quick Reference](#quick-reference)
5. [Reference Guide](#reference-guide)
6. [Cross-References](#cross-references)

---

## Dependencies

```bash
pip install pandas openpyxl ezdxf python-docx
```

Verify:
```bash
python -c "import pandas, openpyxl, ezdxf, docx; print('OK')"
```

---

## SSoT Normalization Workflow

```
Input (messy xlsx/docx)
    ↓
Step 1: Claude normalizes (read data-normalization.md)
    - Unmerge cells, fill down, normalize headers/units
    - Ask user about ambiguities
    ↓
Clean CSV (normalized)
    ↓
Step 2: Scripts validate
    - validate_consistency.py (cross-check files)
    - validate_tag_format.py (naming conventions)
    ↓
Exception list (CSV with row numbers)
    ↓
Step 3: Claude generates corrected output
    - Same format as input (xlsx/docx)
    - Incorporates user-confirmed corrections
```

Copy and track progress:
```
- [ ] Normalize input file
- [ ] Run validate_consistency.py
- [ ] Run validate_tag_format.py
- [ ] Review exception list with user
- [ ] Generate corrected output
- [ ] Verify corrections applied
```

---

## Scripts

**validate_consistency.py** — Cross-check between SSoT files
```bash
python scripts/validate_consistency.py instruments.csv setpoints.csv
python scripts/validate_consistency.py instruments.csv io_list.csv -o discrepancies.csv
```

**validate_tag_format.py** — Check ISA S5.1 naming conventions
```bash
python scripts/validate_tag_format.py instruments.csv
python scripts/validate_tag_format.py --list-isa  # Show reference
```

**extract_dxf_tags.py** — Extract tags from DXF/CAD P&IDs (vector format only; raster/scanned P&IDs require AI-powered digitization tools — as of 2025, platforms such as SymphonyAI and DiagramIQ reduce extraction from 9-12 months to weeks)
```bash
python scripts/extract_dxf_tags.py drawing.dxf -o pid_tags.csv
python scripts/extract_dxf_tags.py *.dxf -o all_tags.csv --layer INSTRUMENTS
```
Output includes drawing_number, revision, date from title block.

**compare_pid_to_ssot.py** — Compare P&ID tags to instrument list
```bash
python scripts/compare_pid_to_ssot.py pid_tags.csv instruments.csv
```

---

## Quick Reference

| Task | Action |
|------|--------|
| Normalize messy xlsx | Read `data-normalization.md`, output clean CSV |
| Cross-check files | Run `validate_consistency.py` |
| Review C&E matrix | Read `cause-effect-review.md`, cross-check vs narrative/P&ID |
| Extract P&ID tags | Run `extract_dxf_tags.py` |
| Compare P&ID to list | Run `compare_pid_to_ssot.py` |
| Generate loop checks | Read `commissioning.md`, generate from instrument list |
| Rationalize alarms | Read `isa-18.2-alarm.md`, populate MAD schema. Flood threshold: >10 alarms/10 min per operator (ISA 18.2) |
| Validate tag format | Read `isa-s5.1-reference.md` |

---

## Reference Guide

All references are in `references/` directory, one level deep.

### Standards
| File | When to Read |
|------|--------------|
| `isa-s5.1-reference.md` | Tag format validation, symbol lookup (updated 2024: ANSI/ISA-5.1-2024 adds loop instrument diagram symbols and two new technical reports TR5.1.02, TR5.1.03) |
| `isa-18.2-alarm.md` | Alarm rationalization, MAD population |
| `standards-index.md` | Quick lookup of all applicable standards |

### Schemas
| File | When to Read |
|------|--------------|
| `canonical-schema.md` | Column definitions, data types, exception format |
| `unit-normalization.md` | Unit conversions (pressure, temp, flow) |

### Workflows
| File | When to Read |
|------|--------------|
| `data-normalization.md` | **First read** when normalizing any file |
| `cause-effect-review.md` | C&E matrix review, SIS/SIF verification |
| `commissioning.md` | Loop check procedures, 5-point testing |
| `document-control.md` | Numbering, revisions, transmittals |

### Domain
| File | When to Read |
|------|--------------|
| `project-lifecycle.md` | FEED→Detailed→Procurement→Fab→Construction phases |

---

## Cross-References

| Need | Resource |
|------|----------|
| Root cause analysis | `engineering-principles` skill |
| SSoT patterns | `engineering-principles` skill |
| Creating xlsx/docx | `docx`, `xlsx` skills |
