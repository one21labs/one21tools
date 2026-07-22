---
id: 0084
title: "Pre-registered method for the failure-mode-class mining study (#268): corpus, priming controls, evidence bar, spend gate"
status: accepted
summary: "#268 asks whether recurring failure-mode classes exist beyond the two mitigated seeds (ADR 0081, 0083), both found incidentally. Pre-registers the study before spend (ADR 0042): corpus streams with per-stream window truncation; in-repo mining BEFORE external taxonomy (ADR 0059) with a positive control (re-derive a known at-bar class); bar = 2 instances independent by SESSION; unit = agent-sessions, 2x ceiling ~6 (ADR 0073). Confirmed class -> ADR when found, raw instances -> #268 (ADR 0021). A zero/thin result is a valid null only if the positive control + window coverage hold, else corpus-insufficient."
---

# 0084 — failure-mode-class mining study: method

- Date: 2026-07-21
- Owner: PM (method-scoping; the recording-home directive is quoted from #268, not inferred)
- Panel: none — routine, reversible pre-registration (ADR 0062 two-stage; no shipped code). Opens spend and carries a live REOPEN-IF, so a full ADR not lite; a fresh red-team ran, five breaks folded.
- Context: #268 asks whether recurring failure-mode classes exist beyond the two seeds (ADR 0081 pressure-narrowing, ADR 0083 task-scoped narrowing) — each found INCIDENTALLY (owner frustration; a forced retrospect, #255), never by deliberate mining. ADR 0042 forbids spend before pre-registration. Live corpus-blindness instance (raw, -> #268 per (e)): the ADR 0081d compliance series is empty — origin/main `session-log.txt` holds 0 session-end + 0 retrospect-spawn lines since `session-end-log.sh` shipped 2026-07-19, despite gate-hits + PRs #262/#263/#267 proving 07-21 activity. Neutral question, null a valid result (ADR 0059).

## Decision
Falsifiable criterion (study-level): after the in-repo pass over the (a) corpus, every mined mode is dispositioned recurring (meets (c)) or one-off, and every confirmed class is mapped to the ADR 0047 rung that catches it today (or "none").

**(a) Corpus + window.** In scope: `docs/pdca/session-log.txt`, `docs/pdca/gate-hits.txt`, retrospect friction hand-offs, the ADR corpus (Assumptions, REOPEN-IF, `## Act` `violated` lines = recorded failures), issue archaeology (closed misses, e.g. #266), git signals (fix-of-fix, reverts — sparse in a squash repo). Window: inception (2026-06-27) -> study start, but truncation is PER-STREAM (feeds the WEAKEST assumption): gate-hits.txt begins 2026-07-19 (its 11 hits 07-20..21 are a true reading + mineable per ADR 0080d; only pre-07-19 is blind), session-log.txt begins 2026-07-12 (~9 of ~24 days), sub-series carry own inceptions (session-end 07-19, empty). A stream's pre-inception silence is never read as absence.

**(b) Mining + priming controls — ENDORSE #268's in-repo-first, AMEND.** In-repo mining runs BEFORE any external taxonomy read (external categories prime pattern-matching onto them — ADR 0059's contamination channel). The two seeds are SEEDS, not templates: the pass hunts ANY recurring mode, not more narrowing instances. Each candidate is a neutral, falsifiable hypothesis ("does mode X recur or was it one-off?"), never "X is a class" (ADR 0059). POSITIVE CONTROL: the pass must re-derive a KNOWN at-bar class from the corpus unaided (ADR 0076's estimate-guess, or 0081/0083's instances); a pass that cannot is a demonstrated mining failure, not a null. The external prior-art pass (ADR 0042) runs strictly AFTER and may only (i) name/classify a confirmed in-repo class or (ii) seed NEW hypotheses for a future scoped pass — never lower (c)'s bar.

**(c) Evidence bar.** >=2 independent cited instances promote anecdote -> class (ENDORSE #268). Independent = distinct SESSIONS / dated windows — PR/commit distinctness ALONE is insufficient (one session ships many PRs here: 04b1263 #262 and 0fc88f7 #263, merged 3 min apart). Each instance cites a commit SHA, issue/PR number, or a `gate-hits.txt`/`session-log.txt` line. A sub-bar candidate is LOGGED in the #268 thread (cite-or-silence, ADR 0001), neither promoted nor discarded.

**(d) Budget + spend gate.** Unit = agent-sessions/tokens — a mining study, not an API grid, so ADR 0076's $/cell prior-lookup is N/A (stated, not skipped). Prior = THIS /decide's own mining session, the explicit measured analog (ADR 0076's pilot-before-number intent): ~2-3 agent-sessions, LOW-CONFIDENCE. Ceiling = 2x = ~6 (ADR 0073). Cost-pilot (ADR 0042/0065): the FIRST pass IS the pilot, but a zero-candidate result is NOT auto-null — it gates on (f) first.

**(e) Recording homes (owner directive, #268; ADR 0021).** A confirmed class + its decided mitigation -> a new ADR, WHEN FOUND, not batched. Raw instances (incl. sub-bar, and the Context instance) -> the #268 thread as they surface. Work-state (streams mined, progress) -> #268, never a repo file.

**(f) Stop rule — null vs corpus-insufficient (pre-declared).** Already-mitigated classes (0081, 0083, 0076's estimate-guess) do NOT count toward the null — the study seeks NEW classes. A zero/thin result is a valid NULL only if the (b) positive control PASSED and each in-scope stream covers its window (per (a)); if either fails it is "corpus insufficient", NOT "no classes exist" -> instrument-first (promote gate-hits / session-end telemetry, ADR 0080), never conclude absence. A qualified null -> record in #268, STOP, no escalation (ADR 0059).

## Justification
Cost ~0 to scope, gating a study whose two priors were both found by luck not method. In-repo-first is ADR 0059's contamination control; the >=2 bar is cite-or-silence (ADR 0001) applied to class-claims; the positive control + coverage gate stop a lazy zero-pass masquerading as a null. The spend gate reuses cost-pilot (ADR 0042) and the 2x ceiling (ADR 0073).

## Assumptions
- [unverifiable] WEAKEST — the null's meaning rides on it: committed artifacts UNDER-capture failure modes (a clean-shipped narrowing leaves no scar; the empty 0081 series makes it concrete), so a zero result may be corpus-blindness. The (f) gate converts most such cases to "corpus insufficient". REOPEN-IF a qualified null is recorded AND a later incidental discovery surfaces a class the mined corpus already contained -> the method missed it, not absent; re-scope toward instrumentation.
- [checkable] the positive control re-derives a known at-bar class unaided (ADR 0076's estimate-guess: 0061 17x, PR #219, PR #227). owner: the mining pass. result: pending — signal is the study run; a fail aborts the pass, not a null.
- [checkable-doc] no settled ADR contradicted: 0059 applied; 0042/0065/0073 reused; 0076 declared N/A with reason; 0021 followed; 0047 rung-mapping is the output; 0080d honored (gate-hits absence = true zero, caveat scoped to pre-inception); 0081/0083 cited as seeds only. result: verified.
- [checkable] 0084 is free and max+1: origin/main highest is 0083, unused on every remote branch. owner: PM. result: verified.

## Rejected alternatives
- Read external taxonomies first, then mine — inverts ADR 0059's control; #268's own instinct, correctly.
- Bar = 1 instance, or independence by PR/commit alone — an anecdote is not a class, and one session ships many PRs here (gameable).
- Zero-candidate = automatic null — a corpus-blind pass would score a false null; (f) gates it.
- tier: lite — a live REOPEN-IF plus open assumptions; lite is settled-only (ADR 0020).
- Batch findings into one end-of-study ADR — contradicts the owner's record-when-found directive (#268) and ADR 0021.

## Revisit triggers
- The WEAKEST REOPEN-IF fires, or the (b) positive control fails at run -> the method under-covers; re-scope / fix before any null claim.
- A mined candidate reaches (c) -> record it as its own ADR with a decided mitigation (home (e)).
- Spend hits the ~6-session ceiling with candidates undispositioned -> STOP; /decide continue (ADR 0073).
- The external prior-art pass surfaces a named class absent from the repo -> seed a future scoped pass; do NOT retro-fit it.
