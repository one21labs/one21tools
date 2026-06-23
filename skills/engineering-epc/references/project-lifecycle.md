# Project Lifecycle

Engineering phases for modular oil and gas facility projects.

## Domain Context

**Scope**: Modular gas processing, compression, refrigeration, and oil separation facilities—typically designed, fabricated in-shop, and field-assembled.

**Key differentiator**: Modular fabrication shifts work from field to shop, increasing quality control opportunity but requiring rigorous document coordination between engineering, fabrication, and field teams.

## Project Phases

| Phase | Purpose | Key Deliverables | SSoT Principle |
|-------|---------|------------------|----------------|
| **FEED** | Define scope, estimate ±15-20% | Basis of Design, PFDs, Preliminary P&IDs, Equipment List | Design docs are SSoT for "what/why" |
| **Detailed Engineering** | Full design for procurement/fabrication | Final P&IDs, Equipment Datasheets, Specifications, Isometrics | Each deliverable has one owner discipline |
| **Procurement** | Acquire equipment and materials | Purchase Orders, Vendor Drawings, MTRs | Vendor docs reference project specs |
| **Fabrication** | Shop assembly of modules | Shop Drawings, QC Records, NCRs, Test Records | As-built reflects actual construction |
| **Construction** | Field installation and tie-ins | Field Redlines, Punchlist, Commissioning Records | Field changes feed back to as-built |
| **Turnover** | Handover to operations | As-Built Package, O&M Manuals, Spare Parts Lists | Final package is SSoT for operations |

## Design-First Application

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

## Equipment Categories

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

## Standards and Codes

| Category | Standards |
|----------|-----------|
| **P&ID** | ISA S5.1, ISO 10628, PIP PIC001 |
| **Pressure Vessels** | ASME VIII, PED (Europe), ABSA (Alberta) |
| **Piping** | ASME B31.3 (Process), B31.8 (Gas Transmission) |
| **Electrical** | CEC (Canada), NEC (USA), IEC |
| **Instrumentation** | ISA, IEC 61511 (SIS) |
| **Structural** | CSA S16 (Steel), NBC (Buildings) |

See `standards/standards-index.md` for complete standards reference.

## Cross-References

| Need | Resource |
|------|----------|
| Document numbering | `references/document-control.md` |
| Commissioning | `references/commissioning.md` |
| Data normalization | `references/data-normalization.md` |
| Engineering principles | `engineering-principles` skill |
