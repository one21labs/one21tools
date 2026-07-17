# Did the ceremony cuts work? — observational outcome measurement (2026-07-17)

Owner ask (17-Jul, in-session): did the two ceremony-cut events — ADR 0062 (14-Jul, /decide
panel re-scoped to a lite default) and commit 860c865 (16-Jul, the every-PR /retrospect mandate
retired to on-demand) — actually work? Zero generation spend: counts over the repo's own record
(PR bodies via `gh`, the ADR corpus, the committed spawn log). Pre-registered in
`metadata.json` before counting; per-item data in `prs.jsonl` and `results.jsonl`.

## Findings (descriptive; exploratory by construction)

1. **Panel ceremony dropped as designed.** ADRs recording a spawned advisor panel: 12/19 (63%)
   pre-ADR-0062 vs 3/12 (25%) after. The three post-cut spawns (0063, 0069, 0071) were the
   contested calls the re-scope reserved the panel for — and in 0071 the panel materially
   changed the design (the adoption-marker choice).
2. **The empty-ritual layer disappeared; the substance did not.** Retrospective RATE is
   unchanged (22/53 = 42% of PRs pre vs 3/7 = 43% post). But composition flipped: the mandate
   era produced EIGHT zero-content "Retrospective: run" compliance stamps in its last four days
   (PRs 158-207) alongside 8 substantive runs; the on-demand era produced zero stamps — every
   post-cut run was substantive (median recorded section 582 chars vs 206 pre).
3. **Yield per run held or improved.** Post-cut: 3 runs emitted 9 findings — 7 adopted (each
   one cited: ADR 0070, PR 217's two fold-ins, PR 218/ADR 0072, PR 220/ADR 0073) and 2
   REJECTED with recorded rationale. Pre-cut substantive runs adopted 12 of 12 emitted — a
   100% adoption rate that is itself a signal (a channel that never rejects a finding is not
   filtering), where the on-demand era's 7/9-with-2-reasoned-rejections shows judgment applied.
4. **Spawn-log volume: INSUFFICIENT-N** — 7 committed lines, and the hook structurally
   under-logs raw-agent panels (this session's own 3-advisor panel never fired it).

## Reading, honestly bounded

Within this window the cuts did what they claimed: the ritual layer (compliance stamps,
default panel spawns on routine calls) is gone, while the instruments' useful output
(substantive retrospectives, findings adopted, panels on genuinely contested calls) is intact
or better. What this run CANNOT answer: whether defects now escape that mandated ceremony
would have caught — the post window is ~1.5 days. Revisit when a post-cut process defect
escapes to main that a mandated retrospective would plausibly have caught.

## Disclosed limits (metadata.json)

Observational, no randomization; the analyst executed most of the post window and read the
history before pre-registering (mitigation: every metric is a count over committed text, cited
per item, reproducible); windows differ in work mix; one pre-registration boundary typo
corrected in favor of the registered event definition (results.jsonl:correction);
section-length under-counts content routed to sibling PRs.
