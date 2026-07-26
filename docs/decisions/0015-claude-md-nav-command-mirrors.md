---
id: 0015
title: "CLAUDE.md nav command mirrors: delete the drifting test-command mirror, keep the unique/inert ones"
status: accepted
tier: lite
summary: "Not delete-all vs keep-all — split by line. DELETE CLAUDE.md's node --test line (a drifted mirror of gates.yml) AND normalize the 4 in-repo TESTING: headers to gates.yml's unquoted form. KEEP validate.py <dir> (not in gates.yml's loop) + adr-lint docs/decisions (drift-inert). Reject collapsing all three to a see-gates.yml pointer."
---

# 0015 — CLAUDE.md nav command mirrors

- Decision: split by line. DELETE the CLAUDE.md test-command line (mirrors gates.yml's
  `node --test`, had drifted) AND couple the deletion to normalizing the 4 in-repo `TESTING:`
  headers to gates.yml's unquoted full-path form — the relative quoted form false-greens (0
  tests, exit 0) from repo root, so deletion is safe only once its substitute works. KEEP
  `validate.py <dir>` (absent from gates.yml's all-skills loop — its one home) and
  `adr-lint ... docs/decisions` (highest-frequency, no glob/quoting hazard) in CLAUDE.md.
- Why: the doctrine file had already drifted once on this class — a mirror with a hazard AND a
  lower home goes, once its substitute is proven correct. The other two have no other home or
  drift surface, so cutting them loses a fact for no drift reduction.
- Rejected: keep all three (the proven-drifted mirror stays). Collapse all to a "see gates.yml"
  pointer (destroys the one-home `validate.py <dir>` fact, adds a hop). A string-equality gate
  (guards the mirror the doctrine says to delete).
- Reopen-if: gates.yml's test invocation changes path/quoting -> re-converge the headers. A
  session stalls because a deleted command wasn't findable -> reconsider a gates.yml pointer.
- Enforced: `CLAUDE.md`, `.github/workflows/gates.yml`, `pdca-workflow/scripts/adr-lint.mjs`
  (normalized `TESTING:` header).
