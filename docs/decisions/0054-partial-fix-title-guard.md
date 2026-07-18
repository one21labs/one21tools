---
id: 0054
title: "Partial-fix title guard: deny only the title-closes / body-declares-partial mismatch"
status: accepted
summary: "A closing-keyword PR title becomes the squash subject and silently auto-closes an issue even when the PR is partial (scar: PR #166 closed #164 with 2 findings open, no red CI). Rung-4 CI extension of check-pr-body.mjs: adopt a `Partial: #NNN` body line; DENY iff the title closes an issue the body declares partial (a decidable contradiction); silent intent PASSes (never deny — owner ruling + ADR 0047 precondition ii). Ships as one decision-set with ADR 0053."
---

# 0054 — partial-fix title guard

- Date: 2026-07-12
- Owner: PM
- Panel: lean-process-engineer / session-operator / process-economist (plugin-adopter omitted — no consumer surface); options argued on issue #168. Ships with ADR 0053 as one ADR-0051 decision-set (2026-07-11 incident cluster).
- Context: issue #168. PR #166's body deliberately carried NO closing keyword ("findings 2-3 keep #164 open"), but its title `Fix #164 finding 1: ...` became the squash-commit subject on main and auto-closed #164 with 2 findings unresolved — silent, no red CI. GitHub scans the squash message for closing keywords, closing the issue on merge.

## Decision
Rung-4 CI guard (ADR 0047 ladder — decidable requirement, surface exists): extend the check-pr-body.mjs family. gates.yml:57-62 injects `PR_BODY` + `PR_TITLE`, run on `pull_request` with **`types: [opened, edited, synchronize, reopened]`** — bare `pull_request` fires only on opened/synchronize/reopened, so a title EDITED to a closing form post-run merges stale-green, and the "reword the title" remedy fires no event to clear a stale red (B2; per ADR 0053's no-stale-merge thesis). Adopt a structured body line **`Partial: #NNN`** = "this PR does NOT fully close issue #NNN" (mirrors the RETRO_LINE anchor, check-pr-body.mjs:25).

**Predicate** (pure, unit-tested — mirrors hasRetroLine):
- **Closing grammar** (GitHub, colon OPTIONAL): `/\b(close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)(?:\s*:\s*|\s+)#(\d+)/gi` — GitHub's docs accept an optional colon (`Fixes: #164` and `Closes:#10` both close); a `\s+`-only grammar false-PASSes that scar class. Extract the set `titleCloses`.
- **Partial parse** (case/punctuation tolerant): for each body line matching `/^partial:(.*)$/gim`, pull every `#(\d+)` from the remainder -> `bodyPartials`. A strict `^Partial:[ \t]*#(\d+)` dropped comma-lists, trailing punctuation, and lowercase — declaring nothing (B3).
- **Fence-strip FIRST**: strip fenced code (```/~~~) and HTML comments (`<!-- -->`) before the Partial scan — a `Partial: #NNN` in a fenced example must not DENY a legitimate closing title (owner: never over-block; B4).
- **DENY** iff `intersection(titleCloses, bodyPartials)` is non-empty: the title claims closure of an issue the body declares partial — a decidable contradiction. Fail naming each NNN.
- **PASS** otherwise. Title closes #NNN with the body SILENT on NNN = undecidable intent (a genuine full-fix is legitimate) -> never deny (ADR 0047 precondition ii; owner ruling below). A non-closing title, or `Partial:` with no matching closure = consistent.

## Justification
Silent failure (no red CI) landing unresolved-issue closures on main — high value to gate. Firing only on a decidable contradiction, it never cries wolf on a legitimate `Fix #NNN`. Pure predicate + test is the cheapest rung-4 mechanism, reusing check-pr-body.

## Assumptions
- [checkable] `titleClosesDeclaredPartial(title, body)` returns the title∩partial intersection: (`Fix #164`,`Partial: #164`)->[164] deny; (`Add feature`,`Partial: #164`)->[] pass — result: verified (scripts/check-pr-body.test.mjs, 6 tests pass).
- [checkable] gates.yml injects `PR_TITLE` alongside `PR_BODY` via `github.event.pull_request.title` — result: verified (gates.yml:61).
- [checkable] grammar breadth — colon `Fixes: #164`/`Closes:#10` deny; comma `Partial: #164, #165`->both; fenced `Partial:` example does NOT deny — owner: build's *.test.mjs (this PR).
- [verified, doc] Closing grammar is close/closes/closed | fix/fixes/fixed | resolve/resolves/resolved, an OPTIONAL colon, then `#NNN` (github/docs linking-a-pull-request-to-an-issue.md: "keywords can be followed by colons"). Squash subject = PR title only for a MULTI-commit squash under this repo's `squash_merge_commit_title: COMMIT_OR_PR_TITLE`; a single-commit PR's squash subject is its lone commit message (Residue).
- [unverifiable] Authors adopt `Partial: #NNN` on partial PRs — REOPEN-IF a partial-fix mis-close recurs with a prose-only "stays open" signal -> stronger nudge (PR-template scaffolding).

## Rejected alternatives
- **Blanket deny on any closing-keyword title** — REJECTED by binding owner ruling ("Banning is too strict. Sometimes that pattern is legit."): a `Fix #NNN` title is correct when the PR completes the issue; blanket deny cries wolf on the legitimate majority (violates ADR 0047 precondition ii). The guard targets only the decidable mismatch.
- **Rung-5 prose title convention** — rejected per 0047:16: a decidable requirement with an available surface (gates.yml) is never homed in prose.
- **Accept risk** — the mis-close is silent and lands unresolved work on main; unacceptable.

## Revisit triggers
- Amended by ADR 0078: body-side closing keywords vs a `Partial:` line now also deny.
- A partial-fix mis-close recurs -> per the [unverifiable] assumption, strengthen adoption of the `Partial:` line.
- Residue (ADR 0047 precondition i) — the guard REDUCES, not eliminates: (a) a merger hand-editing the squash title is invisible to PR-time CI; (b) a **single-commit PR** whose lone commit message carries a closing keyword — under `squash_merge_commit_title: COMMIT_OR_PR_TITLE` its squash subject is the commit message, not the PR title, so a title guard never sees it (finding 2); (c) partial signalled only in prose (no `Partial:` line); (d) a cross-repo `owner/repo#NNN` title ref — far-fetched same-repo, deliberately NOT folded in. ADR 0053 sibling covers the other integrity class.
