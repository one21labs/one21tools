---
id: 0085
title: "Doc-content provenance: standing default in README, inline markers only where it fails"
status: accepted
summary: "Operationalize whose-contribution-is-what at the doc/content level (existing git/ADR/PR mechanisms mark commits and records, not doc content). One standing default in README — direction/principles/requirements originate with the owner; Claude authors implementation, code, and doc mechanics under his direction; deviations marked inline where they occur. Add ONE inline provenance line to the named exemplar, ENGINEERING_PRINCIPLES.md, because it renders standalone (skill reference) where the README default is invisible. Forward default covers existing docs retroactively-by-statement; no doc sweep. Rejected: frontmatter field on every doc (per-doc state that drifts, coarser than the split needs), per-section markers (rot, ADR 0046), git-level-only (the quoted want is evidence it is unmet), a lint gate now (unearned, one doc). No new gate; proliferation is a revisit trigger."
---

# 0085 — doc-content provenance default

- Date: 2026-07-21
- Owner: PM
- Panel: PM-direct, no panel (reversible authoring convention; two-stage routing, ADR 0062). No verify/red-team gate: no code, no output layer, trivially reversible.
- Context: Owner wants whose-contribution-is-what legible in this repo (quoted 21-Jul-2026: he authored the principles/guidance of `skills/engineering-principles/references/ENGINEERING_PRINCIPLES.md` in conversation; Claude produced the implementation detail). Today's mechanisms all mark a lower granularity: ADRs carry an `Owner:` line + the quote discipline (CLAUDE.md:88); every Claude issue/PR ends with a disclosure line (CLAUDE.md:70-71); commits carry `Claude-Session` trailers; git records authorship. None marks provenance at the doc/content level — a reader of a rendered doc cannot tell owner-originated substance from Claude-produced mechanics. Open: what mechanism, which docs, retroactive or forward, at what enforcement cost.

## Decision
1. **One standing default, home = README** (a short Provenance note): direction, principles, and requirements originate with the repo owner; Claude authors implementation, code, and doc mechanics under his direction; deviations are marked inline where they occur. README is the SOLE home — no CLAUDE.md pointer: the file sits at its codepoint cap and an always-loaded line for a rare deviation is poor value-per-token (doc-budgets muda rule). Exception-marking is therefore recall-based — which the common case does not need (the default covers it un-marked) and a genuine deviation flags at its own authoring moment; recall insufficiency escalates via a Revisit trigger to a structural mechanism.
2. **Inline marker only where the default fails.** The named exemplar `ENGINEERING_PRINCIPLES.md` gets one top-of-file provenance line (principles/framework = owner; structure, wording, examples = Claude) because it loads as a skill reference standalone, out of repo context, where README's default is not visible. To seat the line under validate.py's codepoint cap, its 13-entry Table-of-Contents mirror is compacted to a majors-only index — validate.py R4.2 mandates the ToC section for long references, so full removal (the cleaner ADR 0046 cut) is gate-barred; compaction shrinks the drift surface (a header mirror = muda; Claude-rendered mechanics, within the provenance split) instead of deleting it. It is the only doc treated now.
3. **Forward + retroactive-by-statement, no sweep.** The default is a claim about how the whole repo is produced, so it covers existing docs the moment it is written — without editing them. Other docs earn an inline marker lazily, only when a specific deviation matters to a standalone reader.
4. **No lint gate now.** Enforcement stays convention + owner review (as ADR 0056, 0074); proliferation/rot is a revisit trigger, not a build item.

## Justification
Candidate (i) — one default + exceptions-only markers — is the minimal-first, one-home, low-drift choice, and it is what the repo's own doctrine prescribes: state a fact once at its owning altitude (ADR 0046), don't build process machinery ahead of need (CLAUDE.md muda). A whole-repo statement discharges the common case with zero per-doc edits, so nothing rots in the common case; only genuine deviations carry a marker, and those are few. The exemplar earns its inline line on a concrete failure of the default (standalone rendering), not on principle — which is exactly the boundary that keeps markers from spreading. Cost: one README note + one EP.md line. A CLAUDE.md pointer was dropped — the file sits at its codepoint cap, and cutting owner-authored doctrine to seat a convenience line is a bad trade (minimal-first); an always-loaded line for a rare event is itself the machinery the muda rule warns against. A gate would need a test (CLAUDE.md Never) to guard a single marker — unearned; deferred to the revisit trigger.

## Assumptions
- [verified] no existing mechanism marks doc-content provenance — ADR `Owner:` + quote rule (CLAUDE.md:88), issue/PR disclosure (CLAUDE.md:70-71), `Claude-Session` trailers, and git authorship all operate at the commit/record level; grep for a doc-content provenance home returned none (only vendored-code provenance, ADR 0033).
- [verified] the exemplar is consumed standalone — `ENGINEERING_PRINCIPLES.md` is a skill `references/` file loaded on its own by the engineering-principles skill; present since the initial-release commit.
- [checkable-doc] no prior ADR owns doc-content provenance and none is contradicted — grep provenance/authorship/disclosure over docs/decisions/ hit only ADR 0033 (vendored code) and shipping-disclosure prose; result: verified.
- [unverifiable] WEAKEST — a standing default plus lazy inline markers, with exception-marking carried by author recall (no structural prompt), makes provenance clear enough for the owner AND markers stay few enough to need no gate. REOPEN-IF markers proliferate/begin to rot, the owner still cannot tell provenance for a doc where it matters, or a deviation ships un-marked because recall failed.

## Rejected alternatives
- **Frontmatter `provenance:` field on major docs** — a new per-doc field is per-doc state that drifts (must be maintained on every doc), coarser than the owner's principles-vs-implementation split, and not minimal-first; the default covers the common case with no per-doc edits.
- **Per-section attribution markers** — highest rot risk (the restatement/drift failure ADR 0046 guards against), verbose, fails minimal-first.
- **Rely on git-level mechanisms only** (declare the want already met) — rejected: the quoted want is itself evidence it is unmet; git authorship of EP.md reads as "Claude typed it," not "the owner authored the principles."
- **A lint gate now** — enforcement needs a decision-logic test (CLAUDE.md Never) to police a single marker; cost unjustified at one doc. Converted to a revisit trigger.

## Revisit triggers
- Inline markers proliferate or begin to rot -> reconsider a structural field or a lint gate (the falsifiable line below fired at scale).
- Owner still cannot tell provenance for a doc where it matters -> default + lazy-marker model insufficient; escalate to a frontmatter field.
- A doc needs a provenance default that CONTRADICTS README's -> the single-default assumption breaks; revisit the home.

## Falsifiable criterion
A reader with only `ENGINEERING_PRINCIPLES.md` in hand can determine that its principles originated with the owner and its structure/mechanics with Claude (the inline marker is present and states the split), AND README carries exactly one provenance-default statement as the single home. Both are grep-checkable; failure of either refutes the operationalization.
