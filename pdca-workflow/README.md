# pdca-workflow

Two second-opinion skills. Both work by starting fresh subagents that have not seen your
reasoning, because that independence is what they are for.

| Skill | When | What it does |
|---|---|---|
| `/advise` | Before a contested decision | You state your own pick, two independent advisors argue opposing sides, and you report what they changed. |
| `/fresh-check` | Before work ships | A reviewer with no stake reproduces each claim against the real code and output, then tries to break the work. |

Neither is for routine calls. Each costs one or two extra agents, and the evidence for `/advise`
is that it helps you see how a decision could fail, not that it picks better options. The
numbers are in the repository README.

```
/plugin install pdca-workflow@one21tools
/advise should we merge these two services or keep them separate?
/fresh-check the retry fix in src/queue.py
```

The plugin has no hooks, agents or scripts, and needs no project setup.

Until 23-Nov-2026 this plugin was a full decide, build, verify, improve workflow. The repository
README says what was removed and why. The name is from that workflow and no longer describes
the contents; it is kept so that existing installs keep working.
