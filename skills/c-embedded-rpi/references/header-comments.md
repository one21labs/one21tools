# Source File Header Comments for Context Engineering

Header comments that help both AI and humans understand code quickly.

## Principle: Right Altitude, Minimal Staleness

**Include:** Architectural role, design constraints, key patterns, navigation
**Avoid:** Line counts, test counts, function lists (go stale, easily discovered)

## Pattern for Implementation Files (.c)

```c
/*
 * module.c - One-line purpose
 *
 * ARCHITECTURE ROLE:
 *   How this file fits in the system. What it owns.
 *
 * DESIGN CONSTRAINTS:
 *   - Critical invariants that must be preserved
 *   - Performance requirements (e.g., "zero CPU when idle")
 *   - Resource constraints (e.g., "no dynamic allocation")
 *
 * KEY PATTERNS:
 *   Brief description of non-obvious patterns used.
 *   E.g., event loop design, state machine approach.
 *
 * TESTING:
 *   Where to find tests, testing approach (not counts).
 *
 * USED BY:
 *   - What calls this module (if not obvious)
 *
 * SEE ALSO:
 *   - Related files for navigation
 */
```

## Pattern for Header Files (.h)

```c
/*
 * module.h - One-line purpose
 *
 * ARCHITECTURE:
 *   Design pattern or approach (e.g., "Three-state Moore machine")
 *
 * USAGE PATTERN:
 *   1. init()
 *   2. In loop: query(), update()
 *   Brief sequence, not exhaustive API docs.
 *
 * IMPLEMENTATION:
 *   - module.c - What's there
 *   - tests/test_module.c - Testing approach
 *
 * SEE ALSO:
 *   - Integration example location
 */
```

## Pattern for Test Files

```c
/*
 * test_module.c - What's being tested
 *
 * TEST PHILOSOPHY:
 *   - Approach (e.g., "No mocking - pure functions")
 *   - Framework or custom macros used
 *
 * COVERAGE:
 *   - Categories tested (not counts)
 *   - Edge cases covered
 *
 * RUNNING:
 *   Commands to run tests
 *
 * SEE ALSO:
 *   - Implementation files under test
 */
```

## What NOT to Include

| Avoid | Why | Alternative |
|-------|-----|-------------|
| Line counts | Goes stale with every edit | Omit |
| Test counts | Goes stale | "Comprehensive tests" |
| Function lists | Duplicates header file | "See module.h" |
| Detailed API docs | Belongs in function comments | Reference header |
| ASCII diagrams | Often go stale | Reference ARCHITECTURE.md |

## Real Example (touch-timeout)

```c
/*
 * main.c - Touch-timeout daemon entry point and I/O layer
 *
 * ARCHITECTURE ROLE:
 *   I/O and platform layer wrapping the pure state machine (state.c).
 *   Owns: CLI parsing, device discovery, sysfs/input I/O, event loop, signals.
 *
 * DESIGN CONSTRAINTS:
 *   - Zero CPU when idle: Uses blocking poll() with timeout from state machine
 *   - Zero writes when idle: Caches brightness to avoid redundant sysfs writes
 *   - No dynamic allocation: Fixed buffers with compile-time bounds checking
 *   - Monotonic time only: CLOCK_MONOTONIC for wraparound-safe timeouts
 *
 * EVENT LOOP DESIGN:
 *   1. poll() blocks on /dev/input/eventX with timeout from state_get_timeout_sec()
 *   2. On POLLIN: drain_touch_events() → state_touch() → set_brightness() if changed
 *   3. On timeout: state_timeout() → set_brightness() if changed
 *   4. On SIGUSR1: state_touch() to wake display (external integration)
 *   5. On SIGTERM/SIGINT: g_running=false → cleanup → exit
 *
 * MODULE INTERFACE:
 *   Calls state.c API - pure functions where caller provides timestamps.
 *   See state.h for complete interface.
 *
 * TESTING:
 *   Unit tests: tests/test_state.c (tests state machine only)
 *   Integration tests: scripts/test-integration.sh
 *
 * SEE ALSO:
 *   - doc/ARCHITECTURE.md - System architecture overview
 *   - systemd/touch-timeout.service - Systemd integration
 */
```

## Benefits

1. **First file read gives context** - No hunting through multiple files
2. **Design constraints explicit** - Know what NOT to break
3. **Navigation embedded** - "SEE ALSO" points to related files
4. **Testing discoverable** - Know where/how to test changes
5. **Staleness minimized** - Avoids counts and lists that change
