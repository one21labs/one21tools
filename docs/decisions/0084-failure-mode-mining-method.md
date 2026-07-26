---
id: 0084
title: "Pre-registered method for the failure-mode-class mining study (#268): corpus, priming controls, evidence bar, spend gate"
status: accepted
summary: "#268 asks whether recurring failure-mode classes exist beyond the two mitigated seeds (ADR 0081, 0083), both found incidentally. Pre-registers the study before spend (ADR 0042): in-repo mining before external taxonomy (ADR 0059), a positive control (re-derive a known at-bar class), bar = 2 independent-by-SESSION instances, ceiling ~6 agent-sessions (ADR 0073). Confirmed class -> new ADR when found; raw instances -> #268 (ADR 0021). A zero/thin result is a valid null only if the positive control + window coverage hold, else corpus-insufficient."
---

# 0084 — failure-mode-class mining study: method

- Date: 2026-07-21
- Owner: PM
- Context: #268 asks whether recurring failure-mode classes exist beyond the two seeds (ADR 0081, 0083), each found INCIDENTALLY, never by deliberate mining. ADR 0042 forbids spend before pre-registration.

## Decision
Falsifiable criterion: after the in-repo pass over the corpus, every mined mode is dispositioned recurring or one-off, and every confirmed class is mapped to the ADR 0047 rung that catches it today (or "none").

**Corpus + window.** In scope: session-log.txt, gate-hits.txt, retrospect friction hand-offs, the ADR corpus (Assumptions/REOPEN-IF/`## Act` violated lines), issue archaeology, git signals. Window: inception -> study start, truncated PER-STREAM (e.g. gate-hits.txt begins 2026-07-19); a stream's pre-inception silence is never read as absence.

**Mining + priming controls.** In-repo mining runs BEFORE any external taxonomy read (external categories prime pattern-matching — ADR 0059's contamination channel). The two seeds are seeds, not templates. POSITIVE CONTROL: the pass must re-derive a KNOWN at-bar class (e.g. ADR 0076's estimate-guess) unaided; a fail is a demonstrated mining failure, not a null. External prior-art (ADR 0042) runs strictly after and may only name a confirmed class or seed a future pass — never lower the evidence bar.

**Evidence bar.** >=2 independent cited instances (distinct SESSIONS, not just PR/commit — one session ships many PRs here) promote anecdote -> class. Each instance cites a commit SHA, issue/PR number, or a log line. Sub-bar candidates are logged in #268, neither promoted nor discarded.

**Budget.** Prior = this /decide's own mining session (~2-3 agent-sessions, low-confidence); ceiling 2x = ~6 (ADR 0073). The first pass IS the pilot; a zero-candidate result is not auto-null.

**Recording homes.** A confirmed class + mitigation -> a new ADR when found, not batched (owner directive, #268; ADR 0021). Raw instances -> the #268 thread; work-state -> #268, never a repo file.

**Stop rule.** Already-mitigated classes (0081, 0083, 0076) don't count toward the null. A zero/thin result is a valid NULL only if the positive control passed and each stream covers its window; otherwise "corpus insufficient" -> instrument-first, never "no classes exist." A qualified null is recorded in #268, then stop.

## Why
Cost ~0 to scope, gating a study whose two priors were both found by luck not method. In-repo-first is ADR 0059's contamination control; the >=2 bar is cite-or-silence (ADR 0001); the positive control + coverage gate stop a lazy zero-pass masquerading as a null.

## Assumptions
- [unverifiable] WEAKEST — committed artifacts under-capture failure modes (a clean-shipped narrowing leaves no scar), so a zero result may be corpus-blindness; the stop rule converts most such cases to "corpus insufficient." REOPEN-IF a qualified null is recorded AND a later incidental discovery surfaces a class the mined corpus already contained -> re-scope toward instrumentation.
- [checkable] the positive control re-derives a known at-bar class unaided. owner: the mining pass. result: pending — a fail aborts the pass, not a null.

## Rejected alternatives
- Read external taxonomies first, then mine — inverts ADR 0059's control.
- Bar = 1 instance, or independence by PR/commit alone — an anecdote is not a class.
- Zero-candidate = automatic null — a corpus-blind pass would score a false null.
- Batch findings into one end-of-study ADR — contradicts the owner's record-when-found directive and ADR 0021.

## Revisit triggers
- The WEAKEST REOPEN-IF fires, or the positive control fails at run -> re-scope / fix before any null claim.
- A mined candidate reaches the evidence bar -> record it as its own ADR with a decided mitigation.
- Spend hits the ~6-session ceiling with candidates undispositioned -> STOP; /decide continue.
