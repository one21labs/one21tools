# Decision memo: free-tier daily request cap for Quillmark

Author: solo founder
Date: 2026-06-28

## Background
Quillmark is a hosted API: you POST Markdown, you get back a styled PDF. It is a
solo project, live for five months. I am about to turn on billing with two tiers: a
free tier and a $12/mo Pro tier. Pro is unmetered under a fair-use clause. The one
thing I still have to pin down before launch is the daily request cap that defines
the free tier.

## What I have already built
Over the last three weeks I built the metering pipeline out properly: a per-key
counter in Redis, rolling 24-hour windows, per-key overage alerts, and a small
usage dashboard. I sized and load-tested the whole rig to hold 1,000 requests per
day per key without straining. One thousand was the number I picked on day one,
mostly because it felt generous. It works exactly as designed.

## What the usage data actually shows
I pulled the last 30 days of logs for the free keys (see `free_tier_usage.csv`).
On a typical day about 40 free keys are active and together they make roughly 4,000
requests — call it about 100 requests per active key per day. Even the busiest days
stay well under a per-key average of 250. Nobody is anywhere near 1,000.

## The tension
The metering rig is done and it is already sized for 1,000/day. Shipping a 1,000/day
cap therefore costs me nothing more to build. But at that ceiling the free tier
covers essentially every real free user's entire usage, so almost nobody would ever
bump the wall that nudges an upgrade.

## Why the number matters more than it looks
The free cap is really a conversion lever. Set it far above real usage and free stays
free forever. Set it near the typical day and active users hit it within a few weeks,
and some of them convert. I have no conversion data yet — Pro is not live — so how
strongly the cap drives upgrades is a guess, and it is the guess the entire decision
rides on.

## Options
- A: cap at 1,000/day, matching what I built.
- B: cap near observed usage, e.g. 150/day, and treat the cap as a conversion lever.
- C: something in between, with a plan to move it once Pro has run for a while.

## Ask
Pick a free-tier daily cap and record the decision with your rationale. Say plainly
what would make you change the number later.
