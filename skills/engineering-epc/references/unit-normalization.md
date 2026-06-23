# Unit Normalization

Single source of truth for engineering unit normalization. Scripts and workflows reference this file.

## Purpose

1. **Consistency** — Same unit variations map to same canonical form
2. **Comparison** — Scripts can compare values with different unit spellings
3. **Data quality** — Normalized units enable validation

## Normalization Rules

1. Convert to canonical form (case-sensitive as shown)
2. Preserve gauge/absolute distinction where present
3. Flag for review if unit is unrecognized

## Pressure Units

| Canonical | Accepted Variations |
|-----------|---------------------|
| `psig` | psi g, psi(g), PSI G, PSIG, PSI(G), psi-g |
| `psia` | psi a, psi(a), PSI A, PSIA, PSI(A), psi-a |
| `psi` | PSI (when gauge/absolute unspecified) |
| `kPag` | kPa g, kPa(g), KPA G, KPAG, KPA(G), kPa-g |
| `kPaa` | kPa a, kPa(a), KPA A, KPAA, KPA(A), kPa-a |
| `kPa` | KPA, kpa (when gauge/absolute unspecified) |
| `MPa` | mpa, MPA |
| `bar` | BAR, Bar |
| `barg` | bar g, bar(g), BAR G, BARG |
| `bara` | bar a, bar(a), BAR A, BARA |
| `mbar` | MBAR, millibar |
| `inH2O` | in H2O, "H2O, inches H2O, in wc, inwc, in WC |
| `mmH2O` | mm H2O, mmH2O, mm wc |
| `inHg` | in Hg, "Hg, inches Hg |
| `mmHg` | mm Hg, torr, Torr |
| `atm` | ATM, atmosphere |

## Temperature Units

| Canonical | Accepted Variations |
|-----------|---------------------|
| `degC` | °C, deg C, Deg C, C, celsius, Celsius, DEGC |
| `degF` | °F, deg F, Deg F, F, fahrenheit, Fahrenheit, DEGF |
| `K` | kelvin, Kelvin, KELVIN |
| `degR` | °R, deg R, Rankine |

## Flow Units

### Volumetric

| Canonical | Accepted Variations |
|-----------|---------------------|
| `GPM` | gpm, gal/min, gallons/min, USGPM, US GPM |
| `m3/h` | m³/h, m3/hr, M3/H, CMH, cmh, cu m/h |
| `m3/d` | m³/d, m3/day, CMD, cmd |
| `L/min` | l/min, lpm, LPM, liters/min |
| `L/h` | l/h, lph, LPH, liters/hr |
| `bbl/d` | bpd, BPD, BOPD, bbl/day, barrels/day |
| `MMSCFD` | mmscfd, MMscfd, million scf/d |
| `MSCFH` | mscfh, Mscfh, thousand scf/h |
| `Nm3/h` | nm3/h, normal m3/h |
| `ACFM` | acfm, actual cfm |
| `SCFM` | scfm, standard cfm |

### Mass

| Canonical | Accepted Variations |
|-----------|---------------------|
| `kg/h` | kg/hr, KG/H, kilograms/hr |
| `kg/s` | kg/sec, KG/S |
| `lb/h` | lb/hr, LB/H, pounds/hr, pph |
| `t/h` | T/H, tonnes/hr, metric tons/hr |
| `TPD` | t/d, tonnes/day |

## Level Units

| Canonical | Accepted Variations |
|-----------|---------------------|
| `%` | percent, Percent, PCT, pct |
| `mm` | MM, millimeter, millimeters |
| `m` | M, meter, meters, metre |
| `in` | ", inches, inch |
| `ft` | ', feet, foot |

## Electrical Units

| Canonical | Accepted Variations |
|-----------|---------------------|
| `mA` | ma, milliamps, milliamp, mADC |
| `V` | volt, volts, VDC, VAC |
| `VDC` | v dc, V DC, volts DC |
| `VAC` | v ac, V AC, volts AC |
| `A` | amp, amps, ampere |
| `kW` | KW, kilowatt, kilowatts |
| `HP` | hp, horsepower |
| `Hz` | hz, hertz, Hertz |
| `Ω` | ohm, ohms, OHM |

## Analytical Units

| Canonical | Accepted Variations |
|-----------|---------------------|
| `ppm` | PPM, parts per million |
| `ppb` | PPB, parts per billion |
| `mg/L` | mg/l, milligrams/liter |
| `pH` | PH |
| `mS/cm` | mS, millisiemens/cm, conductivity |
| `NTU` | ntu, turbidity |

## Concentration Units

| Canonical | Accepted Variations |
|-----------|---------------------|
| `mol%` | mole %, mole percent |
| `wt%` | weight %, mass % |
| `vol%` | volume % |
| `g/L` | g/l, grams/liter |
| `lb/gal` | pounds/gallon |

## Time Units

| Canonical | Accepted Variations |
|-----------|---------------------|
| `s` | sec, seconds, second |
| `min` | minutes, minute, mins |
| `h` | hr, hrs, hours, hour |
| `d` | day, days |

## Speed/Frequency Units

| Canonical | Accepted Variations |
|-----------|---------------------|
| `RPM` | rpm, rev/min, revolutions/min |
| `m/s` | meters/sec, m/sec |
| `ft/s` | fps, feet/sec |

## Other Common Units

| Canonical | Accepted Variations |
|-----------|---------------------|
| `kg` | KG, kilogram, kilograms |
| `lb` | LB, pound, pounds |
| `ton` | short ton, US ton |
| `tonne` | metric ton, t |
| `N` | newton, newtons |
| `kN` | kilonewton |
| `Nm` | N-m, newton-meter |
| `kg/m3` | kg/m³, kilograms/cubic meter |
| `lb/ft3` | pounds/cubic foot |
| `cP` | centipoise, cp |
| `cSt` | centistokes, cst |

## Signal Types

| Canonical | Accepted Variations |
|-----------|---------------------|
| `4-20mA` | 4-20 mA, 4-20MA, 4 to 20 mA |
| `1-5VDC` | 1-5 VDC, 1-5V |
| `0-10VDC` | 0-10 VDC, 0-10V |
| `HART` | hart |
| `Modbus` | MODBUS, modbus |
| `Foundation Fieldbus` | FF, fieldbus |
| `PROFIBUS` | profibus, Profibus |
| `Discrete` | digital, on/off, DI, DO |

## Boolean/Status Values

| Canonical | Accepted Variations |
|-----------|---------------------|
| `OPEN` | Open, open, O, 1 (for valves) |
| `CLOSED` | Closed, closed, C, 0 (for valves) |
| `RUNNING` | Running, running, RUN, 1 (for motors) |
| `STOPPED` | Stopped, stopped, STOP, 0 (for motors) |
| `YES` | Yes, yes, Y, TRUE, True, 1 |
| `NO` | No, no, N, FALSE, False, 0 |
| `ENABLED` | Enabled, enabled, ON |
| `DISABLED` | Disabled, disabled, OFF |

## Fail Mode Values

| Canonical | Accepted Variations |
|-----------|---------------------|
| `FC` | Fail Closed, fail closed, fail-closed, FTC |
| `FO` | Fail Open, fail open, fail-open, FTO |
| `FL` | Fail Last, fail last, fail-last, FIP, fail in place |
| `FS` | Fail Safe, fail safe |

## Implementation Notes

### Scripts Should:

1. **Normalize on input** — Convert to canonical form when loading
2. **Compare normalized** — Use canonical forms for comparison
3. **Preserve original** — Store original value for reference
4. **Flag unknown** — Report unrecognized units as warnings

### Example Normalization Function

```python
def normalize_unit(unit: str) -> str:
    """Normalize unit to canonical form."""
    if not unit:
        return ""
    
    unit = str(unit).strip()
    
    # Pressure
    if unit.lower() in ['psi g', 'psi(g)', 'psig']:
        return 'psig'
    if unit.lower() in ['kpa g', 'kpa(g)', 'kpag']:
        return 'kPag'
    
    # Temperature
    if unit.lower() in ['°c', 'deg c', 'c', 'celsius', 'degc']:
        return 'degC'
    if unit.lower() in ['°f', 'deg f', 'f', 'fahrenheit', 'degf']:
        return 'degF'
    
    # ... continue for other units
    
    return unit  # Return as-is if not recognized
```

## Cross-References

| Need | Resource |
|------|----------|
| Script implementation | `scripts/validate_consistency.py` |
| Column schemas | `schemas/canonical-schema.md` |
| Normalization workflow | `workflows/data-normalization.md` |
