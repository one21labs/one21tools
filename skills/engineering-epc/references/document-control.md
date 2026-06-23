# Document Control

Document numbering, revision control, and transmittal processes for facility engineering.

## Document Numbering System

A consistent numbering system prevents duplication and enables traceability.

### Typical Structure

```
[Project]-[Originator]-[Area]-[Discipline]-[DocType]-[Sequence]

Example: 2611-PRO-100-PROC-PID-001
         │     │    │    │     │    └─ Sequential number
         │     │    │    │     └────── Document type (PID, ISO, DWG)
         │     │    │    └──────────── Discipline (PROC, MECH, PIPE, INST, ELEC)
         │     │    └───────────────── Area/Unit number
         │     └────────────────────── Originator code
         └──────────────────────────── Project number
```

### Discipline Codes (Common)

| Code | Discipline |
|------|------------|
| PROC | Process |
| MECH | Mechanical |
| PIPE | Piping |
| INST | Instrumentation |
| ELEC | Electrical |
| CIVL | Civil/Structural |
| SAFE | Safety/Fire |

### Document Type Codes (Common)

| Code | Type |
|------|------|
| PFD | Process Flow Diagram |
| PID | Piping & Instrumentation Diagram |
| ISO | Piping Isometric |
| GA | General Arrangement |
| DTS | Datasheet |
| SPC | Specification |
| LST | List/Schedule |
| CAL | Calculation |
| REP | Report |
| LPD | Loop Diagram |
| SLD | Single Line Diagram |
| CED | Cause & Effect Diagram |

**SSoT Rule**: Document numbers are assigned once and never reused. Superseded documents are marked superseded, not deleted.

## Revision Control

### Revision Sequence

| Stage | Revision Format | Meaning |
|-------|-----------------|---------|
| Preliminary/Internal | A, B, C... | Working drafts, not for construction |
| Issued for Review (IFR) | 0 | First client review |
| Issued for Approval (IFA) | 1 | Formal approval cycle |
| Issued for Construction (IFC) | 2+ | Released for fabrication/construction |
| As-Built | Final + "AB" | Reflects actual construction |

### Revision Block Requirements

Each revision must document:
- Revision number
- Date
- Description of change
- Originator initials
- Checker initials
- Approver initials

**100% Review Principle**: Every character in every revision is intentional. Cloud or triangle changes to show what changed.

### Revision Cloud/Triangle Rules

| Symbol | Meaning |
|--------|---------|
| Cloud | Added or changed in current revision |
| Triangle with rev # | Indicates which revision made the change |
| Strikethrough | Deleted (on some projects) |

Clouds and triangles are removed after client acceptance of revision.

## Transmittal Process

Transmittals are the formal record of document exchange.

### Transmittal Workflow

```
Originator prepares documents
    ↓
Document Controller registers in EDMS
    ↓
Transmittal created with:
  - Transmittal number
  - Document list with revisions
  - Purpose (IFR, IFA, IFC, Information)
  - Required response date
    ↓
Recipient acknowledges receipt
    ↓
Review and comments returned
    ↓
Comments incorporated, next revision issued
```

### Transmittal Status Codes

| Code | Status | Meaning |
|------|--------|---------|
| A | Approved | No comments, proceed |
| B | Approved with Comments | Incorporate in next revision |
| C | Revise and Resubmit | Major comments, requires re-review |
| D | Rejected | Does not meet requirements |
| E | For Information | No approval required |

### Common EDMS Tools

| Tool | Typical Use |
|------|-------------|
| Proarc | Large EPC projects, North Sea origin |
| FusionLive (Idox) | Multi-discipline coordination |
| Assai | Oil & gas document control |
| Aconex | Construction document management |
| SharePoint | Smaller projects, internal coordination |

**Waste Identification**: Manual transmittal tracking is a major source of waiting waste. EDMS automation reduces cycle time significantly.

## P&ID Development Workflow

P&IDs are the most critical process document—errors here cascade to all downstream disciplines.

### Development Stages

| Stage | Content Level | Review Required |
|-------|---------------|-----------------|
| **Preliminary (FEED)** | Major equipment, main process lines, basic control | Process internal |
| **IFR** | All equipment, utilities, control loops | Interdisciplinary |
| **30%** | Vendor data incorporated, instruments tagged | Client review |
| **60%** | All redlines incorporated, HAZOP complete | HAZOP closeout |
| **90%** | Minor comments only, ready for IFC | Final client review |
| **IFC** | Approved for construction | Released to fabrication |
| **As-Built** | All field changes incorporated | Turnover to operations |

### P&ID Review Checklist

- [ ] Equipment tag numbers match equipment list
- [ ] Line numbers match line list
- [ ] Instrument tags match instrument index
- [ ] Control loops complete (sensor → controller → final element)
- [ ] Relief devices sized and tagged
- [ ] Utility connections shown
- [ ] Vents and drains shown
- [ ] Spectacle blinds and isolation points shown
- [ ] Notes and legends complete
- [ ] Revision block current

### Common P&ID Errors (Root Cause Patterns)

| Error | Typical Root Cause | Prevention |
|-------|-------------------|------------|
| Missing instruments | Process/Instrumentation miscommunication | Joint P&ID development sessions |
| Wrong line specs | Line list not updated | SSoT: Line list drives P&ID |
| Control loop incomplete | Control narrative not referenced | Verify against control narrative |
| Relief device missing | HAZOP findings not incorporated | HAZOP action tracking |

## Equipment Datasheet Workflow

### Datasheet Development Sequence

```
Process Datasheet (Process Engineer)
  - Operating conditions
  - Duty requirements
  - Process fluids
        ↓
Mechanical Datasheet (Mechanical Engineer)
  - Design codes
  - Materials
  - Nozzle sizes/ratings
  - Mechanical details
        ↓
Vendor Datasheet (Vendor)
  - Actual equipment offered
  - Deviations noted
        ↓
Approved Vendor Datasheet
  - Client/contractor approved
  - Basis for fabrication
```

**SSoT Rule**: Operating conditions live in Process datasheet only. Mechanical datasheet references, never duplicates.

## Redline Management

### Redline Sources

| Source | Timing | Action |
|--------|--------|--------|
| Design review | During design | Incorporate immediately |
| Client comments | After IFR/IFA | Track in comment log, incorporate in next rev |
| HAZOP | During HAZOP | Track in HAZOP action register |
| Fabrication | During fab | Shop drawing markup, backfeed to design |
| Field | During construction | Field markup, incorporate in as-built |

### Redline Incorporation Cycle

```
Collect redlines (weekly during active phases)
    ↓
Review for conflicts or questions
    ↓
Incorporate in master drawing
    ↓
Issue new revision with changes clouded
    ↓
Update document register
    ↓
Transmit to affected parties
```

**Waste**: Unincorporated redlines are inventory waste. Long backlogs create defect risk (forgotten changes).

## Drawing Extraction for Scripts

When extracting data from drawings for validation:

| Drawing Type | Extract Method | Key Data |
|--------------|----------------|----------|
| P&ID (DXF) | `scripts/extract_dxf_tags.py` | Tags, drawing number, revision |
| Instrument List (xlsx) | `workflows/data-normalization.md` | Tag, description, range, type |
| IO List (xlsx) | `workflows/data-normalization.md` | Tag, IO type, address |

### Drawing Metadata Required

For traceability, extracted data must include:
- **Drawing number** — Document identifier
- **Revision** — Version extracted from
- **Date** — Revision date
- **Source file** — Original filename

See DXF script for title block extraction patterns.

## Cross-References

| Need | Resource |
|------|----------|
| Project phases | `domain/project-lifecycle.md` |
| Data schemas | `schemas/canonical-schema.md` |
| Tag format | `standards/isa-s5.1-reference.md` |
| DXF extraction | `scripts/extract_dxf_tags.py` |
