---
id: 0003
title: "Plan-phase criterion-minting: a required, falsifiability-gated step"
status: accepted
tier: lite
summary: "Make minting the per-decision criterion explicit + gated — adr-lint flags an ADR with no falsifiable criterion as UNFALSIFIABLE (reusing existing tags, no new field); name the assumption hit-rate as the emergent quality signal."
---

# 0003 — Plan-phase criterion-minting

- Date: 2026-06-28
- Decision: Plan-phase criterion-minting is REQUIRED and falsifiability-gated, reusing the existing tag vocabulary (no new field). `adr-lint` flags an ADR with no `- [checkable]`/`- [checkable-doc]`/`- [contradiction]` bullet AND no `- [unverifiable]` paired with a REOPEN-IF as UNFALSIFIABLE — gating PRESENCE (shape); the PM + gate judge SUBSTANCE. The corpus-wide assumption hit-rate (resolved `[checkable]` `## Act` outcomes, verified vs refuted) is named as the emergent, bottom-up quality signal — a read-out, not a target.
- Why: closes the lifecycle's one gap at the lowest cost — one executable guard reusing tags already in use, zero new machinery. Failing only the genuinely-empty case keeps a legitimate all-`[unverifiable]` market-fact ADR (which carries REOPEN-IF) passing.
- Rejected: hard-fail every all-`[unverifiable]` ADR — false-positives on legit market-fact calls, invites fake `[checkable]` bullets (Goodhart). A new required template field / `UNFALSIFIABLE` tag — duplicates the existing tag discipline. Rely on template prose alone — leaves the silent-skip unguarded; prevent beats detect.
- Reopen-if: an ADR is legitimately criterion-less yet correct -> the fail-condition is wrong, reopen it. A /retrospect sample shows ADRs gaming the gate with hollow `[checkable]` bullets -> add a substance check or move the judgment fully to the gate.
- Enforced: `pdca-workflow/scripts/adr-lint.mjs` (the falsifiability check); `node pdca-workflow/scripts/adr-lint.mjs docs/decisions`.
