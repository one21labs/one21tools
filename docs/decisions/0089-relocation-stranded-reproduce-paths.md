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

## Act (2026-07-28) — shipped; (b)'s remedy split gains a ship-visibility axis

Shipped in `8d698bc`: the gate runs from `.github/workflows/gates.yml:62-63`, and pointer stubs
restored the stranded paths.

- [outcome] the rung-4 tree invariant holds — verified: 39 cited path tokens across 191
  frozen-dir files, none stranded (28-Jul run).
- [outcome] the WEAKEST assumption (someone actually reproduces a frozen dated dir) — still-open;
  its 12-month REOPEN-IF is unchanged by this amendment.

**Amendment — (b) splits on SHIP-visibility, not only gate-visibility.** (b) assumed the old path
is repo-internal. Three stubs are not: `skills/building-skills/` ships inside the dev-skills
plugin (`.claude-plugin/marketplace.json`), so preserving a path there exports repo-internal
reproduce debt into every adopter install, and each stub points at a `skill-bench/` path absent
from a dev-skills-only install. Inside a shipped plugin source the remedy is (b)(ii)'s correction
note, never a stub. Split by what the gate can see:

1. `skills/building-skills/references/section-ablation.md` — DELETE with a one-line correction
   note in the citing dir's README anyway: its citations sit in FOUR files,
   `benchmarks/2026-07-12-pdca-decide-outcome/outputs/B{1..4}-C-r1.json`, all outside the
   gate's scanned extensions (`check-relocated-paths.mjs:40`) — the note serves the human
   reader the gate structurally cannot; frozen `outputs/` files are never edited.
2. `references/description-ablation.md` (doc-only) — DELETE together with a narrowed predicate:
   FAIL iff absent AND ever-existed AND NOT (the path is `.md`, lies under a shipped skill dir
   derived from the manifest's `skills[]` entries — never the bare `source` roots, which would
   exempt whole toolchains — AND the CITING FILE carries a structured line
   `MOVED: <old-path> -> <new-path>`, old path whole-token plain text, not the cited line
   itself, new path backticked and resolving in the worktree). A prose mention is not a note:
   the cited line contains the path as a substring, and an unrelated Correction heading already
   coexists in one citing dir — only the structured marker is earned. `scripts/eval_verdict.py`
   is EXECUTABLE and stays as its forwarding shim ((b)'s own split: a note cannot run); its two
   citing dirs keep resolving through it. The derived set is printed on every gate run and
   pinned by a fixture test; the exception ships as a pure export with decision-logic tests
   (never `main()`-only), including shipped-WITHOUT-marker still FAILing.
3. Landing is ATOMIC — predicate, correction notes, and the deletion in ONE change; the same
   change repoints the two live shipped references the original enumeration missed:
   `skill-bench/scripts/run_eval.py:32` and ADR 0013's Decision cite, both to the live
   `skill-bench` homes. Split across commits, `main` is red in between.

Outside shipped plugin sources, (b) stands unchanged, as does the WEAKEST REOPEN-IF — if it
fires, the correction notes are all that remain to remove, a cheaper cleanup than today's stubs.

- [process] the exemption is earned, not granted: it requires the structured marker, so a
  relocation still cannot silently strand a path. The invariant keeps its purpose — a reproducer
  can always find where the file went — and sheds only the adopter-facing cost. Narrowing the
  obligation beat teaching the gate a new remedy.
- [outcome] the amendment's implementation (predicate, markers, deletion, repoints) — still-open
