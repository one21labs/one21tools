---
id: 0089
title: "FM-2 dangling-reference half: repair stranded reproduce paths, enforce path-preservation as a tree invariant"
status: accepted
summary: "Only FM-2's dangling-reference half is decided (ADR 0084(c)'s 2-session minimum). Repairs at the PATH end, then a rung-4 tree invariant over frozen dated dirs, filtered by ever-existed-in-git: 0 FP, 3 TPs. Rejects a diff-scoped consumer sweep and accept-and-watch. The vendor-copy half stays uncovered."
---

# 0089 — relocation-stranded reproduce paths

- Date: 2026-07-25
- Owner: PM
- Context: #277 framed FM-2 as one class; it is two — a vendored COPY with hardcoded roots, and a REFERENCE dangling after its target moved. Only the reference half is decided here.

## Decision
**(a) Scope — HALF the framed class.** Covers only the dangling-reference mechanism, at ADR 0084(c)'s two-independent-sessions minimum (`851d1cb`/`535b996`, 2h17m apart, count as ONE session; `6206630` is the second). The vendor-copy half gets no new mechanism; stays per-surface (ADR 0033).

**(b) Repair the live baseline first, at the path end.** Four paths dangle on `main` today (list -> #277). Split by GATE-VISIBILITY: a **backticked** cite gets a restored file at the old path (a forwarding shim if executable, precedent `benchmarks/lib/_forward.py`; a pointer stub if doc-only); an **un-backticked** cite (only `benchmarks/lib/README.md`) gets an appended correction in the citing frozen dir (ADR 0070) — never an edit to the frozen line.

**(c) Ship a tree invariant — rung 4, FAIL not WARN.** Over `benchmarks/<YYYY-MM-DD>-*/` (`*.md,*.py,*.sh,*.js`): FAIL iff a backticked repo-relative path token is absent from the worktree AND `git log --all -- <path>` is non-empty (the ever-existed filter — a synthetic path never existed here; a relocated one did; 0 FP / 3 TP measured). Wired in `gates.yml`; that job's checkout MUST set `fetch-depth: 0` (a shallow clone empties `git log --all`, silently greening the gate forever, ADR 0086's class). Lands after (b).

## Justification
A diff-scoped sweep catches zero of the two known instances — both sit outside any diff. Accept-and-watch is false on its own premise: the per-surface response (#230) did not generalize; a second instance stranded nine days unnoticed.

## Assumptions
- [unverifiable] WEAKEST — everything rides on it: reproducing a frozen dated benchmark as-is is a real operation someone will actually perform. REOPEN-IF twelve months pass with no reproduce attempt and no gate hit -> delete `benchmarks/lib/` and this gate.
- [verified] the predicate flags both known instances (`mechanized_checks.py`, `description-ablation.md`) at 0 FP / 3 TP, measured against the full frozen-dir corpus. No settled ADR contradicted (0041, 0070, 0047, 0084(c), 0086).

## Rejected alternatives
- A diff-scoped sweep / accept-and-watch — refuted above; prose-only or rung 1/2 (no PreToolUse surface sees a relocation); deleting `benchmarks/lib/` instead of shimming (only if WEAKEST refutes).

## Revisit triggers
- The WEAKEST REOPEN-IF fires -> delete `benchmarks/lib/` and this gate.
- A third session strands a reference outside `benchmarks/<date>-*/`, or the gate fires on a never-moved path -> re-measure precision; demote to WARN if refuted.
- The vendor-copy half reaches 0084(c)'s bar -> decide separately.
