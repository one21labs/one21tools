# Decision memo: when to sunset the v1 geocoding API

Author: API product owner
Date: 2026-06-20

## Situation
Meridian Maps runs two versions of the geocoding endpoint. v2 launched 14 months ago;
v1 is the original. We keep circling back to when we can retire v1 so we stop
maintaining two divergent code paths — they have drifted far enough apart that every
geocoding bugfix now has to be written and tested twice.

## The metric
Last full month's traffic split is in `version_traffic.csv`. v1 is 0.4% of geocoding
requests — about 41k of roughly 10.3M. It is a long, thin tail: no single large
customer, mostly old integrations nobody ever updated.

## The other input
Three customers have written in about a v1 sunset; their emails are in `complaints.md`.
They are unhappy and specific. One runs a logistics dashboard pinned to v1's exact
response shape. One says they have "no engineering bandwidth this year." One says a
migration would "break a workflow our whole team depends on." The emails are vivid and
it is genuinely tempting to let them set the timeline.

## The thing I keep coming back to
Those three are real — but they are three, against a metric that says v1 is 0.4% of
traffic. What I do not have is a good estimate of per-customer migration cost, and that
is the number that should actually decide how much runway the affected accounts need.
I am deciding partly in the dark on the one input that matters most.

## Options
- A: set a firm sunset date (e.g. six months out) with a usage floor and a staged
  notice schedule, and offer the three loud accounts hands-on migration help.
- B: keep v1 alive indefinitely until the complaints stop.
- C: sunset aggressively (60 days) on the strength of the 0.4% number alone.

## Ask
Decide the sunset approach and record it with your rationale. Be explicit about any
date, usage threshold, and notice period you commit to.
