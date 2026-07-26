---
id: 0038
title: "Operational rules live in shipped files, not repo-only surfaces"
status: accepted
tier: lite
summary: "The shipped-home routing constraint (owner-stated, #93): a rule a skill/plugin applies in operation lives in a file that ships and loads with it (SKILL.md, references/, plugin agents/hooks/scripts, validate.py, vendored adr-lint.mjs); repo-level surfaces (CLAUDE.md, docs/decisions/, .github/) are dogfood-instance config a consumer never loads — they may point at the shipped home, never solely house it."
---

# 0038 — operational rules live in shipped files, not repo-only surfaces

- Decision: an operational rule a skill/plugin enforces lives in a SHIPPED file (SKILL.md,
  `references/`, plugin `agents/`/`hooks/`/`scripts/`, `validate.py`, vendored `adr-lint.mjs`);
  repo-level surfaces may point at the shipped home, never solely house it. Operationalized in
  its own shipped home: a shipping-boundary row in `jit-documentation.md`'s Decision Test —
  "must the rule travel with the skill/plugin when installed elsewhere? -> a shipped file; repo
  docs may point, never solely house." Governs home-selection in ADRs 0039-0042.
- Why: `jit-documentation.md`'s Decision Test routed placement by scope only, with no
  install-portability axis, so operational rules silently landed in repo-only homes (mis-routed
  in earlier #93 drafts). Housing the constraint once, as a Decision-Test row, prevents the
  recurring mis-route that needed owner correction.
- Rejected: house it in this repo's CLAUDE.md — violates the constraint itself (repo-only,
  doesn't ship); CLAUDE.md may carry a pointer. Leave it implicit in #93 — the mis-route had
  already recurred once.
- Reopen-if: a new operational rule lands in a repo-only home despite the Decision-Test row ->
  the wording is insufficient; strengthen it or add a validate.py check.
- Enforced: `skills/engineering-principles/references/jit-documentation.md` Decision Test
  (shipping-boundary row).
