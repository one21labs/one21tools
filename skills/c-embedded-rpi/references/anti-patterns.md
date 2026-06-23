# Anti-Patterns: Code That Works by Accident

Real issues found in production-ready embedded C code. These patterns compile and run but are fragile, non-portable, or hide bugs.

## Integer Arithmetic

### Cast Timing in Multiplication

```c
/* BAD: Cast happens AFTER overflow (int * int * int, then cast) */
uint32_t dim_ms = (uint32_t)cfg.timeout_sec * cfg.dim_percent * 10;

/* GOOD: Cast at least one operand before operation */
uint32_t off_ms = (uint32_t)cfg.timeout_sec * 1000U;
uint32_t dim_ms = (off_ms * (uint32_t)cfg.dim_percent) / 100U;
```

**Why:** In C, `int * int` is computed as `int`, can overflow before cast applies. Per CERT C INT02-C, casting one operand triggers usual arithmetic conversions, promoting both to the wider type. Project convention: cast first operand for consistency.

### Missing Unsigned Suffixes

```c
/* BAD: 1000 is int, multiplication happens in int */
uint32_t timeout_ms = timeout_sec * 1000;

/* GOOD: 1000U forces unsigned arithmetic (MISRA C:2012 Rule 7.2) */
uint32_t timeout_ms = timeout_sec * 1000U;
```

### Type Width Mismatches in Comparisons

```c
/* BAD: Comparing different-width types */
ssize_t written = write(fd, buf, len);
if (written != len) {  /* int vs ssize_t - truncation risk */

/* GOOD: Explicit cast shows intent */
if (written != (ssize_t)len) {
```

## Error Handling

### Unchecked System Call Returns

```c
/* BAD: Ignoring failures */
sigaction(SIGTERM, &sa, NULL);
snprintf(path, sizeof(path), "%s/%s", dir, name);
write(fd, buf, len);

/* GOOD: Check every system call */
if (sigaction(SIGTERM, &sa, NULL) < 0) {
    log_err("sigaction failed: %s", strerror(errno));
    return EXIT_FAILURE;
}

int n = snprintf(path, sizeof(path), "%s/%s", dir, name);
if (n < 0 || n >= (int)sizeof(path)) {
    log_err("path truncated");
    return -1;
}
```

### Silent Failures in Main Loop

```c
/* BAD: Ignoring write failure, continuing with stale cache */
if (new_bright >= 0 && new_bright != cached_brightness) {
    set_brightness(bl_fd, new_bright);
    cached_brightness = new_bright;  /* Updated even if write failed! */
}

/* GOOD: Only update cache on success */
if (new_bright >= 0 && new_bright != cached_brightness) {
    if (set_brightness(bl_fd, new_bright) == 0) {
        cached_brightness = new_bright;
    }
}
```

## Modern C Idioms

### Old-Style Struct Initialization

```c
/* BAD: Verbose, error-prone */
struct sigaction sa;
memset(&sa, 0, sizeof(sa));
sa.sa_handler = handle_signal;

/* GOOD: C99 brace initialization, zero-initialized */
struct sigaction sa = {0};
sa.sa_handler = handle_signal;

/* ALSO GOOD: Designated initializer */
struct sigaction sa = {
    .sa_handler = handle_signal
};
```

**Note:** `= {0}` does not zero padding bytes for automatic storage. Use `memset` when passing structs across privilege boundaries or when padding must be zeroed (e.g., network protocols, security contexts).

### Incomplete Switch on Enum

```c
/* BAD: Unreachable code after exhaustive switch */
switch (st->state) {
    case STATE_FULL: return brightness_full;
    case STATE_DIMMED: return brightness_dim;
    case STATE_OFF: return 0;
}
return -1;  /* Unreachable - confuses static analyzers */

/* GOOD (MISRA): default inside switch */
switch (st->state) {
    case STATE_FULL: return brightness_full;
    case STATE_DIMMED: return brightness_dim;
    case STATE_OFF: return 0;
    default: return -1;  /* Defensive, handles invalid state */
}
```

**Trade-off:** MISRA C:2004 Rule 15.3 mandates `default:` for defensive programming (enum values can be corrupted at runtime). However, this silences `-Wswitch` compiler warnings that catch missing cases when enums are extended. Some projects deviate from MISRA here to preserve compiler exhaustiveness checks.

## Compile-Time Safety

### Missing Static Assertions

```c
/* BAD: Runtime overflow possible */
int timeout_ms = timeout_sec * 1000;  /* Overflows if timeout_sec > ~2M */

/* GOOD: Prove bounds at compile time */
#define MAX_TIMEOUT_SEC 86400
_Static_assert(MAX_TIMEOUT_SEC <= INT_MAX / 1000,
               "MAX_TIMEOUT_SEC too large for poll() timeout");

/* Now safe because we validated the range */
if (timeout_sec <= MAX_TIMEOUT_SEC) {
    int timeout_ms = timeout_sec * 1000;
}
```

### Buffer Size Relationships

```c
/* BAD: Sizes unrelated, easy to break */
#define NAME_LEN 64
#define PATH_LEN 128  /* Is this enough? Who knows */

/* GOOD: Derive from components */
#define MAX_NAME_LEN 64
#define PATH_BUFFER_LEN (sizeof("/sys/class/backlight/") + MAX_NAME_LEN + sizeof("/brightness"))

_Static_assert(PATH_BUFFER_LEN < 256, "path buffer unexpectedly large");
```

## Documentation Gaps

### Undocumented Intentional Behavior

```c
/* BAD: Why uint32_t? Why not uint64_t? */
static uint32_t now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint32_t)(ts.tv_sec * 1000 + ts.tv_nsec / 1000000);
}

/* GOOD: Document the design decision */
/*
 * Get current time in milliseconds (CLOCK_MONOTONIC).
 * Returns uint32_t which wraps every ~49.7 days.
 * Wraparound is intentional: subtraction still yields correct elapsed time
 * due to unsigned arithmetic. See test_wraparound_handling in test suite.
 */
static uint32_t now_ms(void) { ... }
```

### Missing API Preconditions

```c
/* BAD: Caller doesn't know constraints */
void state_init(state_s *st, int brightness_full, int brightness_dim,
                uint32_t dim_timeout_ms, uint32_t off_timeout_ms);

/* GOOD: Preconditions documented */
/*
 * Initialize state machine.
 *
 * Preconditions (caller must ensure):
 *   - brightness_full >= 0, brightness_dim >= 0
 *   - dim_timeout_ms < off_timeout_ms
 *   - off_timeout_ms <= INT_MAX (for poll() compatibility)
 */
void state_init(state_s *st, int brightness_full, int brightness_dim,
                uint32_t dim_timeout_ms, uint32_t off_timeout_ms);
```

## Checklist: Before Code Review

| Category | Check | Source |
|----------|-------|--------|
| Arithmetic | Cast at least one operand before multiplication | CERT C INT02-C |
| Arithmetic | Unsigned suffixes (1000U, 100U) | MISRA C:2012 Rule 7.2 |
| Arithmetic | Type widths match in comparisons | CERT C INT31-C |
| Safety | `_Static_assert` for bounded calculations | CERT C INT32-C |
| Errors | All system calls return values checked | CERT C ERR33-C |
| Errors | Cache/state updated only on success | — |
| Idioms | `= {0}` initialization (memset for padding) | — |
| Idioms | `default:` in enum switches | MISRA C:2004 Rule 15.3 |
| Docs | Non-obvious behavior documented | — |
| Docs | API preconditions in headers | — |
