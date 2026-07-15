---
id: 0069
title: "check-gate-tests flags a vacuous hook test (literal-path SKIP) and an unenforced python gate"
status: accepted
summary: "Extend check-gate-tests.mjs with two syntactic DENY predicates: (a) a gates.yml-wired hook test that assigns a path-root variable a literal absolute path (the machine-path SKIP-exit-0 scar) fails the gate; (d) a `python3 <path>.py` gate invocation requires an existing sibling `<path>_test.py` that CI executes (glob OR direct). A second live scar (test-adr-lint-post-edit.sh:13) clears ADR 0047's recurring-miss bar; the .mjs-only docstring scope is now stale. Reject the undecidable exit-0 half and the convention-only option."
---

# 0069 — detecting a vacuous / unenforced gate test

- Date: 2026-07-15
- Owner: PM
- Panel: opposing counsel (FOR mechanical enforcement / AGAINST new lint) — `scratchpad/panel-198.md`. Full tier: two live triggers + an open false-positive risk, so not lite.
- Context: `check-gate-tests.mjs` verifies a wired gate/hook test EXISTS and is CI-globbed (:132-169), never that it ASSERTS — a self-skipping test reads green forever (#198). Scar: `.claude/hooks/test-post-edit-gate.sh` hard-coded a Windows `REPO=`, SKIP-exited 0 every CI run, hid a `python`-vs-`python3` defect (fixed 171a5f7). Separately the docstring declares `.mjs`-only (:13-14); a second generic python gate `check_reachability.py` (gates.yml:42, #194) now ships with its pairing enforced by convention only — deleting `check_reachability_test.py` merges green (verified: checker still exits 0). Open: mechanize, document, or accept.

## Decision
Neutral hypothesis (#198, ADR 0059): does self-skip / python-gate vacuity need mechanical detection? Yes, for the two SYNTACTIC signatures the scars actually exhibit — ship both as rung-4 DENY in `check-gate-tests.mjs`, same PR:

- **(a) literal-path SKIP.** For each hook already resolved to a CI-invoked `test-<basename>.sh`, additionally read its text and FAIL if a path-root variable is assigned a LITERAL absolute path (`/home|/Users|/mnt|/opt|/srv|/root/…` or `X:\…`) with no `$(…)`/`${…}` derivation. This forces the sibling fix of `pdca-workflow/hooks/test-adr-lint-post-edit.sh:13` (`REAL_PLUGIN_ROOT="C:/Users/ajmcc/…"`, live second scar) to `$(cd "$HERE/.." && pwd)` in the same PR, else the gate reds. The BASH_SOURCE-derived guard at `test-post-edit-gate.sh:13` is NOT flagged (verified).
- **(d) python gate-has-test.** Capture `python3 (\S+\.py)` on run: lines (drop `*_test.py`, the `python3 "$t"` loop var); require the sibling `<path>_test.py` to EXIST and be CI-executed — glob-covered by a `for t in …*_test.py` line OR directly invoked by a `python3 …_test.py` line. validate.py (direct, gates.yml:35) and check_reachability.py (glob, :43) both pass; delete either sibling and it reds. Update the stale `.mjs`-only docstring.

DROP the "unconditional pre-assertion `exit 0`" detector and any convention line for it: both measured scars are LITERAL-PATH; an exit-0 with no literal path is unobserved and undecidable (ADR 0047 precondition ii, cry-wolf).

## Justification
Cost low (both reuse `extractTestGlobs`/`globCoversPath`; (a) is one content regex, (d) two). Risk low — both syntactic, exclusion-scoped, additive. Value: (a) clears 0047's recurring-miss bar with a SECOND scar (171a5f7 + the live test-adr-lint one), not the single instance the AGAINST counsel priced; (d) closes a verified ENFORCEMENT gap (pairing held by convention only) on a required gate whose docstring scope premise changed when a second generic python gate landed — not "a gate is currently untested" (its test exists and runs).

## Assumptions
- [checkable] the extended predicates flag exactly {test-adr-lint-post-edit.sh:13} and, for (d), {} on the current corpus while deleting `check_reachability_test.py` yields exit 1 — owner: PM/verifier. result: VERIFIED — prototype gave PY GATES={validate.py, check_reachability.py} (validate satisfied by direct `python3 validate_test.py`, reachability by glob), SELFSKIP flagged only test-adr-lint:13, spared the BASH_SOURCE-derived test-post-edit and test-spawn-log.
- [checkable] no THIRD live self-skip beyond the two scars, and no other `python3` gate lacks an executed sibling — owner: verifier at build. result: VERIFIED — grep over `.claude/hooks` + `pdca-workflow/hooks` for literal-path roots hit only test-adr-lint-post-edit.sh:13; the only two py gates both resolve.
- [unverifiable] the literal-path signature stays a reliable bug-proxy (no legitimate CI-run hook test ever needs a hard-coded absolute path). REOPEN-IF a real test trips (a) for a defensible reason — then demote that half to WARN (precondition ii).

## Rejected alternatives
- (b) convention line in ADR 0064's idiom docs only — a second scar clears the executable-home bar (ADR 0047:16); prose is rung-5 for a decidable, twice-observed signature.
- (c) accept the class — two live scars + a verified merge-green hole refute "needed an audit to surface once."
- Undecidable exit-0 detector / widening (a) to fuzzy skip semantics — no scar for the non-literal variant; false-positives on legitimate platform guards (0047 precondition ii).
- Leaving the `.mjs`-only docstring authoritative — its premise (validate.py the sole, separately-tested python gate) expired at #194; a stale scope note that green-lights a test-less python gate is drift.

## Revisit triggers
- (a) fires on a legitimate hard-coded path -> demote that predicate to WARN, keep (d).
- A python gate needs an executed test NOT expressible as glob-or-direct (e.g. pytest discovery) -> generalize (d)'s execution model.
- A self-skip lands via a mechanism neither predicate catches (env-var gate, `return 0`) -> the syntactic scope is too narrow; reopen.
