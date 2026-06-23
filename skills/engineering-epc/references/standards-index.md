# Standards Index

Master reference for applicable ISA, IEC, and industry standards.

## Instrumentation & Control

| Standard | Title | Scope | Skill Reference |
|----------|-------|-------|-----------------|
| **ANSI/ISA-5.1-2024** | Instrumentation Symbols and Identification | Tag naming, P&ID symbols | `standards/isa-s5.1-reference.md` |
| **ISA-5.4-1991** | Instrument Loop Diagrams | Loop diagram content and format | - |
| **ISA-TR5.1.02-2024** | Identification System Guidelines | Supplemental to ISA-5.1 | - |
| **ISA-TR5.1.03-2024** | Graphic Symbol Guidelines | Supplemental to ISA-5.1 | - |
| **ISA-5.7** | P&ID Standard (in development) | P&ID development practices | - |

## Alarm Management

| Standard | Title | Scope | Skill Reference |
|----------|-------|-------|-----------------|
| **ANSI/ISA-18.2-2016** | Management of Alarm Systems | Alarm lifecycle management | `standards/isa-18.2-alarm.md` |
| **IEC 62682** | Management of Alarm Systems (international) | International version of ISA-18.2 | - |
| **ISA-TR18.2.1** | Alarm Philosophy | Philosophy document guidance | - |
| **ISA-TR18.2.2** | Alarm Identification and Rationalization | Rationalization procedures | - |
| **ISA-TR18.2.3** | Basic Alarm Design | Design implementation | - |
| **ISA-TR18.2.4** | Enhanced and Advanced Alarm Methods | Dynamic alarming, state-based | - |
| **ISA-TR18.2.5** | Alarm System Monitoring, Assessment, Auditing | KPIs and metrics | - |

## Safety Instrumented Systems

| Standard | Title | Scope | Skill Reference |
|----------|-------|-------|-----------------|
| **IEC 61511 / ISA-61511** | Safety Instrumented Systems for Process Industry | SIS lifecycle | `workflows/cause-effect-review.md` |
| **IEC 61508** | Functional Safety (general) | SIS design basis | - |
| **ISA-TR84.00.02** | SIL Verification | PFD calculations | - |
| **ISA-TR84.00.03** | Automation Asset Integrity | SIS maintenance | - |
| **ISA-TR84.00.04** | Implementation Guidelines | Practical IEC 61511 guidance | - |
| **ISA-TR84.00.05** | Burner Management Systems | BMS-specific guidance | - |
| **ISA-TR84.00.07** | Fire and Gas Systems | F&G-specific guidance | - |
| **IEC 62881** | Cause and Effect Matrix | C&E documentation standard | `workflows/cause-effect-review.md` |

## Commissioning & Testing

| Standard | Title | Scope | Skill Reference |
|----------|-------|-------|-----------------|
| **ISA-62381 / IEC 62381** | FAT and SAT | Factory and site acceptance | `workflows/commissioning.md` |
| **ISA-62382 / IEC 62382** | Loop Check | Electrical loop integrity | `workflows/commissioning.md` |
| **ISA-105** | Commissioning, Loop Checks, FAT/SAT | Comprehensive commissioning | - |

## Specification & Documentation

| Standard | Title | Scope | Skill Reference |
|----------|-------|-------|-----------------|
| **ISA-TR20.00.01** | Specification Forms | Instrument datasheets | - |
| **ISA-20** | Specification Form Guidelines | Form requirements | - |
| **ISA-51.1** | Instrumentation Terminology | Standard terminology | - |

## Data Integration & Handover

| Standard | Title | Scope | Skill Reference |
|----------|-------|-------|-----------------|
| **ISO 15926** | Integration of Life-Cycle Data | Data model for process plants | - |
| **CFIHOS** | Capital Facilities Information Handover | Handover data requirements | - |
| **IEC 62424** | P&ID Data Exchange | P&ID data integration | - |
| **ISO 8000** | Data Quality | Master data quality | - |

## Process Industry Practices (PIP)

| Standard | Title | Scope |
|----------|-------|-------|
| **PIP PIC001** | Piping and Instrumentation Diagram Documentation Criteria | P&ID content requirements |
| **PIP PCSPS001** | Process Control System Process Safety Requirements | PCS safety requirements |
| **PIP PCMDS001** | Distributed Control System Minimum Design Standard | DCS specifications |

## Other Referenced Standards

| Standard | Title | Scope |
|----------|-------|-------|
| **API 554** | Process Instrumentation and Control | Refinery I&C practices |
| **API RP 556** | Fired Heater Instrumentation | Heater control |
| **NFPA 85** | Boiler and Combustion Systems | BMS requirements |
| **ASME B31.3** | Process Piping | Piping design code |
| **ASME VIII** | Pressure Vessels | Vessel design code |
| **ISA-7.0.01** | Instrument Air Quality | Air system requirements |
| **ISA-12** | Hazardous Location Equipment | Area classification |
| **ISA-75** | Control Valve Standards | Valve sizing and testing |
| **ISA-77** | Fossil Power Plant Automation | Power plant controls |
| **ISA-88** | Batch Control | Batch process automation |
| **ISA-95** | Enterprise-Control Integration | MES integration |
| **ISA-99 / IEC 62443** | Industrial Cybersecurity | Control system security |

## Regulatory References

| Regulation | Jurisdiction | Scope |
|------------|--------------|-------|
| **OSHA 29 CFR 1910.119** | USA | Process Safety Management |
| **EPA 40 CFR 68** | USA | Risk Management Program |
| **ABSA** | Alberta, Canada | Pressure equipment registration |
| **ATEX** | EU | Explosive atmosphere equipment |
| **PED** | EU | Pressure Equipment Directive |
| **SEVESO III** | EU | Major accident hazards |

## Standard Hierarchy

```
IEC (International)
    ↓ adopted as
ISA/ANSI (US National)
    ↓ supplemented by
ISA Technical Reports (Guidance)
    ↓ implemented via
Company Specifications & Procedures
```

## Version Notes

| Standard | Current Version | Previous | Key Changes |
|----------|-----------------|----------|-------------|
| ISA-5.1 | 2024 | 2009 | New symbols, loop diagram table |
| ISA-18.2 | 2016 | 2009 | Package systems, clarifications |
| IEC 61511 | 2016 | 2003 | Cybersecurity, competency |
