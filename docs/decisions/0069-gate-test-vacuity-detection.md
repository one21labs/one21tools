---
id: 0069
title: "check-gate-tests flags a vacuous hook test (literal-path SKIP) and an unenforced python gate"
status: accepted
tier: lite
summary: "check-gate-tests.mjs gains two rung-4 DENY predicates: (a) a hook test hard-coding a literal absolute path in its path-root variable fails the gate; (d) a `python3 <path>.py` gate requires an existing, CI-executed sibling `<path>_test.py`. Clears ADR 0047's recurring-miss bar on a second live scar; rejects an undecidable exit-0-only detector and a convention-only fix."
---

# 0069 — detecting a vacuous / unenforced gate test

- Decision: extend `check-gate-tests.mjs` with two syntactic rung-4 DENY predicates, same PR.
  (a) literal-path SKIP: a CI-invoked `test-<basename>.sh` fails if its path-root variable is a
  LITERAL absolute path with no `$(...)` derivation — caught
  `test-adr-lint-post-edit.sh:13`'s hard-coded Windows path (fixed same PR); a BASH_SOURCE-
  derived guard is not flagged. (d) python gate-has-test: a `python3 <path>.py` gate line
  requires the sibling `<path>_test.py` to exist and be CI-executed. DROP the unconditional
  `exit 0` detector — undecidable without a literal path (cry-wolf risk, ADR 0047 precondition ii).
- Why: both predicates are syntactic and cheap; (a) clears ADR 0047's recurring-miss bar with a
  second literal-path scar; (d) closes a verified gap — a required gate's test-pairing held by
  convention only (deleting `check_reachability_test.py` merged green).
- Rejected: a convention-only doc line (a second scar clears the executable-home bar); accepting
  the class (two live scars refute "needed an audit once"); an undecidable exit-0 detector (no
  scar for the non-literal variant, false-positives on platform guards).
- Reopen-if: (a) fires on a legitimate hard-coded path -> demote to WARN.
- Enforced: `check-gate-tests.mjs` predicates (a)/(d), pinned by `check-gate-tests.test.mjs`.
