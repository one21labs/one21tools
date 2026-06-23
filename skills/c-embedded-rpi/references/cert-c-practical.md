# CERT C Rules That Actually Matter for RPi

Practical subset of CERT C Secure Coding Standard for Raspberry Pi embedded Linux. Focus on rules that prevent real bugs in daemon/service code, not theoretical compliance.

## High Priority: Buffer and String Safety

### STR31-C: Guarantee sufficient storage for strings

**Problem:** Buffer overflow from insufficient space for null terminator.

```c
/* VIOLATION: No room for null terminator */
char name[8];
strcpy(name, "rpi_back");  /* 8 chars + null = 9, overflow! */

/* COMPLIANT: Size includes null terminator */
#define MAX_NAME_LEN 64
char name[MAX_NAME_LEN];
snprintf(name, sizeof(name), "%s", input);
```

### STR32-C: Null-terminate strings passed to library functions

**Problem:** Functions expecting strings receive non-terminated data.

```c
/* VIOLATION: read() doesn't null-terminate */
char buf[16];
ssize_t n = read(fd, buf, sizeof(buf));
printf("%s", buf);  /* Undefined behavior */

/* COMPLIANT: Explicit null-termination */
char buf[16];
ssize_t n = read(fd, buf, sizeof(buf) - 1);
if (n > 0) {
    buf[n] = '\0';
    printf("%s", buf);
}
```

### ARR30-C: Do not form out-of-bounds pointers

**Problem:** Array access beyond bounds.

```c
/* VIOLATION: No bounds check */
int values[10];
int idx = get_user_input();
values[idx] = 42;  /* Out of bounds if idx >= 10 or idx < 0 */

/* COMPLIANT: Validate index */
if (idx >= 0 && idx < 10) {
    values[idx] = 42;
}
```

## High Priority: Integer Safety

### INT02-C: Understand integer conversion rules

**Problem:** Integer promotions cause unexpected signed arithmetic.

```c
/* VIOLATION: unsigned short promotes to signed int, can overflow */
unsigned short x = 45000, y = 50000;
unsigned int z = x * y;  /* Signed overflow - undefined behavior! */

/* COMPLIANT: Cast one operand to control promotion */
unsigned short x = 45000, y = 50000;
unsigned int z = x * (unsigned int)y;  /* Unsigned multiplication */
```

**Note:** Casting either operand triggers usual arithmetic conversions, promoting both to the wider type. Project convention: cast first operand for consistency.

### INT32-C: Signed integer overflow

**Problem:** Signed overflow is undefined behavior in C.

```c
/* VIOLATION: Potential overflow */
int timeout_ms = timeout_sec * 1000;  /* Overflow if timeout_sec > INT_MAX/1000 */

/* COMPLIANT: Check before operation */
#define MAX_TIMEOUT_SEC (INT_MAX / 1000)
_Static_assert(MAX_TIMEOUT_SEC <= INT_MAX / 1000, "overflow risk");

if (timeout_sec <= MAX_TIMEOUT_SEC) {
    int timeout_ms = timeout_sec * 1000;
}
```

### INT31-C: Integer conversion data loss

**Problem:** Truncation when converting to smaller type.

```c
/* VIOLATION: Silent truncation */
long big_value = get_file_size();
int size = big_value;  /* Truncated if > INT_MAX */

/* COMPLIANT: Check range */
if (big_value >= INT_MIN && big_value <= INT_MAX) {
    int size = (int)big_value;
}
```

## Medium Priority: Memory Management

### MEM30-C: Do not access freed memory

**Problem:** Use-after-free vulnerability.

```c
/* VIOLATION: Use after free */
char *buf = malloc(256);
free(buf);
strcpy(buf, "data");  /* Undefined behavior */

/* COMPLIANT: Null after free */
char *buf = malloc(256);
free(buf);
buf = NULL;  /* Prevents accidental reuse */
```

**RPi Note:** Minimize dynamic allocation in daemons. Prefer stack allocation or static buffers to avoid memory leaks entirely.

### MEM31-C: Free dynamically allocated memory

**Problem:** Memory leak.

```c
/* VIOLATION: Leak on error path */
char *buf = malloc(256);
if (init_failed) {
    return -1;  /* buf leaked */
}

/* COMPLIANT: Free on all paths */
char *buf = malloc(256);
if (init_failed) {
    free(buf);
    return -1;
}
```

## Medium Priority: Error Handling

### ERR33-C: Detect and handle standard library errors

**Problem:** Ignoring return values from functions that can fail.

```c
/* VIOLATION: Ignoring errors */
FILE *f = fopen(path, "r");
fread(buf, 1, size, f);  /* f might be NULL */

/* COMPLIANT: Check returns */
FILE *f = fopen(path, "r");
if (f == NULL) {
    log_err("Cannot open %s: %s", path, strerror(errno));
    return -1;
}
```

## Lower Priority for RPi Daemons

These CERT C rules matter less for typical RPi daemon code:

- **Concurrency rules (CON)**: Single-threaded daemons using poll() don't need most of these
- **Floating-point rules (FLP)**: Rare in hardware control code
- **Signal rules (SIG)**: Only `sig_atomic_t` and async-signal-safe functions matter
- **File I/O rules (FIO)**: Mostly relevant, but simple sysfs access is low risk

## Practical Application

### When to Apply CERT C Rigorously

1. **User-provided input**: CLI arguments, config files, IPC data
2. **External device data**: Values read from sysfs, sensors
3. **Buffer operations**: Any string manipulation or array access
4. **Integer math for sizes/indices**: Buffer sizes, array indices, timeouts

### When CERT C is Overkill

1. **Internal constants**: Hardcoded values with known ranges
2. **Simple flag checks**: Boolean state variables
3. **Single-use local variables**: Short-lived, clearly bounded
4. **Framework-provided values**: When Linux kernel/glibc guarantees safety

## Quick Reference Table

| Rule | What It Prevents | RPi Relevance |
|------|------------------|---------------|
| STR31-C | Buffer overflow | HIGH - sysfs paths |
| STR32-C | Missing null terminator | HIGH - read() from sysfs |
| ARR30-C | Out-of-bounds access | MEDIUM - arrays rare |
| INT02-C | Unexpected promotions | HIGH - multiplication |
| INT32-C | Signed overflow UB | HIGH - timeout calculations |
| INT31-C | Truncation bugs | MEDIUM - type conversions |
| MEM30-C | Use-after-free | LOW - minimize malloc |
| MEM31-C | Memory leaks | LOW - minimize malloc |
| ERR33-C | Ignored errors | HIGH - all I/O operations |

## Sources

- [SEI CERT C Coding Standard](https://wiki.sei.cmu.edu/confluence/display/c)
- [MISRA C:2012 Guidelines](https://misra.org.uk/)
- [Barr Group Embedded C Coding Standard (PDF)](https://barrgroup.com/sites/default/files/barr_c_coding_standard_2018.pdf)
