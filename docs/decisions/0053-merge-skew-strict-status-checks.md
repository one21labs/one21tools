---
id: 0053
title: "Merge-skew prevention: require branches up-to-date on the gates check"
status: accepted
summary: "Prevent the individually-green / combined-red merge-skew class by enabling branch protection 'Require branches to be up to date before merging' (strict status checks) on the required gates check — a strict re-run recomputes the full on-disk budget on the merged content. Reject merge queue (premature; 0051:38 parks it as the escalation) and accept-risk. Ships as one decision-set with ADR 0054 (sibling merge-time integrity failure)."
---

# 0053 — merge-skew prevention via strict status checks

- Date: 2026-07-12
- Owner: PM
- Panel: lean-process-engineer / session-operator / process-economist (plugin-adopter omitted — no consumer surface); options argued on issue #164 finding 2; PM accepted. Ships with ADR 0054 as one ADR-0051 decision-set (both merge-time integrity failures from the 2026-07-11 incident cluster).
- Context: issue #164 finding 2. Scar: PRs #162/#163 each passed `gates` individually, merged 7s apart, and their combined char growth broke main's budget. Root cause: GitHub lets a PR merge when its required check passed against a STALE base — the combined on-disk content is never gate-checked before it lands, so two independently-green diffs to one budgeted file sum past the cap on main.

## Decision
On the required `gates` check, enable BOTH branch-protection settings: (1) **"Require branches to be up to date before merging"** (strict status checks) and (2) **"Do not allow bypassing the above settings."** Setting (2) is load-bearing, not optional hardening: branch protection does not bind admins/agent tokens unless bypass is disabled, and the scar's merges were admin-token agent merges — strict mode without (2) is a no-op against the exact merge identity that broke main. Strict mode locks the merge button until `gates` re-runs green against the CURRENT base. Because adr-lint char-budgets the FULL on-disk file (adr-lint.mjs:60 `chars: text.length` over `readFileSync` :218; overrun at :112 — not diff-scoped), the strict re-run recomputes the combined budget on the merged content and catches the exact overrun the scar needed. The `gates` workflow already runs on `pull_request` (gates.yml:9-10); this only changes WHEN a merge is permitted.

Both flips are owner-only, out of this session's reach — this ADR records the decision; the flips are the **Act**, tracked by an ADR-0021 deferred issue (strict flip + bypass-disable + verifying `gates` is marked required, ADR 0012) linked from the shipping PR's Deferred section.

## Justification
Cost trivial (two Settings toggles), risk low, value high: the scar was a live main breakage. Strict mode removes the judgment call from the agent entirely — GitHub blocks the merge until the combined content is proven green. Merge queue (option 2) is heavier and no scar shows strict checks insufficient; 0051:38 already parks it as the escalation. Accept-risk (option 3) leaves a reproduced main-breakage unguarded.

## Assumptions
- [verified, in-session] adr-lint budgets full on-disk content, so a strict re-run against the updated base recomputes the combined budget: adr-lint.mjs:60/:112/:218. A synthetic #162+#163-shape merge (two under-cap edits to one budgeted file) exceeds the cap only in the merged file — precisely what the strict re-run char-counts.
- [verified] Strict checks are available: the repo is public (merge queue also available, unused here).
- [verified, doc] "Require branches up to date" blocks the merge button until a fresh required-check run passes against current base; "Do not allow bypassing the above settings" extends every protection to admins/bypass identities — without it an admin/agent token merges regardless of strict mode (GitHub branch-protection docs). The Act confirms exact wording at flip time.
- [unverifiable] Merge cadence stays low enough that forcing serial re-runs does not bottleneck merges — REOPEN-IF strict re-run churn materially slows merges.

## Rejected alternatives
- **GitHub merge queue** — premature; no scar shows strict checks insufficient, and it is heavier machinery. 0051:38 parks it as the revisit escalation, which this ADR's revisit trigger honors.
- **Accept risk** — the scar broke main; leaving it unguarded is not acceptable for a two-toggle fix.

## Revisit triggers
- Strict re-run churn materially slows merge cadence -> adopt merge queue (0051:38, ADR 0054 sibling).
- A merge-skew breakage recurs despite strict mode (a merge-time integrity failure the `gates` scripts do not compute on the combined on-disk content) -> widen a gate or escalate. Residue (ADR 0047 precondition i): strict mode catches only failures a `gates` script itself detects on the merged content; a merge-time failure invisible to every gate script stays uncovered.
