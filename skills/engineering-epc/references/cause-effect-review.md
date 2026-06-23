# Cause & Effect Matrix Review

Procedures for reviewing and validating C&E matrices against control narratives, P&IDs, and instrument lists per IEC 62881 and IEC 61511.

## C&E Matrix Structure

A Cause & Effect matrix defines safety and control logic in tabular form:

```
             │ Effect 1   │ Effect 2   │ Effect 3   │
             │ Close XV-101│ Trip P-101 │ Alarm      │
─────────────┼────────────┼────────────┼────────────┤
Cause 1      │            │            │            │
PAHH-101     │     X      │     X      │     X      │
─────────────┼────────────┼────────────┼────────────┤
Cause 2      │            │            │            │
LAHH-101     │     X      │            │     X      │
─────────────┼────────────┼────────────┼────────────┤
Cause 3      │            │            │            │
Manual ESD   │     X      │     X      │            │
```

### Matrix Components

| Component | Location | Content |
|-----------|----------|---------|
| **Causes** | Rows | Process deviations (PAHH, LAHH, TAHH, etc.) or manual actions |
| **Effects** | Columns | Actions (close valve, trip pump, activate alarm, etc.) |
| **Cells** | Intersections | Logic relationship (X, AND, OR, time delay) |
| **Notes** | Footer/margin | Voting logic, bypass conditions, time delays |

### Cell Notation

| Symbol | Meaning |
|--------|---------|
| X | Direct activation (cause triggers effect) |
| (blank) | No relationship |
| AND | Requires multiple causes (noted in margin) |
| OR | Any of multiple causes (default for multiple X in column) |
| T=5s | Time delay before action |
| 2oo3 | 2 out of 3 voting logic |
| L | Latching (requires manual reset) |
| * | See notes |

## C&E Normalization Workflow

### Step 1: Extract C&E to SSoT Format

Convert C&E matrix xlsx to structured CSV:

```csv
cause_tag,cause_description,effect_tag,effect_description,logic,time_delay,voting,notes
PAHH-101,Separator pressure high-high,XV-101,Inlet isolation valve,CLOSE,0,1oo1,
PAHH-101,Separator pressure high-high,P-101,Feed pump,TRIP,0,1oo1,
LAHH-101,Separator level high-high,XV-101,Inlet isolation valve,CLOSE,0,1oo1,
ESD-MAN,Manual ESD pushbutton,XV-101,Inlet isolation valve,CLOSE,0,1oo1,Latching
```

### Step 2: Normalize Tags and Actions

Standardize terminology:

| Input Variations | Canonical |
|------------------|-----------|
| Close, CL, CLOSE, close valve | CLOSE |
| Trip, TRIP, Stop, STOP | TRIP |
| Open, OP, OPEN | OPEN |
| Start, START, Run | START |
| Alarm, ALM, Annunciate | ALARM |

## Cross-Check Requirements

### 1. C&E vs Instrument List

**Every cause tag must exist in instrument list:**

```
C&E Cause Tags          Instrument List Tags
─────────────────       ──────────────────────
PAHH-101         ─────► PT-101 (alarm PAHH-101) ✓
LAHH-101         ─────► LT-101 (alarm LAHH-101) ✓
TAHH-102         ─────► (not found) ✗ FLAG
```

**Check for:**
- Missing tags (C&E references instrument not in list)
- Alarm type mismatch (C&E says PAHH but instrument is PAH)
- Range consistency (alarm setpoint within instrument range)

### 2. C&E vs Control Narrative

**Logic must match narrative description:**

| C&E States | Control Narrative States | Check |
|------------|-------------------------|-------|
| PAHH-101 closes XV-101 | "On high-high pressure (PAHH-101), inlet valve XV-101 closes" | ✓ Match |
| LAHH-101 trips P-101 | "On high level, pump P-101 trips" | ✓ Match |
| TAHH-102 closes XV-101 | (not mentioned in narrative) | ✗ FLAG |

**Check for:**
- Actions in C&E not described in narrative
- Actions in narrative not in C&E
- Logic differences (AND vs OR, time delays)
- Setpoint values match

### 3. C&E vs P&ID

**All effect devices must be shown on P&ID:**

```
C&E Effect Tags         P&ID Tags
───────────────         ─────────
XV-101           ─────► XV-101 shown ✓
P-101            ─────► P-101 shown ✓
XV-103           ─────► (not on P&ID) ✗ FLAG
```

**Check for:**
- Valves shown with correct fail position
- Shutdown valves have correct symbology (XV not just V)
- Interlock lines shown (dashed) between cause and effect
- ESD boundary shown if applicable

### 4. C&E vs IO List

**All cause inputs and effect outputs must be wired:**

| C&E Item | IO List Check |
|----------|---------------|
| PAHH-101 (cause) | DI or AI with alarm configured |
| XV-101 (effect) | DO for solenoid or AO for actuator |
| P-101 trip (effect) | DO to motor starter |

**Check for:**
- Missing IO points
- Wrong IO type (DI vs AI, DO vs AO)
- Sufficient channels for voting (2oo3 needs 3 inputs)

## Voting Logic Verification

### 1oo1 (One out of One)
- Single sensor triggers action
- No redundancy
- Used for non-critical alarms

### 1oo2 (One out of Two)
- Either sensor triggers action
- Maximum safety, higher spurious trip rate
- Check: 2 instruments in instrument list

### 2oo2 (Two out of Two)
- Both sensors must agree to trigger
- Minimum spurious trips, lower safety
- Rarely used for safety functions

### 2oo3 (Two out of Three)
- Any 2 of 3 sensors trigger action
- Balance of safety and availability
- Check: 3 instruments in instrument list
- Common for SIL 2/3 functions

**Verification:**
```
C&E shows: 2oo3 voting for PAHH-101

Instrument list must have:
- PT-101A (PAHH-101A)
- PT-101B (PAHH-101B)
- PT-101C (PAHH-101C)

If only 2 transmitters found → FLAG discrepancy
```

## Common C&E Discrepancies

| Discrepancy | Impact | Resolution |
|-------------|--------|------------|
| Cause tag not in instrument list | Shutdown logic can't execute | Add instrument or correct tag |
| Effect valve not on P&ID | Valve may not exist or wrong tag | Verify P&ID, update C&E |
| Voting mismatch | SIL not achieved | Add required redundancy |
| Time delay not in narrative | Operator confusion | Update narrative or C&E |
| Bypass not documented | Uncontrolled bypass risk | Add bypass logic to C&E |
| Reset logic unclear | Stuck in shutdown state | Document reset requirements |

## SIS/SIF Verification Touchpoints

For Safety Instrumented Functions (per IEC 61511):

| Item | Verification |
|------|--------------|
| SIF identified | Documented in Safety Requirements Specification |
| SIL assigned | Based on LOPA or risk graph |
| Architecture | 1oo1, 1oo2, 2oo3 matches SIL requirement |
| Response time | Time delay meets process safety time |
| Proof test interval | Documented in C&E or separate procedure |
| Bypass procedure | Documented with compensating measures |

## C&E Review Checklist

### Completeness
- [ ] All P&ID shutdown valves appear as effects
- [ ] All high-high/low-low alarms appear as causes
- [ ] Manual ESD pushbuttons included
- [ ] Fire & gas inputs included (if applicable)
- [ ] All effects have at least one cause

### Consistency
- [ ] Cause tags match instrument list exactly
- [ ] Effect tags match P&ID exactly
- [ ] Voting logic matches instrument count
- [ ] Time delays documented and justified
- [ ] Fail positions consistent with P&ID

### Logic
- [ ] AND/OR logic clearly indicated
- [ ] Latching requirements documented
- [ ] Reset requirements documented
- [ ] Bypass conditions documented
- [ ] Permissives documented (for start sequences)

### Documentation
- [ ] C&E revision matches control narrative revision
- [ ] HAZOP action items addressed
- [ ] SIL verification complete (for SIS)
- [ ] Witness signatures obtained

## Output: Discrepancy Report

Generate discrepancy CSV:

```csv
source,target,tag,issue_type,details,severity
C&E,Instrument List,TAHH-102,missing_tag,Tag in C&E but not in instrument list,error
C&E,Control Narrative,XV-101,logic_mismatch,C&E shows 5s delay but narrative says immediate,warning
C&E,P&ID,XV-103,missing_device,Effect valve not shown on P&ID,error
C&E,IO List,PAHH-101,voting_mismatch,C&E shows 2oo3 but only 2 inputs in IO list,error
```

## Cross-References

| Need | Resource |
|------|----------|
| Normalize messy C&E xlsx | `ssot-normalization.md` |
| Validate tag formats | `validate_tag_format.py` |
| Compare to instrument list | `validate_consistency.py` |
| Loop check from C&E | `commissioning.md` |
