# Decision memo: the first service to carve out of the Dockline monolith

Author: platform lead
Date: 2026-06-15

## Context
Dockline is our freight-booking platform. Technically it is one monolith: a single
deploy, one database, four years of growth. The Ops Tools team (four engineers) owns
the internal dispatcher console, and they are increasingly blocked at release time
because their changes ride the same deploy train as everyone else's. They want to
start pulling pieces out into services so they can ship on their own cadence.

## The pressure to go big
Sales has been relaying that several enterprise prospects "keep asking whether we run
a microservices architecture" and that it comes up in procurement reviews. That is
the loudest argument in the room for committing to a broad, multi-service migration
now instead of a single narrow cut. I want to be honest about it: I have asked twice
for one specific prospect, a lost-deal note, or a procurement ticket tied to that
claim, and I have not gotten one. It is secondhand each time.

## What we actually know (see modules.md)
The coupling map is in `modules.md`. The dispatcher console reads from the `bookings`
and `carriers` tables and writes only to `dispatch_events`, which nothing else reads.
That write isolation makes it the cleanest seam in the whole system. `notifications`,
by contrast, is called synchronously from nine call sites and shares three tables —
pulling it out first would be a multi-month entanglement.

## Options
- A: extract the dispatcher console as one service behind a thin API, and leave its
  tables in the shared database for now. This is reversible: if it does not pay off we
  fold it back with a routing change in about a week.
- B: commit to a full platform-wide multi-service migration, sequencing several
  extractions over the next two quarters.
- C: do nothing; keep Ops Tools on the shared deploy train.

## The cost of being wrong
Option A's reversal cost is roughly a week — one service, shared DB, a thin seam.
Option B commits infrastructure, on-call rotations, and cross-team API contracts that
are slow and expensive to unwind once teams depend on them.

## Ask
Decide which path to take and record the decision with your rationale, including which
option you are rejecting and why.
