# Advisor panel — one21tools

This repo's own tuned advisor panel (dogfooding pdca-workflow). NOT a shipped standard — a
consumer generates their own via `/pdca-init` (why: `panel-generation.md`). Selection: the
`advise` skill; definitions: `.claude/agents/*.md`.

| Advisor | Why this repo needs it |
|---|---|
| lean-process-engineer | the repo's core discipline is cutting muda and preventing over detecting |
| process-economist | process machinery and evals carry real token cost to weigh |
| plugin-adopter | changes must not break or mislead downstream adopters |
| session-operator | rules must survive a real Claude Code session, not just read well |

Ownership: PM. Membership changes go through `/decide` and are recorded on the deciding ADR's
`Panel:` line; git history is the SSoT for what changed.
