# one21tools

A Claude Code plugin marketplace with four small skills. There is no app and nothing to build:
the product is the text in the `SKILL.md` files, so the care goes into that text.

## Layout

- `.claude-plugin/marketplace.json` lists the three plugins. A broken entry breaks installs for
  everyone, so after any edit check that it still parses and that every path in it exists.
- `skills/code-standards/` and `skills/engineering-principles/` are the two skills served through
  the `dev-skills` and `engineering-skills` plugins.
- `pdca-workflow/` is a plugin with its own `plugin.json` and two skills, `advise` and
  `fresh-check`.
- `scripts/validate.py` is this repo's CI check for skill files. It is not shipped.
- `docs/handoff.md` is a short note for the next session: what git cannot tell it.

Plugin names are an interface people install by. Do not rename or remove one without asking the
owner.

## Changing a skill

Write for a capable reader who has none of your context. Say what to do in a specific situation
and why. The measurements behind this repo found that short situational rules change what the
model does, and that definitions, doctrine and emphasis do not.

Before adding anything, ask whether the model already does it unprompted. If it does, the text
costs context on every load and buys nothing.

A claim in the README about what a skill does needs a measurement behind it, or the words "not
measured". The harness is the `skill-measure` plugin (`/bench`); the past write-ups are in that
repo under `evidence/`. A skill that claims to make the work better stays only if it beats
the bare model on cases written without the skill in view. A skill that carries a preference the
model cannot know, such as a house style, has to show only that the preference gets applied.
What a skill cost to build is not a reason to keep it.

## Checks

```
python3 scripts/validate.py <skill directory>
cd scripts && python3 -m unittest discover -p "*_test.py"
node --test scripts/*.test.mjs
```

Run these before pushing. CI runs the same three, plus a parse of both manifests.

## Shipping

Work on a branch and open a pull request; merging is the owner's call. Say in the pull request
what was tested and what was not. Text written by Claude in a pull request or issue says so.

Do not file or edit issues, pull requests or comments in a repository outside `one21labs`
without the owner approving the exact text first.

In a long session, at 90% of the 5-hour usage window, schedule a resume for after the reset and
stop.
