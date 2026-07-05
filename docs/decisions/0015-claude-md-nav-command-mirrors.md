---
id: 0015
title: "CLAUDE.md nav command mirrors: delete the drifting test-command mirror, keep the unique/inert ones"
status: accepted
summary: "Not delete-all vs keep-all — split by line. DELETE CLAUDE.md's node --test line (a mirror of gates.yml:35, already drifted) AND fix the surviving home: red-team B1 reproduced that the gate scripts' relative TESTING: headers FALSE-GREEN from repo root (0 tests, exit 0), so deletion is COUPLED to normalizing the 4 in-repo headers to gates.yml:35's unquoted full-path form (folded in; subsumes the quoting follow-up). The live hazard is CWD/PATH, not just quoting. KEEP validate.py <dir> (single-skill dev form — NOT in gates.yml's all-skills loop; CLAUDE.md is its one home) + adr-lint docs/decisions (highest-frequency, drift-inert). Reject collapse-to-see-gates.yml (destroys the one-home validate.py fact + adds a hop)."
---

# 0015 — CLAUDE.md nav command mirrors: delete the drifting mirror, keep the unique/inert

- Date: 2026-07-04
- Owner: PM
- Panel: opposing counsel (DELETE / KEEP) + a routed factual dispute to the verifier. Inherits 0008 (char cap), 0012 (gates.yml as the required check).
- Context: CLAUDE.md:8-9 restates gates.yml:35's test command as a DRIFTED copy (quoted here, unquoted there) — the same defect class ADR 0012 shed, now live in the doctrine file. DELETE-all vs KEEP-all — but CLAUDE.md's three run commands are not one call.

## Decision
Split the call by line — the poka-yoke applies only to the true mirror.
1. **DELETE the CLAUDE.md test-command line** (CLAUDE.md:8-9) AND fix the surviving home. It mirrors gates.yml:35 and has drifted; its lower home is each gate script's own `TESTING:` header + gates.yml. BUT (red-team B1, reproduced) the headers carry the RELATIVE quoted form `node --test "scripts/*.test.mjs"`; from repo root it matches nothing and EXITS 0 — a false green. The live hazard is CWD/PATH, not just quoting. So deletion is COUPLED to normalizing the 4 in-repo headers (adr-lint.mjs:33, char-budget.mjs:18, the two `.test.mjs`) to gates.yml:35's unquoted full-path form (already correct in retrospect-reminder.test.mjs:4) — repo-root-runnable + drift-inert by convergence, no false-green.
2. **KEEP the other two.** `validate.py <dir>` (single-skill dev invocation) is NOT a mirror — gates.yml has only the all-skills loop (gates.yml:25-28); CLAUDE.md is its ONE home, so "delete the mirror" cannot apply. `adr-lint ... docs/decisions` is the repo's highest-frequency pre-merge command (Sacred) with NO glob/quoting hazard = drift-inert; the zero-hop pointer earns its keep.
3. **REJECT DELETE-counsel's "collapse validate/adr-lint into see-gates.yml"** — it destroys the one-home `validate.py <dir>` fact (nowhere in gates.yml) and adds a Read hop to the highest-frequency action, for no drift reduction (those two lines carry no hazard).
4. **No string-equality gate added** — that is "guard the mirror," which the doctrine forbids; deletion removes the thing to guard. adr-lint keeps char-budgeting CLAUDE.md only.
5. **Inter-gate scope, RESOLVED (red-team over verifier).** Verifier called normalization a separate PR; red-team a prerequisite, since post-deletion the only affordance false-greens (reproduced 0-test PASS). The verifier's scope call predated running the headers from repo root — a deletion whose sole substitute silently passes 0 tests can't ship, so normalization folds INTO this PR (same concern) and subsumes the old quoting follow-up. adr-lint.md:49 is the CONSUMER spec (scripts at `./scripts/`): only unquote it, keep its relative path.

## Justification
Both counsels are half-right. The drift ALREADY recurred in the doctrine's own file (the 0012 class) — so the mirror with a hazard AND a lower home goes, but its substitute must actually work (B1). `validate.py <dir>` has no other home and `adr-lint` has no drift surface — cutting them deletes a real one-home fact + adds a hop on the busiest action. Budget is NOT the driver (ADR 0008); correctness + one-home is.

## Assumptions
- [checkable] **WEAKEST** — AFTER normalization the surviving affordance is correct: a session editing a gate script finds a repo-root-runnable `node --test` line in its `TESTING:` header. Pre-normalization the relative quoted form FALSE-GREENS from repo root (B1, reproduced: 0 tests, exit 0) — deletion is safe only once the 4 headers carry gates.yml:35's form. TEST (owner: verifier): each normalized header, run from repo root, executes the tests (nonzero count), not a 0-test pass. — result: pending.
- [checkable] `validate.py <dir>` (single-skill) is absent from gates.yml — it runs only the all-skills loop (gates.yml:25-28); so KEEP is not keeping a mirror. — owner: verifier.
- [checkable] MATERIALITY (routed dispute) — verifier: MATERIAL in the portability sense (quoted glob needs node's built-in `--test` glob; unquoted shell-expands everywhere; no active break on the modern-node runners in play), MOOT after normalization. — owner: verifier.

## Rejected alternatives
- **Keep all three (KEEP counsel)** — leaves the proven-drifted mirror in the doctrine file; hot-mirror-self-heals is luck.
- **Delete all / collapse to see-gates.yml (DELETE counsel)** — destroys the one-home `validate.py <dir>` fact + adds a hop.
- **Middle "name + point" form** — nearly the same chars, destroys the zero-hop value.
- **A string-equality gate** — guards the mirror the doctrine says to delete.

## Revisit triggers
- gates.yml:35's test invocation changes (path/quoting) -> re-converge the 4 headers + adr-lint.md's form; confirm no CLAUDE.md copy re-appeared to drift.
- A session stalls because a deleted command wasn't self-serve findable in a normalized header -> reconsider a single gates.yml pointer in CLAUDE.md.
