# Canonical Data Schema

Standard column names and data formats for normalized SSoT files. Scripts expect these exact column names (case-insensitive).

## Why a Standard Schema?

1. **Script reliability** — Validation scripts match on canonical column names
2. **Data exchange** — Consistent format enables tool interoperability
3. **Reduced ambiguity** — One name per concept
4. **Traceability** — Row numbers and source files tracked for exceptions

## Instrument List Schema

Primary SSoT for all instruments. All other files reference tags from this list.

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `tag` | string | ✓ | Instrument tag (ISA S5.1 format) | FIC-101 |
| `description` | string | ✓ | Service description | Feed flow to separator |
| `type` | string | | Instrument type | Transmitter, Switch, Element |
| `manufacturer` | string | | Vendor name | Rosemount, Emerson |
| `model` | string | | Model number | 3051S |
| `range_low` | number | | Lower range value | 0 |
| `range_high` | number | | Upper range value | 1000 |
| `range_unit` | string | | Engineering unit for range | GPM |
| `output_type` | string | | Signal type | 4-20mA, HART, Modbus |
| `fail_mode` | string | | Failure action | FC, FO, FL |
| `location` | string | | Physical location | Module A, Field |
| `pid_reference` | string | | P&ID drawing number | PID-001-A |
| `datasheet` | string | | Specification sheet number | DS-FIC-101 |
| `io_type` | string | | I/O classification | AI, AO, DI, DO |
| `sil` | string | | Safety integrity level | SIL 1, SIL 2, Non-SIS |
| `area` | string | | Process area | Separation, Compression |

## Setpoint List Schema

Control setpoints for instruments (not alarms — see Master Alarm Database).

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `tag` | string | ✓ | Instrument tag (must exist in instrument list) | FIC-101 |
| `setpoint` | number | ✓ | Control setpoint | 500.0 |
| `setpoint_unit` | string | ✓ | Setpoint unit | GPM |
| `control_mode` | string | | AUTO, CASCADE, MANUAL | AUTO |
| `tuning_p` | number | | Proportional gain | 1.5 |
| `tuning_i` | number | | Integral time (min) | 2.0 |
| `tuning_d` | number | | Derivative time (min) | 0 |
| `output_low` | number | | Output low limit (%) | 0 |
| `output_high` | number | | Output high limit (%) | 100 |

## Master Alarm Database (MAD) Schema

SSoT for all alarm configuration per ISA-18.2. See `standards/isa-18.2-alarm.md`.

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `tag` | string | ✓ | Instrument tag | PT-101 |
| `alarm_type` | string | ✓ | Alarm type (H, HH, L, LL, DEV) | HH |
| `alarm_tag` | string | | Full alarm tag if different | PAHH-101 |
| `setpoint` | number | ✓ | Alarm setpoint value | 1200 |
| `setpoint_unit` | string | ✓ | Engineering unit | kPag |
| `deadband` | number | | Alarm deadband | 10 |
| `on_delay` | number | | Delay before alarming (s) | 5 |
| `off_delay` | number | | Delay before clearing (s) | 0 |
| `priority` | string | ✓ | Critical, High, Medium, Low | High |
| `cause` | string | ✓ | What causes this condition | Blocked outlet, closed valve |
| `consequence` | string | ✓ | What happens if not addressed | Overpressure, vessel damage |
| `operator_action` | string | ✓ | Required operator response | Open bypass valve, reduce feed |
| `response_time_min` | number | ✓ | Maximum response time (min) | 10 |
| `classification` | string | | Safety, Environmental, Quality, Equipment | Safety |
| `state_based` | string | | When alarm is active | Normal, Startup, Shutdown |
| `suppression_allowed` | boolean | | Can be shelved | true |
| `sif_reference` | string | | If part of SIF | SIF-001 |
| `rationalization_date` | date | | When rationalized | 2025-01-15 |
| `rationalized_by` | string | | Who rationalized | JD |
| `rationalization_status` | string | | Approved, Pending, Rejected | Approved |
| `notes` | string | | Additional notes | |

### Alarm Type Codes

| Code | Description |
|------|-------------|
| H | High |
| HH | High-High |
| L | Low |
| LL | Low-Low |
| DEV | Deviation (from setpoint) |
| ROC | Rate of Change |
| FAIL | Instrument failure |
| DISC | Discrepancy (between redundant) |

## IO List Schema

Input/Output wiring and addressing.

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `tag` | string | ✓ | Instrument tag | FIC-101 |
| `io_type` | string | ✓ | AI, AO, DI, DO | AI |
| `signal_type` | string | ✓ | 4-20mA, 24VDC, RTD, TC | 4-20mA |
| `plc_name` | string | | PLC or DCS name | PLC-01 |
| `plc_rack` | string | | PLC rack number | 1 |
| `plc_slot` | string | | PLC slot number | 4 |
| `plc_channel` | string | | Channel number | 2 |
| `plc_address` | string | | Full PLC address | %IW100 |
| `cabinet` | string | | Marshalling cabinet | MC-01 |
| `terminal` | string | | Terminal block/number | TB1-5 |
| `cable` | string | | Cable number | C-FIC-101 |
| `jb` | string | | Junction box | JB-101 |
| `fail_state` | string | | For DI: NC/NO; for AO: value | FC |
| `intrinsic_safe` | boolean | | IS circuit | false |
| `loop_resistance` | number | | Maximum loop resistance (Ω) | 600 |

## Cause & Effect Matrix Schema

When extracted to tabular format per IEC 62881.

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `sif_id` | string | | Safety function identifier | SIF-001 |
| `cause_tag` | string | ✓ | Initiating tag (alarm/switch) | PAHH-101 |
| `cause_description` | string | | Description of cause | Pressure high-high |
| `effect_tag` | string | ✓ | Responding tag (valve/pump) | XV-101 |
| `effect_description` | string | | Description of effect | Inlet isolation valve |
| `action` | string | ✓ | CLOSE, OPEN, TRIP, START, ALARM | CLOSE |
| `logic` | string | | AND, OR, or blank for direct | |
| `voting` | string | | 1oo1, 1oo2, 2oo3 | 2oo3 |
| `time_delay` | number | | Delay in seconds | 5 |
| `latching` | boolean | | Requires manual reset | true |
| `sil` | string | | Safety integrity level | SIL 2 |
| `bypass_tag` | string | | Bypass switch tag | XS-101 |
| `reset_tag` | string | | Reset switch tag | XS-102 |

## Loop Check Schema

Commissioning status tracking.

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `tag` | string | ✓ | Instrument tag | FIC-101 |
| `loop_number` | string | | Loop identifier | 101 |
| `pid_reference` | string | | P&ID drawing | PID-001-R3 |
| `cold_check_date` | date | | Cold loop check date | 2025-01-15 |
| `cold_check_by` | string | | Technician initials | JD |
| `cold_check_pass` | boolean | | Pass/fail | true |
| `hot_check_date` | date | | Hot loop check date | 2025-01-16 |
| `hot_check_by` | string | | Technician initials | JD |
| `hot_check_pass` | boolean | | Pass/fail | true |
| `test_0` | number | | Reading at 0% input | 4.00 |
| `test_25` | number | | Reading at 25% input | 8.00 |
| `test_50` | number | | Reading at 50% input | 12.00 |
| `test_75` | number | | Reading at 75% input | 16.00 |
| `test_100` | number | | Reading at 100% input | 20.00 |
| `functional_test_date` | date | | Functional test date | 2025-01-17 |
| `functional_test_pass` | boolean | | Pass/fail | true |
| `punch_items` | string | | Outstanding issues | Valve sticking at 25% |

## Cable Schedule Schema

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `cable_number` | string | ✓ | Cable identifier | C-FIC-101 |
| `cable_type` | string | ✓ | Cable specification | 2C-16AWG-SH |
| `from_location` | string | ✓ | Origin (tag or JB) | FIC-101 |
| `from_terminal` | string | | Terminal at origin | TB1 |
| `to_location` | string | ✓ | Destination (JB or cabinet) | JB-101 |
| `to_terminal` | string | | Terminal at destination | TB2 |
| `length_m` | number | | Cable length (m) | 45 |
| `tray` | string | | Cable tray routing | CT-01 |
| `gland_from` | string | | Gland size at origin | M20 |
| `gland_to` | string | | Gland size at destination | M20 |
| `tested` | boolean | | Continuity tested | true |
| `test_date` | date | | Test date | 2025-01-14 |

## File Naming Convention

```
[document_type]_[system]_[revision].csv

Examples:
  instrument_list_compression_R3.csv
  setpoint_list_separation_R2.csv
  io_list_module_a_R1.csv
  ce_matrix_esd_R4.csv
  alarm_database_plant_R1.csv
```

## Exception Output Schema

All validation scripts produce consistent exception CSV format:

| Column | Description |
|--------|-------------|
| `severity` | error, warning, info |
| `tag` | Affected instrument tag |
| `field` | Column name with issue (if applicable) |
| `issue_type` | Specific issue category |
| `file1_name` | First file name |
| `file1_row` | Row number in first file (1-indexed) |
| `file1_value` | Value from first file |
| `file2_name` | Second file name |
| `file2_row` | Row number in second file |
| `file2_value` | Value from second file |

### Issue Types

| Issue Type | Severity | Description |
|------------|----------|-------------|
| `missing_in_file1` | warning | Tag in file2 not found in file1 |
| `missing_in_file2` | warning | Tag in file1 not found in file2 |
| `value_mismatch` | error/warning | Same field has different values |
| `unit_mismatch` | error | Units don't match after normalization |
| `format_mismatch` | warning | Tag format variation (FIC-101 vs FIC_101) |
| `invalid_first_letter` | warning | First letter not in ISA S5.1 |
| `unparseable` | error | Tag format not recognized |
| `alarm_no_action` | error | Alarm missing operator_action |
| `alarm_no_consequence` | error | Alarm missing consequence |
| `voting_count_mismatch` | error | 2oo3 voting but only 2 instruments |

## Cross-References

| Related Resource | Purpose |
|-----------------|---------|
| `schemas/unit-normalization.md` | Unit conversion tables |
| `workflows/data-normalization.md` | Header mapping workflow |
| `standards/isa-s5.1-reference.md` | Tag format rules |
| `standards/isa-18.2-alarm.md` | Alarm management requirements |
| `scripts/validate_consistency.py` | Cross-file validation |
| `scripts/validate_tag_format.py` | Tag format validation |
