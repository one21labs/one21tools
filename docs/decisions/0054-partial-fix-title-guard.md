---
id: 0054
title: "Partial-fix title guard: deny only the title-closes / body-declares-partial mismatch"
status: accepted
summary: "A closing-keyword PR title becomes the squash subject and silently auto-closes an issue even when the PR is partial (scar: PR #166 closed #164 with 2 findings open, no red CI). Rung-4 CI extension of check-pr-body.mjs: adopt a `Partial: #NNN` body line; DENY iff the title closes an issue the body declares partial (a decidable contradiction); silent intent PASSes (never deny — owner ruling + ADR 0047 precondition ii). Ships as one decision-set with ADR 0053."
---

# 0054 — partial-fix title guard

- Date: 2026-07-12
- Owner: PM
- Panel: lean-process-engineer / session-operator / process-economist (plugin-adopter omitted — no consumer surface); options argued on issue #168; PM accepted. Ships with ADR 0053 as one ADR-0051 decision-set (both merge-time integrity failures from the 2026-07-11 incident cluster).
- Context: issue #168. PR #166's body deliberately carried NO closing keyword ("findings 2-3 keep #164 open"), but its title `Fix #164 finding 1: ...` became the squash-commit subject on main and auto-closed #164 with 2 findings unresolved — silent, no red CI. GitHub scans the squash message (PR title by default, absent a merger edit) for closing keywords and closes the referenced issue on merge.

## Decision
Rung-4 CI guard (ADR 0047 ladder — decidable requirement, surface exists): extend the check-pr-body.mjs family. gates.yml:57-61 already injects `PR_BODY`; add `PR_TITLE: ${{ github.event.pull_request.title }}` the same way. Adopt a structured body line **`Partial: #NNN`** = "this PR does NOT fully close issue #NNN" (mirrors the RETRO_LINE anchor, check-pr-body.mjs:18).

**Predicate** (pure, unit-tested — mirrors hasRetroLine + its test):
- Closing-keyword grammar (GitHub): `/\b(close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)\s+#(\d+)/gi` — extract the set `titleCloses` of issue numbers a title closes.
- Partial line: `/^Partial:[ \t]*#(\d+)(?=\s|$)/m` (also `/gm` for multiple) — extract `bodyPartials`.
- **DENY** iff `intersection(titleCloses, bodyPartials)` is non-empty: the title claims closure of an issue the body declares partial — a decidable contradiction. Fail naming each NNN.
- **PASS** otherwise. Title closes #NNN with the body SILENT on NNN (no `Partial:` line) = undecidable intent (a genuine full-fix is legitimate) -> PASS, never deny (ADR 0047 precondition ii; owner ruling below). Title without a closing keyword, or `Partial:` with no matching title-closure = consistent -> PASS.

## Justification
The failure is silent (no red CI) and lands unresolved-issue closures on main — high value to gate. The guard fires only on a decidable contradiction, so it never cries wolf on the legitimate `Fix #NNN` that truly completes an issue. Pure predicate + test is the cheapest rung-4 mechanism and reuses the check-pr-body architecture wholesale.

## Assumptions
- [checkable] `titleClosesDeclaredPartial(title, body)` returns the intersection; cases: (`Fix #164`, `Partial: #164`)->[164] deny; (`Fix #164`, silent)->[] pass; (`Add feature`, `Partial: #164`)->[] pass; (`Fixes #164`, `Partial: #165`)->[] pass — owner: build's *.test.mjs.
- [checkable] gates.yml can inject `PR_TITLE` alongside `PR_BODY` at :57-61 via `github.event.pull_request.title` — the PR_BODY pattern already proves the env-injection works.
- [verified] Closing grammar is close/closes/closed | fix/fixes/fixed | resolve/resolves/resolved + `#NNN`; a squash-merge uses the PR title as the commit subject absent a merger edit.
- [unverifiable] Authors adopt `Partial: #NNN` on partial PRs — REOPEN-IF a partial-fix mis-close recurs with a prose-only "stays open" signal -> add a stronger nudge (PR-template scaffolding of the line).

## Rejected alternatives
- **Blanket deny on any closing-keyword+issue-ref title** — REJECTED by binding owner ruling: "Banning is too strict. Sometimes that pattern is legit." A `Fix #NNN` title is correct when the PR completes the issue; a blanket deny cries wolf on the legitimate majority (violates ADR 0047 precondition ii — undecidable intent must never deny). The guard targets only the decidable mismatch.
- **Rung-5 prose title convention** — rejected per 0047:16: a decidable requirement with an available surface is never homed in prose (the gates.yml surface exists).
- **Accept risk** — the mis-close is silent and lands unresolved work on main; unacceptable.

## Revisit triggers
- A partial-fix mis-close recurs -> per the [unverifiable] assumption, strengthen adoption of the `Partial:` line.
- Residue (ADR 0047 precondition i): a merger hand-editing the squash title in the merge dialog is invisible to PR-time CI — the gate checks the PR title, not the final squash subject the merger can override. An author who signals partial only in prose (no `Partial:` line) also slips; the guard covers the decidable case only. The guard REDUCES, not eliminates, the risk (ADR 0053 sibling covers the other merge-time integrity class).
