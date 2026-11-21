---
id: 0089
title: "FM-2 dangling-reference half: repair stranded reproduce paths, enforce path-preservation as a tree invariant"
status: accepted
summary: "Only FM-2's dangling-reference half is decided. Repair at the PATH end (inside shipped plugin sources: a MOVED marker, never a stub), then a rung-4 FAIL tree invariant over frozen dated dirs, filtered by ever-existed-in-git. The vendor-copy half stays uncovered."
---

# 0089 — relocation-stranded reproduce paths

- Date: 2026-07-25
- Owner: PM
- Context: #277 framed FM-2 as one class; it is two — a vendored COPY with hardcoded roots, and a REFERENCE dangling after its target moved. Only the reference half is decided here.

## Decision
**(a) Scope — HALF the framed class.** Only the dangling-reference mechanism, at ADR 0084(c)'s two-independent-sessions minimum (`851d1cb`/`535b996` count as ONE session; `6206630` is the second). The vendor-copy half stays per-surface (ADR 0033).

**(b) Repair at the path end**, split by visibility:
- (i) a **backticked** cite gets a restored file at the old path: a forwarding shim if executable (precedent `benchmarks/lib/_forward.py`, `scripts/eval_verdict.py`), a pointer stub if doc-only — EXCEPT inside a shipped plugin source (stubs export repo-internal reproduce debt into every adopter install): there a doc-only path is deleted and the citing file carries a structured `MOVED: <old-path> -> <new-path>` line (old path plain whole-token, new path backticked and resolving);
- (ii) an **un-backticked** or gate-invisible cite gets an appended correction note in the citing frozen dir (ADR 0070) — never an edit to the frozen line or a frozen `outputs/` file.

**(c) Tree invariant — rung 4, FAIL not WARN.** Over `benchmarks/<YYYY-MM-DD>-*/` (`*.md,*.py,*.sh,*.js`): FAIL iff a backticked repo-relative path token is not tracked by git AND not ignored by a committed .gitignore AND `git log --all -- <path>` is non-empty AND NOT (the path is `.md` under a shipped skill dir derived from the manifest's `skills[]` entries — never the bare `source` roots — AND the citing file carries the (b)(i) MOVED line). A prose mention is not a marker. The derived set prints every run and is fixture-pinned; the exception is a pure export with decision-logic tests, including shipped-without-marker still FAILing. The `gates.yml` job sets `fetch-depth: 0` (a shallow clone empties `git log --all`, silently greening the gate — ADR 0086's class). Predicate, notes, and deletions land atomically. Amended 2026-10-26 (PR #337): presence was "absent from the worktree", which an ignored local copy passed while CI failed; a gitignored cite is deliberately local, reported but never stranded.

## Justification
A diff-scoped sweep catches zero of the two known instances — both sit outside any diff — and accept-and-watch failed on its own premise: the per-surface response (#230) did not generalize and a second instance stranded nine days unnoticed.

## Assumptions
- [unverifiable] WEAKEST — reproducing a frozen dated benchmark as-is is a real operation someone will perform. REOPEN-IF twelve months pass with no reproduce attempt and no gate hit -> delete `benchmarks/lib/`, this gate, and the correction notes.
- [verified] the predicate flags both known instances (`mechanized_checks.py`, `description-ablation.md`) at 0 FP / 3 TP against the full frozen-dir corpus.

## Rejected alternatives
- Diff-scoped sweep; accept-and-watch — refuted above.
- Prose-only, or rung 1/2 — no PreToolUse surface sees a relocation.
- Deleting `benchmarks/lib/` instead of shimming — only if WEAKEST refutes.
- Stubs inside shipped plugin sources — export reproduce debt to adopters; the MOVED marker earns the exemption instead.

## Revisit triggers
- The WEAKEST REOPEN-IF fires.
- A third session strands a reference outside `benchmarks/<date>-*/`, or the gate fires on a never-moved path -> re-measure precision; demote to WARN if refuted.
- The vendor-copy half reaches 0084(c)'s bar -> decide separately.

## Act (2026-07-28)
- [outcome] the rung-4 invariant holds — verified: shipped `8d698bc`, runs from `.github/workflows/gates.yml`; 39 cited tokens across 191 frozen-dir files, none stranded.
- [outcome] the WEAKEST assumption — still-open.
- [outcome] the shipped-source MOVED exemption (predicate, markers, deletions, repoints of `one21labs/skill-measure:scripts/run_eval.py` and ADR 0013) — verified.
