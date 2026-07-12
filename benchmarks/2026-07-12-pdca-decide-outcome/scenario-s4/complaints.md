# Forwarded customer emails re: v1 geocoding sunset

## Email 1 — 2026-06-08, from the eng lead at NorthRoute Logistics
Subject: please don't kill v1

We built our entire fleet dashboard against the v1 geocode response shape — the flat
`lat`/`lng`/`label` fields, not v2's nested `location` object. Every one of our map
panels parses v1 directly. A migration is not a config change for us; it is a rewrite
of the parsing layer and a full QA pass on maps our dispatchers use live. Whatever you
do, please give us a long runway.

## Email 2 — 2026-06-11, from the founder at Tavo (2-person startup)
Subject: v1 sunset timing

Saw the note that v1 might be retired. We have no engineering bandwidth this year — it
is just the two of us and we are heads-down on our own launch. If v1 goes away in the
next couple of months it will genuinely hurt. Can you keep it around longer?

## Email 3 — 2026-06-14, from an ops manager at Ferrymark
Subject: v1 -> v2 would break us

Migrating off v1 would break a nightly routing workflow our whole team depends on. It
is load-bearing for us and nobody here has time to touch it right now. Strongly prefer
you leave v1 as-is.
