---
id: 0069
title: "check-gate-tests flags a vacuous hook test (literal-path SKIP) and an unenforced python gate"
status: superseded
tier: lite
summary: "Extended check-gate-tests.mjs with two rung-4 DENY predicates: a hook test hard-coding a literal absolute path in its path-root variable, and a python gate lacking a CI-executed sibling test. SUPERSEDED 2026-07-27: the gate carrying both was deleted after measuring zero CI failures across 552 runs (issue #311), so neither predicate runs. Re-decide before rebuilding."
---

# 0069 — detecting a vacuous / unenforced gate test

- Decision: two syntactic rung-4 DENY predicates in `check-gate-tests.mjs` — (a) a CI-invoked
  `test-<basename>.sh` whose path-root variable is a literal absolute path (it SKIPs everywhere
  but one machine, asserting nothing); (d) a `python3 <path>.py` gate with no CI-executed sibling
  `<path>_test.py`. Both cleared ADR 0047's recurring-miss bar on a live scar.
- Rejected: an exit-0-only detector (undecidable — a gate may legitimately exit 0), and a
  convention-only fix (prose, the thing the scar already defeated).
- **SUPERSEDED (2026-07-27).** The host gate was deleted: zero CI failures in 552 runs, 1,229
  lines, and the vacuity property it claimed was independently held elsewhere (issue #311). The
  SCAR IS REAL AND NOW UNGUARDED — a machine-bound test still asserts nothing elsewhere. Do
  not rebuild citing this record; the economics that justified it no longer hold.
- Enforced: NOTHING — stated so no later record inherits it as coverage.
