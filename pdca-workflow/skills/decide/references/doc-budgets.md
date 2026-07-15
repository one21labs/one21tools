# Doc system — altitude ladder, char budgets, token approximation

Single home for the **documentation hierarchy**: the altitude ladder (below) and the doc-size
budgets. Char budgets were decided in **ADR 0008**. The authoritative *value* of each cap lives in
its enforcement home (`char-budget.mjs`); the table below indexes them for navigation, not as a
second source. The one-home / drift *rule* lives in CLAUDE.md "Docs — one home per fact"; this file
owns the *ladder* that rule ranks by.

## Altitude ladder

The tier order a fact's home is ranked against (high -> low):

**STRATEGY > ROADMAP > README > CLAUDE.md > docs/ + skill references > source headers > code**

Code is the lowest tier and owns executables — schema versions, signatures, dims, filenames,
breakpoints, and (here) the budget numbers themselves (`char-budget.mjs`). A copy above its home is drift.

## Budgeted docs

`~tok` is the chars / 4 anchor (see Method) — reference only; budgets are set and checked in **chars**.

| Altitude | File / type | Char cap | ~ tok | Cap's home |
|---|---|---|---|---|
| STRATEGY | `STRATEGY.md` | none | — | — |
| ROADMAP | `ROADMAP.md` | none (legitimately variable) | — | — |
| README | `README.md` | none | — | — |
| CLAUDE.md | `CLAUDE.md` | **6,000** (~2 pp) | ~1,500 | `char-budget.mjs` (`DOC_BUDGETS`) |
| CLAUDE.md | pdca-init's `claude-md-template.md` (the scaffold it copies) | **6,000** | ~1,500 | `char-budget.mjs` (`DOC_BUDGETS`) |
| docs | `docs/decisions/NNNN-*.md` (ADR) | **6,000** (~2 pp) norm | ~1,500 | `char-budget.mjs` (`ADR_CHAR_BUDGET`) |
| docs | `docs/decisions/NNNN-*.md` (lite ADR, `tier: lite`) | **1,500** (~0.5 pp) | ~375 | `char-budget.mjs` (`LITE_ADR_CHAR_BUDGET`) |
| docs | `docs/decisions/README.md` (ADR guide) | none | — | — |
| agent | `pdca-workflow/agents/*.md` | **3,000** | ~750 | `char-budget.mjs` (`AGENT_CHAR_BUDGET`) |
| source | header block comments | none — see Extending | — | — |
| code | executables | none | — | — |

The caps above (CLAUDE.md / ADRs / agents) are the SSoT + over-budget predicate in `char-budget.mjs`,
enforced by `adr-lint.mjs` (ADRs, no exemptions; `oversizeDocs()` over `CLAUDE.md`; `oversizeAgents()`
over agent prompts) and unit-tested in `adr-lint.test.mjs` + `char-budget.test.mjs`. **SKILL.md-body +
skill-reference char budgets are a separate concern owned by the `building-skills` skill, not
pdca-workflow** — ADR 0009 extends the discipline there so this plugin has no cross-skill dependency.
Lower a cap when a doc is leaned; never pad it.

**A consumer with a designated detail-home doc** (one other docs reference, so a larger cap is the
correct altitude) adds its own entry to `DOC_BUDGETS` with a bigger number — e.g. a
`docs/review-system.md` at ~12,000 (~4 pp). The table above is the pattern, not a fixed list;
`DOC_BUDGETS` in `char-budget.mjs` is the fixed list.

## Editing a budgeted doc — measure first, never iterate against the gate

Before ANY edit to a capped file, measure headroom = cap − current, and size the planned addition
the same way, minus any text it replaces. Measure in the GATE'S unit: every enforced cap —
validate.py's (`skills/**/references/*.md`, SKILL.md) AND `char-budget.mjs`'s (CLAUDE.md, ADRs,
agent prompts) — counts unicode CODEPOINTS, not bytes (`wc -c` over-reads every em-dash by 2), so
measure with the gate itself or
`python3 -c "print(len(open(f,encoding='utf-8').read()))"`. If the
addition exceeds the headroom, do NOT word-golf the new line into mush and do NOT edit-validate-trim
in a loop: review the WHOLE file for muda and drift (restatements of another home, narration,
dead references) and cut there first — a file living at its cap is itself a smell that it carries
waste or holds facts belonging at a different altitude. The pm agent's ADR rule (draft to the
margin, measure once) is this same discipline at authoring time; this section owns it for edits.

## Method — chars <-> tokens

Budgets are in **chars** (ADR 0008): a char count can't be gamed by long lines, and needs no API
call to check in CI. The token column is a convenience estimate via the standard **~4 chars/token**
rule for English/markdown, cross-checked against **words x 1.33**; the two bracket each other within
~25%, and dense markdown (backticks, slashes, symbols) sits nearer the chars / 4 end. Page anchor:
**~3,000 chars ~= 1 page ~= ~750 tokens**.

The real ratio is **model-specific**; the authoritative count is the `count_tokens` API (never
`tiktoken` — it under-counts Claude tokens). Those counts were **not run** when this table was
written (no API credentials in the env), so treat `~tok` as an order-of-magnitude anchor, not a
measured value.

## Extending the budget — evaluation

- **The named-doc self-budget is enforced** from the `char-budget.mjs` SSoT (`char-budget.test.mjs`
  reads the `DOC_BUDGETS` map and asserts each file's char length; `adr-lint.mjs` runs
  `oversizeDocs()` at the gate) — same poka-yoke as the ADR check ("compute the verdict, never
  assert it"). The next lean is a red/green test loop, not a blind char-count grind.
- **Source header comments — do NOT budget.** A header's failure mode is **drift** (it describes
  what the file *was*, names an absent construct, or lists imports), not length — a char cap would
  gate the wrong thing. A flat cap also misfits headers of legitimately varying complexity (a
  central module vs a one-line util). The existing rule — *update the header in the same change;
  extract logic -> narrow the parent's header; stale = drift* (CLAUDE.md, Docs) — already targets
  the real failure. Adding a cap here is muda.
- **STRATEGY / ROADMAP / README — not worth it.** README is small; ROADMAP length is legitimately
  variable (ladder + backlog); altitude discipline (one home, reference don't restate) already
  bounds them. A cap would risk forcing premature cuts.
