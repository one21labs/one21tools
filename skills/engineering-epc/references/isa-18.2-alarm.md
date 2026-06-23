# ISA-18.2 Alarm Management

Alarm system lifecycle management per ANSI/ISA-18.2-2016 and IEC 62682.

## Core Principle

> An alarm requires an operator response. If no response is needed, it should not be an alarm.

## Alarm Definition

All three criteria must be true for a valid alarm:

1. **Abnormal situation** — Indicates equipment malfunction, process deviation, or abnormal condition
2. **Requires response** — Operator must take action
3. **Time-critical** — Action needed within a defined response time

Items that fail these criteria should be:
- **Events** (logged but not alarmed)
- **Alerts** (informational, no immediate action)
- **Status messages** (normal state changes)

## Alarm Management Lifecycle

```
┌──────────────────────────────────────────────────────────────────┐
│                     ALARM PHILOSOPHY                              │
│         (Central document governing all stages)                   │
└────────────────────────────┬─────────────────────────────────────┘
                             │
    ┌────────────────────────┼────────────────────────────────┐
    │                        │                                │
    ▼                        ▼                                ▼
┌─────────┐            ┌─────────────┐              ┌────────────┐
│IDENTIFI-│───────────►│RATIONALI-   │─────────────►│DETAILED    │
│CATION   │            │ZATION       │              │DESIGN      │
└─────────┘            └─────────────┘              └────────────┘
    │                        │                            │
    │                        ▼                            │
    │              ┌─────────────────┐                    │
    │              │MASTER ALARM     │                    │
    │              │DATABASE (MAD)   │                    │
    │              └─────────────────┘                    │
    │                        │                            │
    ▼                        ▼                            ▼
┌─────────────┐      ┌─────────────┐              ┌─────────────┐
│IMPLEMENTATION│◄────│OPERATION    │◄─────────────│MAINTENANCE  │
└─────────────┘      └─────────────┘              └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │MONITORING & │
                     │ASSESSMENT   │
                     └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │MANAGEMENT   │
                     │OF CHANGE    │
                     └─────────────┘
```

## Alarm Philosophy Document

The alarm philosophy is the SSoT for alarm management. Required content:

| Section | Content |
|---------|---------|
| **Objectives** | Goals of the alarm system |
| **Definitions** | What constitutes an alarm vs event/alert |
| **Prioritization** | Priority levels and criteria |
| **Performance targets** | Alarm rate KPIs |
| **Roles & responsibilities** | Who owns alarm management |
| **Work processes** | Rationalization, MOC, suppression procedures |

### Priority Levels

| Priority | Criteria | Max Response Time | Example |
|----------|----------|-------------------|---------|
| **Critical/Emergency** | Imminent safety/environmental impact | < 5 min | PAHH on relief device |
| **High** | Significant process upset imminent | 5-10 min | Tank overflow imminent |
| **Medium** | Process deviation, time to respond | 10-30 min | Off-spec product |
| **Low** | Awareness, non-urgent | 30+ min | Filter differential high |

**Distribution target**: Approximately 5% Critical, 15% High, 25% Medium, 55% Low

## Alarm Identification

Sources for identifying required alarms:

| Source | Alarm Types |
|--------|-------------|
| **HAZOP** | Process hazard alarms |
| **LOPA/SIL** | Safety instrumented function alarms |
| **Equipment vendor** | Package unit alarms |
| **Operations experience** | Nuisance alarm removal, missing alarms |
| **Regulatory** | Required alarms per API, OSHA, etc. |

## Alarm Rationalization

Systematic review of each potential alarm against philosophy criteria.

### Rationalization Questions

For each alarm, document:

1. **Is it an alarm?** Does it meet all three criteria?
2. **What is the cause?** Root cause of the condition
3. **What is the consequence?** If operator doesn't respond
4. **What is the response?** What should operator do
5. **How much time?** Time available before consequence
6. **What priority?** Based on consequence and time

### Knock-Out Criteria (Remove if any apply)

| Criterion | Example | Action |
|-----------|---------|--------|
| No operator action required | Equipment status change | Convert to event |
| Duplicate of another alarm | Multiple alarms for same condition | Remove duplicate |
| Alarm on normal operation | Pump running | Remove or redesign |
| Operator cannot respond in time | Response time < process safety time | Requires SIF or redesign |
| Alarm point not in service | Abandoned equipment | Remove |

## Master Alarm Database (MAD)

The MAD is the SSoT for alarm configuration. All alarm changes flow through MAD.

### MAD Schema

See `schemas/canonical-schema.md` for full schema. Key fields:

| Field | Description | Required |
|-------|-------------|----------|
| `tag` | Instrument tag | ✓ |
| `alarm_type` | PAH, PAL, PAHH, etc. | ✓ |
| `setpoint` | Alarm setpoint value | ✓ |
| `setpoint_unit` | Engineering unit | ✓ |
| `priority` | Critical, High, Medium, Low | ✓ |
| `cause` | What causes this alarm | ✓ |
| `consequence` | What happens if ignored | ✓ |
| `operator_action` | Response procedure | ✓ |
| `response_time` | Time to respond (minutes) | ✓ |
| `deadband` | Alarm deadband | |
| `on_delay` | Time delay before alarming | |
| `off_delay` | Time delay before clearing | |
| `classification` | Environmental, Safety, Quality, etc. | |
| `sif_reference` | If part of SIF | |
| `rationalization_date` | When rationalized | |
| `rationalized_by` | Who rationalized | |

## Alarm System Performance Metrics

### Alarm Rate Targets (per operator position)

| Metric | Target | Maximum Acceptable |
|--------|--------|-------------------|
| Average alarms per 10 min | ≤ 1 | 2 |
| Average alarms per hour | ≤ 6 | 12 |
| Average alarms per day | ≤ 144 | 300 |
| Peak alarms per 10 min | ≤ 10 | - |

**Alarm flood**: > 10 alarms in 10 minutes

### Other KPIs

| Metric | Target |
|--------|--------|
| Chattering alarms | < 1% of total |
| Stale alarms (standing > 24 hr) | < 5 at any time |
| Frequently occurring (bad actors) | Top 10 addressed monthly |
| Suppressed alarms | All documented with expiry |
| Priority distribution | Matches philosophy targets |

## Nuisance Alarm Types

| Type | Definition | Resolution |
|------|------------|------------|
| **Chattering** | Alarms/clears > 3 times in 1 min | Add deadband or on-delay |
| **Fleeting** | Clears before operator can respond | Add on-delay |
| **Stale** | Remains in alarm > 24 hours | Fix condition or redesign |
| **Consequential** | Secondary alarm caused by primary | Suppress or state-based |
| **Bad actor** | In top 10 most frequent | Root cause analysis |

## State-Based Alarming

Alarms should be relevant to current operating state.

| Operating State | Alarm Behavior |
|-----------------|----------------|
| Startup | Suppress normal alarms, enable startup-specific |
| Normal operation | Full alarm set active |
| Shutdown | Suppress process alarms, enable shutdown-specific |
| Maintenance | Suppress equipment alarms (with documented bypass) |

## Alarm Suppression

### Suppression Types

| Type | Duration | Approval | Documentation |
|------|----------|----------|---------------|
| **Shelving** | Temporary (hours) | Operator | Log entry |
| **Out of service** | Extended (days) | Supervisor | MOC-lite |
| **Designed out** | Permanent | Engineering | Full MOC |

### Suppression Requirements

- All suppressions logged with reason, time, and responsible person
- Maximum suppression duration defined in philosophy
- Compensating measures documented
- Automatic expiry with reminder

## Integration with SIS

For alarms that are part of Safety Instrumented Functions:

| Aspect | Requirement |
|--------|-------------|
| Independence | SIS alarms may require separate display |
| Priority | SIS alarms typically High or Critical |
| Bypass | Subject to IEC 61511 bypass procedures |
| Testing | Included in SIF proof test |
| Documentation | Cross-reference SRS and MAD |

## Alarm Rationalization Workflow

```
1. Export current alarm configuration
           ↓
2. Load into MAD template
           ↓
3. For each alarm:
   - Apply knock-out criteria
   - Document cause/consequence/response
   - Assign priority per philosophy
   - Identify nuisance patterns
           ↓
4. Peer review by operations
           ↓
5. Approve changes via MOC
           ↓
6. Implement in DCS/PLC
           ↓
7. Update MAD as SSoT
           ↓
8. Monitor performance metrics
```

## Cross-References

| Need | Resource |
|------|----------|
| Alarm setpoint schema | `schemas/canonical-schema.md` |
| C&E matrix (for SIS alarms) | `workflows/cause-effect-review.md` |
| Commissioning (alarm testing) | `workflows/commissioning.md` |
| Full standard | ANSI/ISA-18.2-2016 |
| Technical reports | ISA-TR18.2.1 (Philosophy), TR18.2.2 (Rationalization) |
| International standard | IEC 62682 |
