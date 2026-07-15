# Dockline monolith — module coupling map (as of 2026-06-10)

One Rails-style app, one Postgres database. Notes below are from tracing call sites
and table access across the codebase.

## Modules and their coupling

### dispatcher_console (owned by Ops Tools)
- Reads: `bookings`, `carriers`
- Writes: `dispatch_events` (no other module reads this table)
- Inbound synchronous callers: 0 (it is a leaf; the UI calls it, nothing internal does)
- Notes: the only write target is private to this module. Cleanest seam in the app.

### bookings
- Reads: `bookings`, `customers`, `carriers`
- Writes: `bookings`, `booking_lines`
- Inbound synchronous callers: 6 (quoting, dispatcher_console, billing, notifications,
  carrier_portal, admin)
- Notes: central table; touched almost everywhere. Not a candidate for early extraction.

### notifications
- Reads: `bookings`, `customers`, `users`
- Writes: `notification_log`
- Inbound synchronous callers: 9 (bookings, billing, quoting, dispatcher_console,
  carrier_portal, admin, onboarding, exceptions, carriers)
- Shared tables: 3 (`bookings`, `customers`, `users`)
- Notes: called synchronously from nine places. Extracting first would be a multi-month
  entanglement.

### billing
- Reads: `bookings`, `invoices`, `customers`
- Writes: `invoices`, `payments`
- Inbound synchronous callers: 4
- Notes: regulated data paths; out of scope for a first cut.

## Table ownership summary
| table            | written by                | read by (count) |
|------------------|---------------------------|-----------------|
| dispatch_events  | dispatcher_console        | 0               |
| bookings         | bookings                  | 6               |
| notification_log | notifications             | 1               |
| invoices         | billing                   | 2               |
