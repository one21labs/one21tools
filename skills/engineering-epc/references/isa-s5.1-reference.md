# ISA S5.1 Reference

Instrument symbols and identification per ANSI/ISA-5.1-2024.

## Tag Structure

```
[First Letter][Succeeding Letters]-[Loop Number][Suffix]
     ↓              ↓                    ↓         ↓
  Measured      Function            Sequence   Redundancy
  Variable      (I, C, T, etc.)     Number     (A, B, C)
```

### Examples

| Tag | First Letter | Succeeding | Number | Suffix | Meaning |
|-----|--------------|------------|--------|--------|---------|
| FIC-101 | F (Flow) | IC (Indicating Controller) | 101 | - | Flow Indicating Controller, loop 101 |
| PT-201A | P (Pressure) | T (Transmitter) | 201 | A | Pressure Transmitter, loop 201, first redundant |
| LAHH-301 | L (Level) | AHH (Alarm High-High) | 301 | - | Level Alarm High-High, loop 301 |
| TIC-100-401 | T (Temperature) | IC | 100-401 | - | Temperature Controller, area 100, loop 401 |

## First Letter (Measured/Initiating Variable)

The first letter identifies what is being measured or initiates the action.

| Letter | Measured Variable |
|--------|-------------------|
| A | Analysis (composition, pH, conductivity) |
| B | Burner/Combustion |
| C | User's Choice (commonly Conductivity) |
| D | User's Choice (commonly Density) |
| E | Voltage |
| F | Flow |
| G | User's Choice (commonly Gauging/Position) |
| H | Hand (manual) |
| I | Current (electrical) |
| J | Power |
| K | Time/Schedule |
| L | Level |
| M | User's Choice (commonly Moisture) |
| N | User's Choice |
| O | User's Choice |
| P | Pressure/Vacuum |
| Q | Quantity (totalizer) |
| R | Radiation |
| S | Speed/Frequency |
| T | Temperature |
| U | Multivariable |
| V | Vibration |
| W | Weight/Force |
| X | Unclassified |
| Y | Event/State/Presence |
| Z | Position/Dimension |

## Succeeding Letters (Modifier/Readout/Output)

Succeeding letters describe the function performed.

| Letter | Modifier | Readout/Passive | Output/Active |
|--------|----------|-----------------|---------------|
| A | - | Alarm | - |
| B | User's Choice | User's Choice | User's Choice |
| C | - | - | Control |
| D | Differential | - | - |
| E | Primary Element | - | - |
| F | Ratio (Fraction) | - | - |
| G | Glass/Gauge | - | - |
| H | High | - | - |
| I | - | Indicate | - |
| J | - | - | Scan |
| K | Time Rate of Change | - | Control Station |
| L | Low | Light | - |
| M | Middle/Intermediate | - | - |
| N | User's Choice | User's Choice | User's Choice |
| O | Orifice/Restriction | - | - |
| P | - | Point (test) | - |
| Q | Integrate/Totalize | - | - |
| R | - | Record | - |
| S | Safety | - | Switch |
| T | - | Transmit | - |
| U | Multifunction | Multifunction | Multifunction |
| V | - | - | Valve/Damper |
| W | Well/Probe | - | - |
| X | Unclassified | Unclassified | Unclassified |
| Y | - | - | Relay/Compute |
| Z | - | - | Driver/Actuator |

## Common Tag Combinations

| Tag Pattern | Description | Example |
|-------------|-------------|---------|
| PT | Pressure Transmitter | PT-101 |
| PIC | Pressure Indicating Controller | PIC-101 |
| PICA | Pressure Indicating Controller with Alarm | PICA-101 |
| PAH | Pressure Alarm High | PAH-101 |
| PAHH | Pressure Alarm High-High | PAHH-101 |
| PSH | Pressure Switch High | PSH-101 |
| PSHH | Pressure Switch High-High | PSHH-101 |
| PV | Pressure Valve (control valve) | PV-101 |
| FT | Flow Transmitter | FT-201 |
| FIC | Flow Indicating Controller | FIC-201 |
| FE | Flow Element (orifice plate) | FE-201 |
| FO | Flow Orifice | FO-201 |
| LT | Level Transmitter | LT-301 |
| LIC | Level Indicating Controller | LIC-301 |
| LG | Level Gauge (sight glass) | LG-301 |
| LSH | Level Switch High | LSH-301 |
| TT | Temperature Transmitter | TT-401 |
| TIC | Temperature Indicating Controller | TIC-401 |
| TE | Temperature Element (RTD, TC) | TE-401 |
| TW | Temperature Well (thermowell) | TW-401 |

## Equipment Tag Prefixes

Single-letter prefixes typically denote equipment (not instruments).

| Prefix | Equipment Type | Example |
|--------|----------------|---------|
| V | Vessel (separator, scrubber, drum) | V-101 |
| P | Pump | P-201A |
| C | Compressor | C-301 |
| E | Heat Exchanger | E-401 |
| H | Heater (fired) | H-501 |
| T | Tower/Column | T-101 |
| R | Reactor | R-101 |
| F | Filter | F-201 |
| D | Drum | D-301 |
| K | Compressor (alternate) | K-101 |

## Suffix Conventions

| Suffix | Meaning |
|--------|---------|
| A, B, C | Redundant/parallel equipment (first, second, third) |
| 1, 2, 3 | Alternate numbering for redundancy |
| N, S, E, W | Location (North, South, East, West) |
| I, O | Inlet, Outlet |

## Line Numbering

Typical format: `[Size]-[Service]-[Sequence]-[Spec]`

| Component | Description | Example |
|-----------|-------------|---------|
| Size | Nominal pipe size (inches or mm) | 4 |
| Service | Fluid service code | HC (hydrocarbon) |
| Sequence | Unique number | 001 |
| Spec | Piping specification | A1 |

**Example**: `4"-HC-001-A1` = 4-inch hydrocarbon line, sequence 001, spec A1

## Validation Rules

Scripts should validate:

1. **First letter** must be in the first letter table
2. **Succeeding letters** should be in the succeeding letters table
3. **Separator** should be hyphen (preferred) or underscore
4. **Loop number** should be 3+ digits
5. **Suffix** should be single uppercase letter (A-Z) for redundancy

## Cross-References

| Need | Resource |
|------|----------|
| Tag format validation | `scripts/validate_tag_format.py` |
| P&ID tag extraction | `scripts/extract_dxf_tags.py` |
| Full standard | ANSI/ISA-5.1-2024 (purchase required) |
| Loop diagrams | ISA-5.4-1991 |
| Specification forms | ISA-TR20.00.01 |
