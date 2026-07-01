---
id: 0009
title: "Char budgets extend to SKILL.md bodies, skill references, and agent prompts"
status: accepted
summary: "Extend the char-budget discipline (ADR 0008) from ADRs + CLAUDE.md to the other frequently-loaded prose: SKILL.md body <=6,000 chars, skill references/*.md <=12,000 (with a TOC when over 6,000), agent prompts <=3,000. Owner-set caps. The gate splits by invocation model (Python + JS cannot share a constant): validate.py (the per-skill-folder gate) owns SKILL.md body + references; char-budget.mjs/adr-lint (the repo-wide JS gate) owns agents, alongside the ADR + CLAUDE.md caps it already enforces. doc-budgets.md's table is the human-readable SSoT listing every cap + its enforcing gate. No exemptions — the 3 over-budget SKILL.md bodies are rewritten under the cap (depth relocated to references, which have headroom), matching 0008's rewrite-not-grandfather."
---

# 0009 — char budgets for SKILL.md, references, and agent prompts

- Date: 2026-07-01
- Owner: PM
- Panel: none — the owner set the three caps directly (a contained docs/tooling threshold, no product-correctness lens). Verifier + red-team run on the gate logic + the rewrites (the verify gate this does not skip).
- Context: ADR 0008 char-budgeted the always-loaded ADRs + CLAUDE.md, but the prose that loads on demand — SKILL.md bodies (on skill trigger), their references (progressive disclosure), agent prompts (on spawn) — had no char cap. validate.py capped the SKILL.md body by LINES (`BODY_MAX_LINES=500`), which 0008 showed is gameable: the largest body, `optimizing-context`, is 230 lines (under the cap) yet 9,756 chars — the line cap never binds. Agents had no size gate at all.

## Decision
1. **Caps (owner-set):** SKILL.md body **<=6,000** chars; skill `references/*.md` **<=12,000** (with a `## Table of Contents` when over 6,000); agent prompts (`pdca-workflow/agents/*.md`) **<=3,000**. References get the larger cap as the progressive-disclosure detail tier (loaded only when needed); SKILL.md bodies + agent prompts load more eagerly, so they stay leaner.
2. **Gate placement splits by invocation model** (Python + JS cannot share a constant): `validate.py` — the per-skill-folder gate — owns the SKILL.md body cap (converting `BODY_MAX_LINES` to a char cap) + new reference validation (12,000 + TOC). `char-budget.mjs`/`adr-lint.mjs` — the repo-wide JS gate — owns the agent cap (`AGENT_CHAR_BUDGET` + `oversizeAgents()`), alongside the ADR + CLAUDE.md caps it already enforces.
3. **`doc-budgets.md`'s table is the policy SSoT** — it lists every cap + its enforcing gate; each gate owns its own cap *value* (no cross-language duplication of the integer). SKILL.md keeps its existing line-based TOC trigger (>150 lines); only references gain a char-based TOC trigger.
4. **No exemptions (rewrite-not-grandfather, per 0008):** the 3 SKILL.md bodies over 6,000 (`optimizing-context` 9,756, `decide` 7,044, `code-standards` 6,555) are rewritten under the cap by relocating depth into references (which have headroom); 5 references over 6,000 gain a TOC. No version bump (meta/tooling).

## Justification
The char-budget thesis (0008) applies wherever prose loads into a finite context: a line cap measures layout, a char cap measures token cost. SKILL.md is the strongest extension — it loads on every skill trigger, its 500-line cap never binds (max 230 lines at 9,756 chars), and validate.py already char-caps the name (64) + description (1,024), so the body was the one field left on the gameable metric. References earn 12,000 as the intentional depth tier; agents get 3,000 as a lean-prompt guard (binds nothing today — all <2,800 — but prevents future bloat, and the retrospect agent already calls prompt bulk "muda"). The Python/JS split is not ideal SSoT but unavoidable across two runtimes; doc-budgets.md's table + per-gate cap ownership keeps one navigable policy home.

## Assumptions
- **[checkable] WEAKEST: the SKILL.md 6,000 cap is met by relocating depth to references without losing skill function** — the over-budget bodies carry moveable detail, not 6,000+ chars of irreducible trigger/routing. TEST (owner: verifier): after the rewrites each skill still validates, and its description-as-trigger + core routing survive; if a body cannot reach 6,000 without cutting a load-bearing instruction, the cap (or the skill's scope) is wrong. — result: pending.
- [checkable] the gates enforce the caps + are tested — validate.py (new: char body + reference walk) gets its first test; `char-budget.test.mjs` covers `oversizeAgents()`; `python validate.py <dir>` + `node --test` both green. — owner: verifier.
- [unverifiable] 6,000 / 12,000 / 3,000 are the right tiers (efficiency without undue restriction). REOPEN-IF a legitimate skill/reference/agent cannot fit without cutting a load-bearing crux.

## Rejected alternatives
- **Keep the SKILL.md line cap** — gameable (the 9,756-char / 230-line body is the proof); 0008 already settled line->char.
- **One gate for all caps** — impossible without duplicating the cap integer across Python (validate.py) + JS (char-budget.mjs); the split-by-invocation-model + the doc-budgets.md table is the SSoT-preserving compromise.
- **Grandfather the 3 over-budget skills** — 0008 chose rewrite for a small over-budget set; same here (only 3), and the depth relocates cleanly to references.

## Revisit triggers
- A skill / reference / agent legitimately cannot fit its cap without cutting a load-bearing crux -> revisit that tier.
- A second consumer adopts the plugin and its skills routinely blow 6,000 -> re-evaluate whether the cap fits skills authored outside this repo.
