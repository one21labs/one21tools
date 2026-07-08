# Advisor panel — one21tools

This repo's own tuned advisor panel (dogfooding pdca-workflow; adopted in ADR 0023). It is NOT a
shipped standard — a consumer generates their own via `/pdca-init` (a borrowed panel gives
confident-but-irrelevant advice). The `advise` skill picks the 2-3 lenses a call needs; the
definitions live in `.claude/agents/*.md`, tracked via the `.claude/* + !.claude/agents/` negation
(ADR 0004).

| Advisor | Lens | Why this repo needs it |
|---|---|---|
| lean-process-engineer | waste vs poka-yoke | the repo's core discipline is cutting muda and preventing over detecting |
| process-economist | cost-per-decision / AI spend | process machinery and evals carry real token cost to weigh |
| plugin-adopter | a solo dev adopting the plugin in a second repo | changes must not break or mislead downstream adopters |
| session-operator | live-session execution realism | rules must survive a real Claude Code session, not just read well |

Ownership: PM. Membership changes go through `/decide` and are recorded on the deciding ADR's
`Panel:` line; git history is the SSoT for what changed. Each file here has frontmatter `name:`
matching its filename (adr-lint agent guard).
