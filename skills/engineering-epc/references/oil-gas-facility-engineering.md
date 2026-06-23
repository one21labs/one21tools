# Oil & Gas Facility Process Engineering

Engineering principles applied to modular oil and gas facility design, fabrication, and document control.

## Table of Contents

1. [Domain Context](#domain-context)
2. [Project Phases and Document Flow](#project-phases-and-document-flow)
3. [Engineering Deliverables Hierarchy](#engineering-deliverables-hierarchy)
4. [Document Numbering System](#document-numbering-system)
5. [Revision Control](#revision-control)
6. [Transmittal Process](#transmittal-process)
7. [P&ID Development Workflow](#pid-development-workflow)
8. [Equipment Datasheet Workflow](#equipment-datasheet-workflow)
9. [Quality Control Documentation](#quality-control-documentation)
10. [Turnover Package (Handover)](#turnover-package-handover)
11. [Common Waste in Facility Engineering](#common-waste-in-facility-engineering)
12. [Cross-References](#cross-references)
13. [Standards and Codes](#standards-and-codes-common)

---

## Domain Context

**Scope**: Modular gas processing, compression, refrigeration, and oil separation facilities—typically designed, fabricated in-shop, and field-assembled.

**Key differentiator**: Modular fabrication shifts work from field to shop, increasing quality control opportunity but requiring rigorous document coordination between engineering, fabrication, and field teams.

## Project Phases and Document Flow

| Phase | Purpose | Key Deliverables | SSoT Principle |
|-------|---------|------------------|----------------|
| **FEED** | Define scope, estimate ±15-20% | Basis of Design, PFDs, Preliminary P&IDs, Equipment List | Design docs are SSoT for "what/why" |
| **Detailed Engineering** | Full design for procurement/fabrication | Final P&IDs, Equipment Datasheets, Specifications, Isometrics | Each deliverable has one owner discipline |
| **Procurement** | Acquire equipment and materials | Purchase Orders, Vendor Drawings, MTRs | Vendor docs reference project specs |
| **Fabrication** | Shop assembly of modules | Shop Drawings, QC Records, NCRs, Test Records | As-built reflects actual construction |
| **Construction** | Field installation and tie-ins | Field Redlines, Punchlist, Commissioning Records | Field changes feed back to as-built |
| **Turnover** | Handover to operations | As-Built Package, O&M Manuals, Spare Parts Lists | Final package is SSoT for operations |

### Design-First Application

In modular facility work, Design-First is critical because:
- Fabrication starts before field conditions are fully known
- Module interfaces must be precisely defined
- Rework in shop is expensive; rework after shipping is catastrophic

**Checkpoint**: Before releasing for fabrication, verify:
- [ ] All interfaces defined (piping, electrical, structural)
- [ ] All vendor data incorporated
- [ ] HAZOP complete and actions closed
- [ ] 3D model clash-checked
- [ ] Client IFC (Issued for Construction) approval received

## Engineering Deliverables Hierarchy

### Process Engineering (Drives All Downstream)

| Deliverable | Purpose | Downstream Users |
|-------------|---------|------------------|
| **Process Flow Diagram (PFD)** | Material/energy balance, major equipment | All disciplines for scope understanding |
| **Heat & Material Balance (H&MB)** | Stream conditions for equipment sizing | Mechanical, Piping, Instrumentation |
| **P&ID** | Process control philosophy, all equipment/instruments | Piping, Electrical, Instrumentation, Safety |
| **Process Datasheet** | Equipment duty conditions | Mechanical for sizing, Procurement for RFQ |
| **Line List** | Pipe specifications per line | Piping for isometrics, stress analysis |
| **Instrument List** | All instruments with tag numbers | Instrumentation for loop diagrams |

**SSoT Rule**: Process datasheets are SSoT for operating conditions. Mechanical datasheets reference process datasheets—never duplicate operating data.

### Mechanical Engineering

| Deliverable | Input From | Output To |
|-------------|------------|-----------|
| **Equipment Datasheet (Mechanical)** | Process datasheet | Procurement RFQ, Vendor |
| **Equipment List** | P&IDs, Process datasheets | All disciplines for coordination |
| **GA Drawings** | Vendor data, Plot plan | Piping, Structural, Electrical |
| **Nozzle Orientation Drawings** | Piping coordination | Piping isometrics |

### Piping Engineering

| Deliverable | Purpose | Key Verification |
|-------------|---------|------------------|
| **Plot Plan** | Equipment arrangement | Maintenance access, safety egress |
| **Piping Isometrics** | Fabrication drawings | Stress analysis complete, supports located |
| **Pipe Support Drawings** | Support details | Structural loads provided |
| **Stress Analysis** | Verify thermal/pressure loads | All critical lines analyzed |

### Instrumentation & Controls

| Deliverable | Purpose | Integration Point |
|-------------|---------|-------------------|
| **Instrument Index** | Master list of all instruments | Tag numbers consistent with P&ID |
| **Loop Diagrams** | Wiring and control logic | Electrical for panel design |
| **Instrument Datasheets** | Specification for procurement | Process conditions from P&ID |
| **Control Narrative** | Operating philosophy | HAZOP verification |
| **Cause & Effect Diagram** | Safety system logic | SIL verification |

### Electrical Engineering

| Deliverable | Purpose | Input Required |
|-------------|---------|----------------|
| **Single Line Diagram** | Power distribution | Load list from all disciplines |
| **Area Classification** | Hazardous area zones | Process for source identification |
| **Cable Schedule** | Cable sizing and routing | Instrument list, motor list |
| **Lighting Layout** | Illumination design | Plot plan, area classification |

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

### Equipment Categories

| Category | Typical Packages | Key Specs |
|----------|-----------------|-----------|
| **Separation** | Inlet separators, test separators, FWKO | Pressure, temperature, liquid handling capacity |
| **Compression** | Reciprocating, screw compressors | Suction/discharge pressure, flow, driver HP |
| **Heat Transfer** | Line heaters, shell & tube exchangers | Duty, UA, pressure drop |
| **Treating** | Amine units, dehydrators (TEG), filters | Throughput, contaminant removal efficiency |
| **Storage** | Tanks, bullets, spheres | Volume, pressure rating, product |

## Quality Control Documentation

### Fabrication QC Records

| Record | Purpose | Retention |
|--------|---------|-----------|
| **Material Test Reports (MTRs)** | Traceability of materials | Life of asset |
| **Weld Maps** | Location of all welds | Life of asset |
| **NDE Reports** | Non-destructive examination results | Life of asset |
| **Hydrostatic Test Records** | Pressure test verification | Life of asset |
| **NCR (Non-Conformance Report)** | Deviation documentation | Life of asset |
| **Dimensional Reports** | Verification of critical dimensions | Project closeout |

### NCR Process (5 Whys Application)

When NCR is raised:
1. Document the non-conformance factually
2. Determine disposition (use-as-is, repair, reject)
3. If recurring, perform root cause analysis
4. Implement corrective action to prevent recurrence
5. Verify effectiveness

**Jidoka Principle**: Stop and fix quality problems immediately. Do not pass defects downstream to field.

## Turnover Package (Handover)

### Minimum Turnover Documentation

| Category | Documents |
|----------|-----------|
| **Design** | As-built P&IDs, PFDs, equipment datasheets |
| **Vendor** | O&M manuals, spare parts lists, certificates |
| **Construction** | As-built drawings, test records, commissioning records |
| **Regulatory** | Pressure equipment registration, safety certifications |
| **Operating** | Operating procedures, control narratives, alarm lists |

### As-Built Requirements

As-built drawings must reflect:
- All field changes (with cloud/revision notation)
- Final equipment/instrument tag numbers
- Actual routing of piping and cables
- Confirmed nozzle orientations
- Installed spare connections

**SSoT for Operations**: The turnover package becomes the single source of truth for the operating facility. Incomplete turnover creates ongoing operational waste.

## Common Waste in Facility Engineering

| Waste | Manifestation | Mitigation |
|-------|---------------|------------|
| **Waiting** | Design holds waiting for vendor data | Early vendor engagement, long-lead identification |
| **Rework** | P&ID changes after IFC | Freeze design earlier, rigorous review gates |
| **Overprocessing** | Excessive detail in FEED | Match detail level to project phase |
| **Defects** | Field fit-up issues from drawing errors | 3D model review, dimensional QC |
| **Inventory** | Unincorporated redlines | Regular redline incorporation cycles |
| **Motion** | Searching for current revision | EDMS with revision control |
| **Transportation** | Multiple transmittal cycles for same document | Complete review before reissue |

## Cross-References

For underlying methodology, consult the `engineering-principles` skill:
- Root cause analysis (5 Whys)
- Waste identification (Seven Wastes)
- Design review checklists
- SSoT enforcement patterns
- Core TPS/Lean principles

## Standards and Codes (Common)

| Category | Standards |
|----------|-----------|
| **P&ID** | ISA S5.1, ISO 10628, PIP PIC001 |
| **Pressure Vessels** | ASME VIII, PED (Europe), ABSA (Alberta) |
| **Piping** | ASME B31.3 (Process), B31.8 (Gas Transmission) |
| **Electrical** | CEC (Canada), NEC (USA), IEC |
| **Instrumentation** | ISA, IEC 61511 (SIS) |
| **Structural** | CSA S16 (Steel), NBC (Buildings) |
