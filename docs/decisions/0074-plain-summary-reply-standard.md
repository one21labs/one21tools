---
id: 0074
title: "Reply standard: 15-30s highlights lead, brief detail follows, expand on request"
status: accepted
tier: lite
summary: "Owner directives (17-Jul + 18-Jul, quoted): the plain ~100-word summary (cap 350) LEADS the reply as a 15-30-second highlights block — what happened, what it's worth, what's waiting on the reader — then a brief detail layer; deeper explanation only on request. Shipped as an output style: .claude/output-styles/plain-summary.md (dogfooded) + pdca-workflow/templates/plain-summary.md (/pdca-init)."
---

# 0074 — layered plain-language replies

- Decision: every substantive reply OPENS with a highlights block readable in 15-30s (3-5
  plain bullets or ~100 words, cap 350 — outcome first, value in reader terms, deviations +
  what's waiting on the reader), then a brief detail layer; anything deeper waits for the
  reader to ask. The style file is the SSoT for the rules.
- Why: owner-directed twice, quoted — 17-Jul (one plain summary, ~100 words) and 18-Jul ("the
  highlights in 15-30s, then maybe a bit more detail, and I'll ask to expand"): a compliant
  closing summary still fails when the reader must scroll past the detail to reach it — budget
  the reader's first half-minute, not just the word count.
- Enforced: `.claude/output-styles/plain-summary.md` (this repo, `outputStyle` in
  .claude/settings.json) and `pdca-workflow/templates/plain-summary.md` (consumers, /pdca-init
  step 5). Convention, not a gate — no linter counts reply words.
