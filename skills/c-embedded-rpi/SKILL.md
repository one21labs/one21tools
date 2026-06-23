---
name: c-embedded-rpi
description: Use when the user asks to "review C code", "check C code", "audit embedded C", "write C code for Raspberry Pi", "create an RPi daemon", "implement embedded C", "write sysfs code", "create a Linux input handler", or works on C code targeting Raspberry Pi with backlight, GPIO, input subsystem, or systemd integration. Also applies during code review for quality, safety patterns, and best practices compliance.
---

# Embedded C Best Practices for Raspberry Pi

Modern, maintainable C patterns for Raspberry Pi embedded Linux development. Focus: prevent bugs through consistent patterns, not through over-engineering.

## Core Principles

1. **Clear over clever** - Readable code prevents bugs
2. **Compile-time safety** - Catch errors before runtime when possible
3. **Consistent patterns** - Same problems, same solutions
4. **Minimal complexity** - Only add what's needed

## Buffer and String Safety

### Named Buffer Sizes

Define all buffer sizes as named constants with clear relationships:

```c
/* BAD: Magic numbers scattered in code */
char path[128];
char buf[64];
snprintf(path, 128, "%s/%s", dir, name);

/* GOOD: Named constants with derived sizes */
#define MAX_DEVICE_NAME_LEN  64
#define SYSFS_VALUE_LEN      16
/* Path: dir + "/" + name + "/brightness" + null */
#define PATH_BUFFER_LEN      (sizeof(SYSFS_BACKLIGHT_DIR) + 1 + MAX_DEVICE_NAME_LEN + 16)

char path[PATH_BUFFER_LEN];
char device[MAX_DEVICE_NAME_LEN];
```

### Compile-Time Buffer Validation

Use `_Static_assert` to verify buffer size relationships:

```c
/* Verify path buffer can hold longest path */
_Static_assert(PATH_BUFFER_LEN >= sizeof(SYSFS_DIR) + 1 + MAX_NAME_LEN + sizeof("/max_brightness"),
               "PATH_BUFFER_LEN too small for sysfs paths");

/* Verify timeout fits in poll() parameter */
_Static_assert(MAX_TIMEOUT_SEC <= INT_MAX / 1000,
               "MAX_TIMEOUT_SEC too large for poll() timeout");
```

### String Functions: snprintf and strscpy

Always use `snprintf()` — it guarantees null-termination. On Linux 5.10+ (Raspberry Pi OS Bullseye+), prefer `strscpy()` where available: it always NUL-terminates, returns character count or `-E2BIG` on truncation, and is the Linux kernel standard (`strncpy` was removed from the kernel in v7.2):

```c
/* Preferred on modern Linux — explicit truncation detection */
ssize_t ret = strscpy(dst, src, sizeof(dst));
if (ret == -E2BIG) {
    log_err("name truncated");
    return -1;
}
```

Fall back to `snprintf()` for portability or when strscpy is unavailable:

```c
/* BAD: strncpy doesn't guarantee null-termination */
strncpy(cfg->device, optarg, sizeof(cfg->device) - 1);
cfg->device[sizeof(cfg->device) - 1] = '\0';  /* Manual fix required */

/* GOOD: snprintf always null-terminates */
snprintf(cfg->device, sizeof(cfg->device), "%s", optarg);
```

Check return value when truncation matters (data integrity, control flow):

```c
/* Required: when result affects program behavior */
int len = snprintf(buf, sizeof(buf), "%d", value);
if (len < 0 || len >= (int)sizeof(buf)) {
    log_err("buffer overflow");
    return -1;
}

/* Optional: pure logging where truncation is acceptable */
snprintf(msg, sizeof(msg), "Debug: %s", long_string);
log_verbose("%s", msg);  /* Truncated output is fine */
```

## Modern C Types

### Fixed-Width Integers

Use `<stdint.h>` for explicit sizes:

```c
#include <stdint.h>

uint32_t timestamp_ms;    /* Exactly 32 bits, predictable wrap */
uint8_t brightness;       /* 0-255 range explicit */
int16_t temperature;      /* Signed 16-bit */
```

### Boolean Type

Use `<stdbool.h>` for boolean logic:

```c
#include <stdbool.h>

static bool g_verbose = false;

bool validate_input(const char *str) {
    if (str == NULL) return false;
    /* ... */
    return true;
}
```

### Exit Codes

Always use standard exit codes:

```c
#include <stdlib.h>

int main(int argc, char *argv[]) {
    if (init_failed)
        return EXIT_FAILURE;  /* Not 1, -1, or magic numbers */

    /* ... */
    return EXIT_SUCCESS;      /* Not 0 */
}
```

## Naming Conventions

### Type Suffixes (Project Convention)

POSIX reserves `_t` suffixes for future standard types. Common approaches:

| Style | Example | Used by |
|-------|---------|---------|
| `_t` suffix | `config_t` | Barr Group, most embedded |
| `_s`/`_e` suffix | `config_s`, `state_e` | This project (POSIX-safe) |
| No suffix | `struct config` | Linux kernel |

This project uses `_s`/`_e` for POSIX compliance and self-documentation:

```c
/* Struct typedefs: _s suffix */
typedef struct {
    int brightness;
    int timeout_sec;
} config_s;

/* Enum typedefs: _e suffix */
typedef enum {
    STATE_FULL = 0,
    STATE_DIMMED = 1,
    STATE_OFF = 2
} state_e;
```

**Note:** Barr Group recommends `_t` for all types. Linux kernel discourages typedefs entirely. The `_s`/`_e` convention is project-specific.

### Function Naming

Module prefix + verb (+ noun) per Barr Group "noun-verb" ordering:

```c
/* Public API: module_verb() or module_verb_noun() (required) */
void state_init(state_s *st, ...);
int state_touch(state_s *st, uint32_t now_ms);
int state_get_timeout_ms(const state_s *st, uint32_t now_ms);

/* Static helpers: same pattern recommended but optional */
static int config_parse_int(const char *str, int *out);
static bool device_validate_name(const char *name);
```

### Variable Naming

```c
/* Globals: g_ prefix per Barr Group (Linux kernel omits prefix) */
static volatile sig_atomic_t g_running = 1;
static bool g_verbose = false;

/* Constants/macros: MODULE_UPPER_CASE (universal) */
#define CONFIG_DEFAULT_BRIGHTNESS  150
#define STATE_MIN_TIMEOUT_MS       1000

/* Locals: snake_case */
int brightness_value = 0;
uint32_t timeout_ms = now_ms();
```

## Error Handling

### Consistent Return Patterns

```c
/* Functions returning status: 0 success, -1 error */
static int set_brightness(int fd, int value) {
    if (write(fd, buf, len) != len) {
        log_err("brightness write failed: %s", strerror(errno));
        return -1;
    }
    return 0;
}

/* Functions returning values: valid value or -1 for no-change/error */
int state_touch(state_s *st, uint32_t now_ms) {
    if (st->state == STATE_FULL)
        return -1;  /* No change needed */
    st->state = STATE_FULL;
    return st->brightness_full;  /* New brightness */
}
```

### System Call Errors

Always use `strerror(errno)` for system call failures:

```c
#include <errno.h>
#include <string.h>

int fd = open(path, O_RDWR);
if (fd < 0) {
    log_err("Cannot open %s: %s", path, strerror(errno));
    return -1;
}
```

## Logging Patterns

### Daemon Logging (systemd)

stderr is automatically captured by systemd journal - simplest approach for portable daemons:

```c
#define log_info(fmt, ...)    fprintf(stderr, "INFO: " fmt "\n", ##__VA_ARGS__)
#define log_warn(fmt, ...)    fprintf(stderr, "WARN: " fmt "\n", ##__VA_ARGS__)
#define log_err(fmt, ...)     fprintf(stderr, "ERROR: " fmt "\n", ##__VA_ARGS__)
#define log_verbose(fmt, ...) do { \
    if (g_verbose) fprintf(stderr, "DEBUG: " fmt "\n", ##__VA_ARGS__); \
} while(0)
```

**Alternatives:** For structured metadata, use `sd_journal_print()`. For priority control with stderr, use `SD_WARNING` prefixes.

## Raspberry Pi Specifics

### Sysfs Symlink Resolution

Always resolve `/sys/class`, `/sys/bus`, and `/sys/block` symlinks to their `/sys/devices` real path before access. These are symlink forests — only `/sys/devices` contains the true hierarchy. Using the symlink path directly creates a TOCTOU race:

```c
#include <limits.h>

char link_path[PATH_BUFFER_LEN];
char real_path[PATH_MAX];

snprintf(link_path, sizeof(link_path), "/sys/class/backlight/%s", name);
if (realpath(link_path, real_path) == NULL) {
    log_err("Cannot resolve sysfs path %s: %s", link_path, strerror(errno));
    return -1;
}
/* Use real_path for all subsequent access */
snprintf(path, sizeof(path), "%s/brightness", real_path);
```

### Sysfs Paths

Define path constants, never hardcode in function bodies:

```c
#define SYSFS_BACKLIGHT_DIR  "/sys/class/backlight"
#define DEV_INPUT_DIR        "/dev/input"

/* Build paths safely */
char path[PATH_BUFFER_LEN];
snprintf(path, sizeof(path), "%s/%s/brightness", SYSFS_BACKLIGHT_DIR, name);
```

### Input Validation for Device Names

Prevent path traversal attacks:

```c
static bool validate_device_name(const char *name) {
    /* Reject paths containing / or .. */
    if (strchr(name, '/') != NULL || strstr(name, "..") != NULL)
        return false;
    size_t len = strlen(name);
    if (len == 0 || len >= MAX_DEVICE_NAME_LEN)
        return false;
    return true;
}
```

### Signal-Safe Globals

For signal handlers, use `sig_atomic_t`:

```c
#include <signal.h>

static volatile sig_atomic_t g_running = 1;
static volatile sig_atomic_t g_wake_requested = 0;

static void handle_signal(int sig) {
    if (sig == SIGUSR1)
        g_wake_requested = 1;
    else
        g_running = 0;
}
```

## Pre-Implementation Checklist

For all embedded C code, verify:

**Buffer Safety:**
- [ ] All buffer sizes defined as named constants
- [ ] Buffer size relationships validated with `_Static_assert`
- [ ] Using `snprintf()` instead of `strncpy()`/`strcpy()`
- [ ] Return values checked for truncation

**Modern C Patterns:**
- [ ] Using `<stdint.h>` fixed-width types
- [ ] Using `<stdbool.h>` for booleans
- [ ] Using `EXIT_SUCCESS`/`EXIT_FAILURE`
- [ ] Struct init with `= {0}` (use memset only when zeroing padding matters)
- [ ] Consistent logging macros

**Naming (Barr Group standard):**
- [ ] Type suffix strategy chosen (avoid `_t` or accept non-conformance)
- [ ] Functions use `module_verb()` pattern
- [ ] Globals have `g_` prefix
- [ ] All identifiers spell-checked

**Integer Arithmetic (MISRA C:2023, CERT C):**
- [ ] Cast at least one operand before multiplication: `(uint32_t)a * b`
- [ ] Unsigned suffixes on literals: `1000U`, `100U` (MISRA Rule 7.2)
- [ ] Type widths match in comparisons (explicit casts)
- [ ] `_Static_assert` for bounded calculations
- [ ] No signed integer overflow — undefined behavior (CERT INT32-C); GCC -O2+ silently removes overflow checks on signed types (use unsigned arithmetic or explicit range checks)

**Error Handling:**
- [ ] ALL system call returns checked (sigaction, write, snprintf)
- [ ] State/cache updated only on success
- [ ] System errors reported with `strerror(errno)`
- [ ] Resources cleaned up on error paths

**Switch Statements (MISRA C:2004 Rule 15.3):**
- [ ] `default:` case present in enum switches (trade-off: silences `-Wswitch`)

**Documentation:**
- [ ] Non-obvious behavior documented (e.g., intentional wraparound)
- [ ] API preconditions in function headers

## Additional Resources

For detailed reference material, consult:
- **`references/anti-patterns.md`** - Code that works by accident (case studies)
- **`references/cert-c-practical.md`** - CERT C rules that actually apply to RPi (note: MISRA C:2023 supersedes C:2012 — 221 rules vs 143, adds multithreading rules 22.11-22.20 relevant to daemon patterns)
- **`references/header-comments.md`** - Source file header patterns for context engineering

**Static analysis:** `cppcheck --addon=misra.json --std=c99 --platform=unix32 <file>` — free, open-source, RPi-compatible, MISRA C:2023 support.
