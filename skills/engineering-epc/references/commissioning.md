# Commissioning Workflows

Instrumentation commissioning procedures based on ISA-62381/62382 and IEC 61511.

## Commissioning Phases

| Phase | Scope | Prerequisites |
|-------|-------|---------------|
| **Pre-commissioning** | Document review, visual inspection | Mechanical completion |
| **Cold loop check** | Wiring verification (power off) | Cabling complete, instruments installed |
| **Hot loop check** | Signal verification (power on) | PLC/DCS operational, SAT complete |
| **Functional test** | Logic and interlock verification | Loop checks complete |
| **Performance test** | Process operation verification | Functional tests complete |

## Loop Folder Contents

Each instrument loop requires a complete loop folder before testing:

| Document | Purpose | Verification |
|----------|---------|--------------|
| Loop diagram | Wiring schematic | Matches as-built |
| Instrument datasheet | Specifications | Range, output, fail mode |
| Calibration certificate | Factory/field calibration | Within tolerance |
| Hook-up drawing | Physical installation | Correct orientation, impulse lines |
| P&ID extract | Process context | Tag matches, correct service |
| IO list extract | PLC/DCS addressing | Address matches configuration |

## Cold Loop Check Procedure

**Purpose**: Verify wiring integrity without power

### Prerequisites
- [ ] Instrument installed per hook-up drawing
- [ ] Cable terminations complete at all points
- [ ] Loop diagram available and current revision
- [ ] Multimeter/continuity tester available
- [ ] LOTO applied if required

### Procedure

1. **Visual inspection**
   - Instrument tag matches loop diagram
   - Cable/ferrule labels match drawings
   - Junction box connections tight
   - Glands sealed, covers in place

2. **Point-to-point verification**
   ```
   Field instrument terminals
       ↓ (verify ferrule labels)
   Field junction box
       ↓ (verify cable number)
   Marshalling cabinet
       ↓ (verify terminal numbers)
   PLC/DCS I/O card
   ```

3. **Continuity test**
   - Disconnect at both ends
   - Measure resistance: should be < 5Ω for signal wires
   - Check shield continuity (grounded at one end only)
   - Verify no shorts between conductors

4. **Insulation test** (if required)
   - 500V megger test
   - Minimum 1 MΩ insulation resistance

### Documentation
- Sign cold loop check column on loop check form
- Note any discrepancies on punch list
- Apply BLUE label to instrument (cold checked)

## Hot Loop Check Procedure

**Purpose**: Verify signal path with power applied

### Prerequisites
- [ ] Cold loop check complete
- [ ] Instrument powered and configured
- [ ] PLC/DCS channel configured
- [ ] HART communicator available (for smart instruments)
- [ ] Current loop simulator available
- [ ] Radio communication with control room

### 5-Point Test Methodology

Test at 0%, 25%, 50%, 75%, 100% of range in **both directions**:

| Input % | 4-20mA | Action |
|---------|--------|--------|
| 0% | 4.0 mA | Verify DCS shows 0% / LRV |
| 25% | 8.0 mA | Verify DCS shows 25% |
| 50% | 12.0 mA | Verify DCS shows 50% |
| 75% | 16.0 mA | Verify DCS shows 75% |
| 100% | 20.0 mA | Verify DCS shows 100% / URV |
| 75% | 16.0 mA | Verify decreasing (check hysteresis) |
| 50% | 12.0 mA | Verify decreasing |
| 25% | 8.0 mA | Verify decreasing |
| 0% | 4.0 mA | Verify returns to 0% |

### Procedure by Instrument Type

#### Analog Input (AI) - Transmitters

1. Connect HART communicator to transmitter
2. Verify configuration:
   - Tag number matches
   - Range matches datasheet (LRV, URV)
   - Engineering units correct
   - Damping appropriate
3. Simulate signal using HART (or apply physical input)
4. Verify DCS indication at each test point
5. Check alarms activate at setpoints:
   - Low alarm (if configured)
   - High alarm (if configured)
   - Low-low / High-high (if configured)

#### Analog Output (AO) - Control Valves

1. Verify valve fails to correct position (remove air/signal)
2. Command 0% from DCS → verify valve at 0% (or fail position)
3. Command 25%, 50%, 75%, 100% → verify valve position feedback
4. Verify positioner feedback matches command
5. Check stroke time acceptable
6. Verify limit switches (if fitted) operate at correct positions

#### Digital Input (DI) - Switches

1. Verify switch in normal state → DCS shows correct status
2. Actuate switch → DCS status changes
3. Verify correct state naming (OPEN/CLOSED, RUNNING/STOPPED)
4. Check alarm activates if configured

#### Digital Output (DO) - Solenoids/Relays

1. Command ON from DCS → verify device energizes
2. Command OFF from DCS → verify device de-energizes
3. Verify feedback status matches command
4. Check fail-safe state correct (power loss)

### Wire Break / Fail-Safe Test

1. Disconnect signal wire at field junction box
2. Verify DCS shows:
   - "Bad" or "Failed" status
   - Signal goes to fail value (< 4mA or > 20mA)
3. Verify fail alarm activates
4. Reconnect and verify normal operation restored

### Documentation
- Complete hot loop check columns on loop check form
- Record actual values at each test point
- Note any deviations or issues
- Apply GREEN label to instrument (loop checked)

## Loop Check Form Fields

| Field | Description |
|-------|-------------|
| Loop number | Unique loop identifier |
| Tag number | Instrument tag |
| Service description | Process function |
| P&ID reference | Drawing number and revision |
| Range | LRV - URV with units |
| Alarm setpoints | L, H, LL, HH values |
| Cold check | Date, initials, pass/fail |
| Hot check | Date, initials, pass/fail |
| Test points | Actual readings at 0/25/50/75/100% |
| Punch items | Issues requiring resolution |
| Sign-off | Technician, witness, date |

## Color Label System

| Color | Meaning | Applied After |
|-------|---------|---------------|
| BLUE | Pre-installation tested / Cold checked | Cold loop check |
| YELLOW | Pressure tested | Hydro/pneumatic test |
| GREEN | Loop tested | Hot loop check complete |
| RED | Loop test failed | Failed test (needs rework) |
| WHITE | Test failed - needs attention | Any failed test |

## Common Loop Check Failures

| Issue | Possible Cause | Resolution |
|-------|----------------|------------|
| No signal at DCS | Open circuit, wrong terminals | Trace wiring, check terminations |
| Reversed indication | Polarity reversed | Swap +/- connections |
| Wrong range | Configuration error | Update DCS/transmitter config |
| Erratic signal | Loose connection, noise | Tighten terminals, check shielding |
| Alarm not activating | Wrong setpoint, logic error | Verify configuration |
| Valve won't stroke | Air supply isolated, positioner fault | Check air supply, calibrate positioner |
| Feedback mismatch | Positioner not calibrated | Calibrate positioner feedback |

## Functional Test vs Loop Check

| Aspect | Loop Check | Functional Test |
|--------|------------|-----------------|
| **Scope** | Single instrument/loop | Complete control logic/interlock |
| **Purpose** | Signal integrity | Logic behavior |
| **Reference** | Loop diagram, datasheet | Control narrative, C&E matrix |
| **Example** | PT-101 reads correctly | PAHH-101 closes XV-101 |

## Cross-References

| Need | Resource |
|------|----------|
| Generating loop check lists from instrument list | `ssot-normalization.md` |
| Validating instrument list completeness | `validate_consistency.py` |
| C&E matrix review for functional tests | `cause-effect-review.md` |
