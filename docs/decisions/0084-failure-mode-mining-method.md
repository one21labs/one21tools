---
id: 0084
title: "Pre-registered method for the failure-mode-class mining study (#268): corpus, priming controls, evidence bar, spend gate"
status: accepted
summary: "Pre-registers the #268 failure-mode mining study (ADR 0042): in-repo mining before external taxonomy, a positive control, bar = 2 independent-by-SESSION instances, ceiling ~6 agent-sessions; a zero/thin result is a null only if the control and window coverage hold, else corpus-insufficient."
---

# 0084 — failure-mode-class mining study: method

- Date: 2026-07-21
- Owner: PM
- Context: #268 asks whether recurring failure-mode classes exist beyond the two seeds (ADR 0081, 0083), each found INCIDENTALLY, never by deliberate mining.

## Decision
Falsifiable criterion: after the in-repo pass, every mined mode is dispositioned recurring or one-off, and every confirmed class is mapped to the ADR 0047 rung that catches it today (or "none").

**(a) Corpus + window.** session-log.txt, gate-hits.txt, retrospect friction hand-offs, the ADR corpus (Assumptions/REOPEN-IF/`## Act` violated lines), issue archaeology, git signals. Window: inception -> study start, truncated PER-STREAM; a stream's pre-inception silence is never read as absence.

**(b) Mining + priming controls.** In-repo mining runs BEFORE any external taxonomy read (ADR 0059's contamination channel). Seeds are seeds, not templates. POSITIVE CONTROL: the pass must re-derive a KNOWN at-bar class (e.g. ADR 0076's estimate-guess) unaided; a fail is a mining failure, not a null. External prior-art (ADR 0042) runs after and may only name a confirmed class or seed a future pass — never lower the bar.

**(c) Evidence bar.** >=2 independent cited instances (distinct SESSIONS, not PR/commit — one session ships many PRs) promote anecdote -> class. Each cites a commit SHA, issue/PR, or log line. Sub-bar candidates are logged in #268, neither promoted nor discarded.

**(d) Budget.** ~2-3 agent-sessions prior; ceiling ~6 (ADR 0073). The first pass IS the pilot.

**(e) Recording homes.** A confirmed class + mitigation -> its own ADR when found, not batched (ADR 0021). Raw instances and work-state -> the #268 thread, never a repo file.

**(f) Stop rule.** Already-mitigated classes (0081, 0083, 0076) don't count toward the null. A zero/thin result is a valid NULL only if the positive control passed and each stream covers its window; otherwise "corpus insufficient" -> instrument-first. A qualified null is recorded in #268, then stop.

## Why
The study's two priors were both found by luck, not method: in-repo-first is ADR 0059's contamination control, the >=2 bar is cite-or-silence (ADR 0001), and the positive control + coverage gate stop a lazy zero-pass masquerading as a null.

## Assumptions
- [unverifiable] WEAKEST — committed artifacts under-capture failure modes (a clean-shipped narrowing leaves no scar), so a zero result may be corpus-blindness. REOPEN-IF a qualified null is recorded AND a later incidental discovery surfaces a class the mined corpus already contained -> re-scope toward instrumentation.
- [checkable] the positive control re-derives a known at-bar class unaided. owner: the mining pass. result: pending — a fail aborts the pass, not a null.

## Rejected alternatives
- External taxonomies first — inverts ADR 0059's control.
- Bar = 1 instance, or independence by PR/commit — an anecdote is not a class.
- Zero-candidate = automatic null — a corpus-blind pass would score a false null.
- One end-of-study ADR — contradicts the record-when-found directive and ADR 0021.

## Revisit triggers
- The WEAKEST REOPEN-IF fires, or the positive control fails -> re-scope / fix before any null claim.
- A candidate reaches the bar -> its own ADR with a decided mitigation.
- Spend hits ~6 sessions with candidates undispositioned -> STOP; /decide continue.
