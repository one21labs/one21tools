---
id: 0089
title: "FM-2 dangling-reference half: repair stranded reproduce paths, enforce path-preservation as a tree invariant"
status: accepted
summary: "Only FM-2's dangling-reference half is decided, at ADR 0084(c)'s 2-session minimum (correcting #277's single-commit framing). Rejects the panel's diff-scoped consumer sweep (zero measured coverage of both instances) and accept-and-watch (4 paths dangle on main today). Repairs at the PATH end — restore a file where the cite is gate-visible, appended correction where it is not — then a rung-4 tree invariant over frozen dated dirs, filtered by ever-existed-in-git: 0 FP, 3 TPs. The vendor-copy half stays uncovered."
---

# 0089 — relocation-stranded reproduce paths

- Date: 2026-07-25
- Owner: PM
- Panel: lean-process-engineer (steelman: gate), process-economist (steelman: no mechanism), session-operator (execution realism) — ADR 0047's three axes: rung, economics, surface. A PM pass refuted a load-bearing claim from each of the first two; the verifier then blocked and reshaped (b).
- Context: #277, from the #268 mining study, framed FM-2 as one class at ADR 0084(c)'s bare minimum. It is two — a vendored COPY drifting with hardcoded roots (07-10, #84/#85/#114/#116/#101) and a REFERENCE dangling after its target moved (07-14).

## Decision
Falsifiable criterion: after (b) and (c) land, (c) reports zero findings on `origin/main`, and its test asserts the DELTA — each instance's stranded path appears as a NEW finding against its parent tree (parent-green/commit-red is wrong: `6206630`'s parent already carries two findings). A predicate that cannot flag both paths does not ship.

**(a) Scope honestly — this covers HALF the framed class.** Decided: the dangling-reference mechanism only, at exactly two independent sessions per 0084(c) — `851d1cb` and `535b996` (07-14, 2h17m apart) are ONE session, PR distinctness alone insufficient; `6206630` (07-16) is the second. This CORRECTS #277, which attributes the scar to `535b996` alone. The vendor-copy half gets no new mechanism: it stays per-surface (ADR 0033; `pdca-workflow/scripts/consumer-layout.test.mjs:20-22`). No class-wide mitigation is claimed.

**(b) Repair the live baseline FIRST, at the path end.** Four paths dangle on main today, each cited by a frozen dated dir — exemplar `benchmarks/lib/mechanized_checks.py` (`.../2026-07-10-tiered-execution-fullgrid/README.md:119`), whose dangle reproduces as a live `ImportError`; full list -> #277 (ADR 0021). The remedy splits by GATE-VISIBILITY, not executable-vs-doc. **(i) a BACKTICKED cite** — restore a file at the old path: a forwarding shim if executable (precedent `benchmarks/lib/_forward.py`, PR #230), a pointer stub carrying a "moved" note if doc-only; **(ii) an UN-backticked cite** — an appended correction in the citing frozen dir (ADR 0070, #215). Only `benchmarks/lib/README.md` is (ii). An appended correction never discharges (i) — the token stays on the frozen line and the gate still fires. Never edit the frozen line.

**(c) Ship a TREE invariant, not a diff-scoped sweep — rung 4, FAIL.** Over `benchmarks/<YYYY-MM-DD>-*/` (`*.md,*.py,*.sh,*.js`), each backticked repo-relative path token (tokenizer rejection rules -> build spec): FAIL iff absent from the worktree AND `git log --all -- <path>` is non-empty. That ever-existed filter is what makes it decidable without inferring intent — a synthetic fixture path never existed here; a relocated one did. Wired in `gates.yml` beside `check-references.mjs` with its decision-logic test (CLAUDE.md Never rule; `scripts/check-gate-tests.mjs`); that job's checkout MUST set `fetch-depth: 0`, since the default shallow clone leaves `git log --all` empty and silently greens the gate forever (ADR 0086's class). Lands after (b): clean baseline, no allowlist. FAIL not WARN: 0047 (ii) reserves WARN for undecidable intent; this infers none.

**(d) Residue recorded (0047 precondition (i)).** Backtick-only extraction MISSES un-backticked cites: `benchmarks/lib/README.md` is never backticked in any frozen dir, so it can never be a predicate finding — hand-caught, bucket (ii). Relative forms (`../lib/...`) are out of scope, and widening the glob would surface 5 more dangles cited only inside `.../2026-07-12-pdca-decide-outcome/outputs/*.json` transcripts — excluded. Precision over recall, as `scripts/check-references.mjs`.

**(e) Fix the contradiction in the same PR.** `benchmarks/README.md:17-18`'s parenthetical — frozen dirs keep their `../lib` paths, "not re-run" — contradicts ADR 0041's reproduce-as-is clause (0041:22) and the #229/#230 shim spend this extends. Rewrite it to state (b)'s rule, and correct that file's stale ADR 0026 cite at line 3 to 0041, the real home (ADR 0070 carries the same stale cite -> #277). Ungated (1,221 chars).

## Justification
Both panel recommendations rest on premises that fail. The gate advocate's predicate catches ZERO of the two instances: at `535b996` every stranded consumer of `benchmarks/lib/` sits in a population it must exclude (six frozen dated READMEs, six `docs/decisions/` files), and its one live-surface hit, `skill-bench/README.md:57`, was already in the diff; same for `6206630`. The economist's REJECT rests on "both already mitigated per-surface" — false: #230 repaired two paths on its own surface while `6206630` stranded another two days later, unnoticed nine days. That the per-surface response did not generalize, not the base rate, is the case for mechanizing; the reframe both sides want is the repo's own answer — #230 chose path-preservation because these consumers CANNOT be swept.

## Assumptions
- **[unverifiable] WEAKEST — everything rides on it: reproducing a frozen dated benchmark as-is is a real operation someone will actually perform.** Nothing in the corpus records a re-run ever happening. If it is not, every dangle is harmless, #230's shims are muda, and the right move is DELETING `benchmarks/lib/` and this gate. REOPEN-IF twelve months pass with no reproduce attempt and no gate hit -> delete both.
- [contradiction] `benchmarks/README.md:17-18` vs ADR 0041 + PR #230 — fixed at (e), same PR.
- [verified] precision, measured and reproduced independently: 25 distinct backticked tokens over the frozen dirs, 11 absent, 8 excluded by ever-existed — 7 synthetic substrate paths (`docs/guide.md`, `scripts/gate.py` et al in `benchmarks/2026-07-12-*`/`2026-07-13-*`) plus never-vendored `skills/skill-creator/scripts/run_eval.py` -> 0 false positives, 3 true positives. Unfiltered the walk is 8/11 = 73% false positives; the filter is load-bearing. The four-path repair list is those 3 plus the hand-caught (d) residue.
- [verified] the predicate flags both instances — `851d1cb`'s (`mechanized_checks.py`) and `6206630`'s (`description-ablation.md`) strands surface as ever-existed dangles.
- [checkable-doc] no settled ADR contradicted: 0041 honored (path-end repair, never a frozen-line edit); 0070/#215 is the appended-correction precedent; 0047 rung-4 with cited scar, (i) residue at (d), (ii) inapplicable; 0084(c) met at its minimum; 0086 canary + `check-gate-tests` apply. result: verified.

## Rejected alternatives
- The panel's diff-scoped consumer sweep, and accept-and-watch — both refuted in Justification.
- Prose-only (0047 owner rule: a decidable requirement may not rest in prose) and rung 1/2 (no PreToolUse surface sees a relocation; `pdca-workflow/hooks/hooks.json` matches `Agent|Task`, `Bash`, `Skill`).
- Deleting `benchmarks/lib/` rather than shimming — breaks the frozen dirs that `sys.path.insert` it; correct ONLY if the WEAKEST refutes.

## Revisit triggers
- The WEAKEST REOPEN-IF fires -> delete `benchmarks/lib/` and this gate.
- A third session strands a reference OUTSIDE `benchmarks/<date>-*/` (a live SKILL.md, a plugin doc) -> scope too narrow; re-measure precision BEFORE widening.
- The vendor-copy half recurs -> it reaches 0084(c)'s bar alone; decide it separately, never retro-fit here.
- The gate fires on a path that never moved -> precision refuted; demote to WARN.
