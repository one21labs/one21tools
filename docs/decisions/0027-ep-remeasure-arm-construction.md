---
id: 0027
title: "EP re-measure: reference-inclusive symmetric arms, in-run baseline"
status: accepted
summary: "Issue #52 re-measure of engineering-principles-improve (675033c): same-run 3-arm (without / with-old / with-new), appending the 3 touched reference files to both with-arms (extends ADR 0019's --include-references to the benefit side). Rejects body-only: 6 of 9 edits live in references, repeating EP's ~8x cost confound. Merge bar (amended post-red-team): directional mean(diff)>0, diff=d_new-d_old, CI reported not gating. Flat/negative (d_new<=1e-9) on ANY of evals 1/2/5/6 escalates to Option E as a diagnostic."
---

# 0027 — EP re-measure: arm construction, merge bar

- Date: 2026-07-09
- Owner: PM
- Panel: opposing counsel, 2 unprimed advisors (comparability- vs fidelity-first); red-team broke the merge bar (below); verifier reproduced all claims.
- Context: prior baseline (`benchmarks/2026-07-08-skills-hermetic/metadata.json:38`) measured EP body-only: delta +0.020, CI [-0.066,0.107], CUT-CANDIDATE (refs unreachable). Draft `675033c`: 9 edits, 3 in body (5464->4012), 6 across 3 refs (+456/+594/+441, +1491). Evals 1/2's fixes live entirely in refs; 5/6 half. Body-only is blind to 6/9 edits.

## Decision
1. **Arms (same-run, EP only):** `without` (no treatment, hermetic per ADR 0023) / `with-old` (old body + OLD 3 touched refs) / `with-new` (new body @ 675033c + NEW same 3 refs). All 3 use this run's `claude -p` recipe (empty cwd `harness.sh:10`, DENY list `harness.sh:12`); ADR 0023's hermeticity requirement scopes to the control arm (ADR 0023:16). **`without`'s purpose (break 2):** zero merge-gate power — `diff=d_new-d_old` cancels it algebraically. Real value: individual `d_old`/`d_new` for the escalation trigger and comparability to +0.020, plus anomaly detection (an unappended treatment reads as `with-* ≈ without`). Kept for that, not gate power.
2. **Treatment content:** `--append-system-prompt` = neutral framing + SKILL.md body (frontmatter stripped) + the 3 touched refs, filename-headered. Untouched refs NOT appended.
3. **Cost, both ADR 0019 bounds:** body-only -1452 (5464->4012); reference-inclusive -1452+1491=+39, near cost-neutral — any positive fraction-met delta (ADR 0025) is a real gain either way. Basis (break 7): python `len()`, LF-normalized, frontmatter stripped — the 6-byte gap vs `wc -c` is bytes-vs-chars/CRLF, not an error.
4. **Reps + top-up:** 3-rep minimum (54 cells = 3 arms x 6 evals x 3 reps); top-up only on straddling cells (ADR 0019 #2).
5. **Merge bar — AMENDED (break 1):** `d_old`/`d_new` = with-arm minus `without`, fresh this run (ADR 0024's "pre-edit baseline" means re-measured, not +0.020). `diff=d_new-d_old` reduces algebraically to a paired with-new-vs-with-old comparison. PRIMARY: `mean(diff)>0` -> MERGE, directional. The eval-clustered 95% CI on `diff` is reported per-eval (win/loss pattern) as a secondary signal, not a gate: at n=6 evals the prior grid's CI never excluded 0 on a far larger contrast (half-widths 0.09-0.19, ADR 0019); requiring exclusion here would veto nearly every real improvement by construction. **Ambiguous middle** (mean>0, CI straddles 0): still MERGE, flagged weak-confidence — issue #52's bar is fraction-met up OR cost down with no regression; cost already clears (-1452 body, ~neutral +39 full), so directional benefit suffices as corroboration. `mean(diff)<=0` -> NO MERGE, one valid de-confounded ADR 0024 iteration (iteration 1; +0.020 doesn't count).
6. **Flat/negative escalation — DEFINED (break 5):** `d_new<=1e-9` (float-zero guard, matches `aggregate.py:63`), firing on ANY (not ALL) of evals {1,2,5,6}. On fire: file Option E (Read tool + per-arm sandboxed refs, without gets an empty dir) as a non-gating diagnostic — its Read grant would violate ADR 0023's tool-deny requirement if verdict-bearing, so it stays strictly diagnostic. Answers whether the widened trigger gets the file opened; targets iteration 2 only.

## Justification
Body-only repeats, on the benefit side, the confound ADR 0019 fixed on the cost side (~8x). Reference-inclusive arms extend ADR 0019's `--include-references` precedent, same grain. The amended bar keeps the gate usable: CI-exclusion on this reduced with-vs-with contrast is unsatisfiable at n=6 evals (break 1); directional-plus-CI matches ADR 0024's per-iteration check ("benefit-per-token improved," not "CI excludes 0"), reserving strict exclusion for the heavier KEEP/CUT verdict (ADR 0019/0025).

## Assumptions
- [verified] edit surface splits 3 body / 6 references — `git show 675033c --stat -- skills/engineering-principles/`.
- [verified, was mis-scoped] cost arithmetic reproduces exactly (`treatments/costs.json`, verifier-confirmed). "Reuses `blind.py`/`aggregate.py` unchanged" was WRONG: old scripts hardcode 2 arms (`blind.py:25`, `aggregate.py:54`); harness builder wrote adapted 3-arm versions, trivially.
- [checkable] all 3 arms stay hermetic per ADR 0023 — gate; result: verified (run metadata: hermetic true).
- [unverifiable] WEAKEST: the 3 touched refs approximate in-production benefit enough for a KEEP/CUT call — REOPEN-IF `d_new<=1e-9` on ANY of evals 1/2/5/6; escalate to Option E, not a clean cut.

## Rejected alternatives
- Body-only rerun — blind to 6/9 edits; a null can't distinguish "doesn't help" from "unmeasured," doesn't count toward ADR 0024's cap.
- Option E now — answers the trigger-behavior question this can't, but heavier; worth it only if evals come back flat.
- Strict CI-excludes-0 on `diff` — smaller contrast than the grid's largest-ever, which never excluded 0 at this eval count; rejects real improvements by construction (break 1).

## Revisit triggers
- `d_new<=1e-9` on ANY of evals 1/2/5/6 -> run Option E before writing off the reference edits.
- A future draft touches refs outside the 3 named here -> re-derive the touched-file set from its diff.
- The directional bar merges a draft a later re-measurement shows net-negative -> tighten the ambiguous middle.
