---
id: 0085
title: "Doc-content provenance: standing default per shipped unit, inline markers both ways"
status: accepted
tier: lite
summary: "Provenance: a standing default per standalone-consumed unit — the repo README and each shipped plugin's README (owner directs, Claude implements). Inline marker where that default is invisible or wrong in EITHER direction, including an idea Claude originated. No lint gate."
---

# 0085 — doc-content provenance default

- Decision: one standing default per standalone-consumed unit — a Provenance note in the repo
  README and in EACH shipped plugin's README: direction, principles and requirements originate
  with the owner; Claude authors implementation, code and doc mechanics under that direction. An
  inline marker goes where that default is invisible (a doc read standalone,
  `ENGINEERING_PRINCIPLES.md`) or wrong in EITHER direction — a design call specifically the
  owner's, AND an idea Claude originated that was adopted. Attribution runs both ways. Forward,
  no doc sweep. No lint gate; enforcement is convention + owner review.
- Why: ADR `Owner:`, issue/PR disclosure, `Claude-Session` trailers and git authorship mark
  commit-level provenance only. The default must ship per plugin because an adopter installs one
  and never sees the repo README. One-way marking would leave every unmarked idea reading as
  Claude's — the opposite of the record asked for.
- Rejected: per-doc frontmatter `provenance:` — drifts, coarser than the split. Per-section
  markers — highest rot risk. Git-level-only — the quoted want is evidence it's unmet.
- Reopen-if: markers proliferate/rot -> a structural field or lint gate. Owner still can't tell
  provenance where it matters -> escalate to a frontmatter field.
- Enforced: Provenance sections in `README.md`, `pdca-workflow/README.md`,
  `skill-bench/README.md`; the inline line atop
  `skills/engineering-principles/references/ENGINEERING_PRINCIPLES.md`.
