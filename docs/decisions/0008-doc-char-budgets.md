---
id: 0008
title: "Doc-size budgets are char budgets, not line budgets"
status: accepted
summary: "Doc size is capped in chars, not lines (line caps are gameable by long lines): CLAUDE.md <=6,000, ADRs <=6,000 norm, enforced with no exemptions (the 2 over-budget ADRs are rewritten under the cap, not grandfathered); caps SSoT in char-budget.mjs, enforced by adr-lint; source headers + STRATEGY/ROADMAP/README left unbudgeted"
---

# 0008 — Doc-size budgets are char budgets, not line budgets

- Date: 2026-06-30
- Owner: PM
- Panel: none — the owner set the two caps directly. A contained docs/tooling budget call; no
  product-domain or correctness lens applies, and the owner needs no advisor panel to decide — the
  panel is a tool for hard/product calls, not a gate on the owner.
- Context: the ADR size budget was a **line** cap (`adr-lint` `--budget=70` lines). Line caps are
  gameable — cram more onto longer lines — so they measure layout, not the signal/token cost the
  budget is meant to bound. Evidence: `0006-retrospect-agent-model-tier.md` passes the 70-line cap
  at 8,813 chars (its lines run to 1,467 chars).

## Decision
Budget docs in **chars**, not lines. Caps: `CLAUDE.md` **<=6,000** (~2 pp, the always-loaded
layer); ADRs **<=6,000** norm. The caps + the over-budget predicate are the SSoT in
`pdca-workflow/scripts/char-budget.mjs` (one place to look, no grandfather set); **enforced** by
`adr-lint.mjs` (the ADR corpus + `oversizeDocs()` over `CLAUDE.md`) and unit-tested in
`adr-lint.test.mjs` + `char-budget.test.mjs`. The caps hold **with no exemptions**: the two ADRs
over budget (`0006` + `0007`) are **rewritten under the cap**, not grandfathered, leaving a clean
corpus. **Do not budget** source header comments, `STRATEGY.md`, `ROADMAP.md`, or `README.md`.
Budget system home: `pdca-workflow/skills/decide/references/doc-budgets.md` (altitude ladder + cap +
token table). ADRs stay version-agnostic.

## Justification
A char count can't be gamed by long lines and captures the real intent (high signal / token
efficiency) with no API call in CI — see the 0006 evidence above. **Rewrite under budget, don't
grandfather**: only **two** ADRs are over the cap, so rewriting them is cheaper than a shrink-only
allowlist and carries no exemption debt; an allowlist earns its keep only when many settled records
are over budget at once. **Source headers are not budgeted** because a header's failure mode is *drift* (it
describes what the file *was*, names an absent construct, or lists imports), not length — a char cap
would gate the wrong thing, and a flat cap misfits headers of legitimately varying complexity. The
existing "update the header same change / stale = drift" rule already targets that failure.

## Assumptions
- [verified] the line cap is gamed — `0006` passes the <=70-line cap at 8,813 chars (its lines run
  to 1,467 chars), the gameable-line evidence (`char-budget.mjs`; `adr-lint.test.mjs`).
- [checkable] ~4 chars/token for this corpus — anchor cross-checked vs words x1.33 (~25% band).
  Authoritative `count_tokens` not run (no API creds in env) — owner, anchor only. REOPEN-IF a
  measured count shows the ~3,000 chars/page anchor is off enough to mislead.
- [unverifiable] 6,000 is the right cap (efficiency without undue restriction). REOPEN-IF a
  legitimate addition can't fit without cutting a load-bearing crux.

## Rejected alternatives
- Keep line budgets — gameable by long lines; the status quo this replaces.
- **Grandfather the legacy ADRs** — correct when many settled records are over budget; here only 2
  are, so a rewrite is cheaper and leaves a clean corpus + no allowlist machinery. Chose rewrite.
- Token budgets — need `count_tokens` (no API in CI) and are model-specific (drift); chars are the
  ungameable, CI-checkable proxy, with a token column documented for reference only.

## Revisit triggers
- A legitimate `CLAUDE.md` addition can't fit <=6,000 without cutting a crux — revisit the cap or
  the always-loaded set.
- The corpus accumulates MANY settled ADRs over budget at once (e.g. a large import) — the rewrite
  cost flips, so re-evaluate a grandfather allowlist for that batch.
- A `count_tokens` run on the corpus shows the ~3,000 chars/page anchor is materially off — re-state it.

## Act (post-ship — 2026-07-01, PR #12)
