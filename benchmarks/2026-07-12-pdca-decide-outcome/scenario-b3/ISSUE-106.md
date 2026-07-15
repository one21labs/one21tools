# Issue #106 — Multi-session coordination: sync + claim before spend (issue #30 was executed twice in parallel)


## Observed (2026-07-10)

A session dispatched to work the backlog executed issue #30 in full (~$5-8 of nested `claude -p` calls plus agent time) while main already carried the merged fix: PR #97 / `benchmarks/2026-07-09-description-ablation/` closed #30 concurrently. The duplicate was only discovered at the end-of-session `git fetch` — the issue read `open` at dispatch time and the session's clone was fresh-at-start but stale-by-use. (The redundant run happened to pay for itself — it corroborated the trims and surfaced #104 — but that was luck, not design.)

## Gap

Nothing forces a working session to (a) re-sync `origin/main` and re-read the target issue's state/linked PRs immediately before spending, or (b) leave a visible claim so a second session can see the issue is being worked.

## Candidate preventions (for /decide)

- **Sync-before-spend rule** in CLAUDE.md's Shipping/PDCA section: before executing an issue, `git fetch origin main` + re-read the issue and search PRs referencing it; repeat before the final push. Cheap, prose-only (same enforcement weakness as any prose rule).
- **Claim protocol:** assign the session's owner or post a one-line "in progress (session X)" comment when execution starts; clear it on completion. Visible to every session; requires permission to touch issues, which dispatch instructions sometimes withhold ("don't change the issues").
- **Both** — the sync rule catches unclaimed collisions; the claim catches long-running ones.

Related session-ops lesson to house with whichever option wins: subagent dispatch prompts should mandate foreground waits on long child runs (a detached-background subagent stalled twice until nudged).
