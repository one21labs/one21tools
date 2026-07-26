---
id: 0091
title: "gate-pipe-guard.sh deleted, not retrofitted: scoped by a three-prong test, not blanket undecided-cleanup"
status: accepted
summary: "Owner-direct: gate-pipe-guard.sh (both copies) + tests deleted, not retrofitted — retrofitting would let the shipped artifact frame/anchor the panel (ADR 0084(b)'s contamination channel) and no already-decided predicate existed to preserve. Scoped by a three-prong test (BLOCKING + zero decided predicate anywhere + legitimacy acquired via undisposed re-citation) so it can never be cited to delete adr-lint.mjs, post-edit-gate.sh, or claude-review.yml. Names the repo phenomenon (a mention inherited as a decision) distinctly from Chroma's unrelated, measured context-rot finding."
---

# 0091 — Delete-not-retrofit for an undecided BLOCKING guard, scoped narrowly

- Date: 2026-07-26
- Owner: PM (recording an owner-direct order already executed; scope of the resulting rule is PM's call)
- Panel: none — owner-direct deletion (CLAUDE.md "Feedback = PDCA trigger" routine-call path); this ADR records it and sets the applicability boundary.
- Context: `gate-pipe-guard.sh` (`.claude/hooks/`, `pdca-workflow/hooks/`) was a rung-1 (deny) hook blocking every piped gate invocation with NO ADR ever deciding its predicate. Build commit `51e628f` (#158) cited "ADR 0047 wave-1" authority; 0047's Decision (a) (`docs/decisions/0047-detection-latency-ladder.md:23-27`) enumerates exactly four wave-1 items and the pipe guard is not one — though 0047's Context does cite the PR#134 pipe-mask scar it addressed. Two later ADRs treated it as settled without deciding it: 0071 said "unchanged... as-is" (corrected in place); 0090's Context named it only as the thing another gate was denied from. Three encounters, zero decisions, growing apparent legitimacy. The technical premise was also wrong on its own terms: a pipe does not inherently lose an exit code — `set -o pipefail` returns the first failure (verified: `false | cat` exits 1 under pipefail vs 0 without), `${PIPESTATUS[@]}` reads each stage (`1 0` observed), a redirect-then-read loses nothing. The guard's own header conceded this ("swallow the exit code without `set -o pipefail`") and used the concession only to widen the ban.

## Decision
1. **Delete, don't retrofit.** Both `gate-pipe-guard.sh` copies + `test-*.sh` suites stay deleted; hooks.json/settings.json registrations + `check-gate-tests.mjs`'s guard-mirror machinery stay removed (`check-gate-tests.mjs` now reports 10 wired gates / 8 hooks / 23 canary classes, exit 0 — verified). ADRs 0047, 0071, 0090 keep their in-place corrections (no longer describing the guard as live or wave-1-authorized).
2. **Applicability test — ALL THREE prongs required, conjunctive:**
   (i) **BLOCKING** — denies/prevents, not advisory;
   (ii) **zero decided predicate anywhere** — not partial, and not distributed-but-decided across other cited ADRs;
   (iii) **acquired apparent legitimacy via undisposed re-citation** across 2+ later records, not merely "new and unreviewed."
   A mechanism failing ANY prong is NOT a delete-not-retrofit candidate — it gets an ordinary retrofit or a narrow supplemental ADR instead.
3. **This ADR does not authorize deleting:** `adr-lint.mjs` — BLOCKING but fails prong (ii): every rule it enforces is separately decided (0088, 0087, 0067, 0020) and its CI-required rung is decided by 0012 — a bookkeeping gap, not an undecided predicate. `post-edit-gate.sh` — fails prong (ii): its rung-2 CONTENT is decided by 0047; only the shared-dispatcher SHAPE is unweighed (PARTIAL, not zero) — needs a narrow shape-only ADR, not deletion. `claude-review.yml` — fails prong (i): NONE decided but non-blocking, so no forcing-function hazard; ordinary backlog item.
4. **Why delete beats retrofit:** deciding ABOUT an existing artifact isn't deciding the question — the shipped shape frames the panel's option set. ADR 0084(b) holds this in a sibling domain (`docs/decisions/0084-failure-mode-mining-method.md:20`): in-repo mining runs before reading any external taxonomy because "external categories prime pattern-matching onto them." A guard already built and blocking sessions is the same prime, aimed inward — retrofitting makes "keep it, roughly as built" the path of least resistance. Deleting first restores a neutral question. Recorded honestly: `pipefail` + `| head` can raise spurious SIGPIPE failures — a rebuild must handle that, not rediscover it.
5. **Naming.** The owner calls this "context rot"; that published term (Chroma, 2026-07, 18 models) means something else and measured: performance degrading as input length grows. This repo's failure is a MENTION inherited as a DECISION — name it **mention-laundering** here, distinct from context rot. Causal link, one line: the decision corpus is ~415k chars (~104k tokens), unreadable whole, so sessions sample it by grep — and a passing authority-mention is exactly the topically-related distractor that degrades retrieval most. No external link added (ADR 0079's check-references gate would require a fetch-audit record this ADR doesn't carry).

## Justification
Cost x risk x value: retrofitting is cheap but banks the anchoring risk (0084(b)) into a live
rung-1 gate with a false-authority history — low value once the mechanism has zero real predicate
to preserve. Deletion re-opens the pipe-mask hazard from zero (PR#134 unremedied) but removes the
anchor, and the corrected premise lets any rebuild start from `pipefail`/`PIPESTATUS`, not a
blanket ban. The three-prong scope blocks the cheap generalization ("undecided => delete") from
reaching `adr-lint.mjs`, this corpus's own required gate.

## Assumptions
- [verified] ADR 0047 Decision (a) lists exactly four wave-1 items, no pipe guard — `docs/decisions/0047-detection-latency-ladder.md:23-27`.
- [verified] `pipefail` gives first-failure exit (1) vs default (0); `PIPESTATUS` reads both stages (`1 0`) — reproduced this session.
- [verified] post-deletion `check-gate-tests.mjs`: 10 wired gates / 8 hooks / 23 canary classes, exit 0 — reran this session.
- [checkable-doc] adr-lint.mjs's rules trace to 0088/0087/0067/0020, CI rung to 0012 (prong (ii) failure, out of scope here) — PM read; gate may re-verify by grep.
- [contradiction] ADR 0071's Decision line 1 asserted the guard was "unchanged... as-is" under 0047 authority 0047 never granted — fixed in place this session, noted here so 0091/0071 read consistently.
- [unverifiable] "mention-laundering" recurs beyond this instance — REOPEN-IF a second cite-without-decision case surfaces in a future retrospect or the #268 mining study.

## Rejected alternatives
- **Retrofit a record for the guard as-built** — the anchoring problem this ADR exists to name: no already-decided content to preserve (unlike adr-lint.mjs's distributed case).
- **Keep-and-decide (backfill later)** — extends the "no forcing function until a diff exists" residency ADR 0090 flagged; the blanket-pipe-ban premise is also independently wrong.
- **Blanket delete-all-undecided** — refuted directly: 16 of 21 audited mechanisms are solidly decided; a blanket rule would reach `adr-lint.mjs` (BLOCKING, content decided, just distributed) — the three-prong test blocks this overreach.

## Revisit triggers
- Prong (ii)+(iii) met by another BLOCKING mechanism (a second false-authority-cited guard) -> apply this same path, cite this ADR.
- A future record cites 0091 to delete `adr-lint.mjs`, `post-edit-gate.sh`, or `claude-review.yml` -> invalid on its face (each fails a prong); the citing ADR is wrong, not this one.
- PR#134's pipe-mask hazard recurs (a piped gate silently swallows a failure on `main`) -> a rebuilt guard targets the corrected premise (deny bare pipes lacking `pipefail`/`PIPESTATUS`, not all pipes), predicate decided BEFORE it ships.

## Act (post-ship — 2026-07-26)
- [outcome] deletion + settings/hooks/check-gate-tests cleanup verified in the working tree this session; ADRs 0047/0071/0090 corrected in place — verified.
