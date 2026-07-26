---
id: 0085
title: "Doc-content provenance: standing default in README, inline markers only where it fails"
status: accepted
tier: lite
summary: "Doc-content provenance: one standing default in README — direction/principles/requirements = owner, Claude authors implementation/mechanics, deviations marked inline. One inline line added to ENGINEERING_PRINCIPLES.md, the only doc consumed standalone. No lint gate; proliferation is a revisit trigger."
---

# 0085 — doc-content provenance default

- Decision: one standing default lives in README (a Provenance note) — direction, principles,
  requirements originate with the owner; Claude authors implementation, code, and doc mechanics
  under his direction; deviations marked inline. Inline marker only where the default fails:
  `ENGINEERING_PRINCIPLES.md` gets a top-of-file line because it loads standalone (a skill
  reference) where README's default is invisible. Forward + retroactive-by-statement — no doc
  sweep. No lint gate; enforcement stays convention + owner review.
- Why: existing mechanisms (ADR `Owner:`, issue/PR disclosure, `Claude-Session` trailers, git
  authorship) mark commit/record-level provenance only. A whole-repo default discharges the
  common case with zero per-doc edits; only genuine deviations carry a marker.
- Rejected: frontmatter `provenance:` field per doc — drifts, coarser than the split.
  Per-section markers — highest rot risk. Git-level-only — the quoted want is evidence it's
  unmet. A lint gate now — needs a decision-logic test for one marker; unjustified.
- Reopen-if: markers proliferate/rot -> reconsider a structural field or lint gate. Owner still
  can't tell provenance where it matters -> escalate to a frontmatter field. A doc needs a
  default contradicting README's -> the single-default assumption breaks.
- Enforced: `README.md` Provenance section; the inline line atop
  `skills/engineering-principles/references/ENGINEERING_PRINCIPLES.md`.
