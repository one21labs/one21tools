# Handoff

Written 23-Nov-2026. Rewrite this file whole when the state changes; do not append to it. Where
it disagrees with git or the issue tracker, they are right.

## State

On 23-Nov-2026 the repo was cut from about 211 KB of shipped guidance, plus hooks, agents,
scripts and a decision log, to four skills of about 13 KB in total. The reason was the repo's own
benchmarks; the README's last section gives the numbers. The last commit with everything in it
is `0a1834d`.

The benchmark write-ups moved to `one21labs/skill-measure` under `evidence/`. The raw run output
(about 22 MB) was not moved: it stays in this repo's history at `0a1834d`, under `benchmarks/`.

## Not yet measured

- `engineering-principles` was rewritten to four rules. Its cases in `evals/evals.json` still
  apply, but the rewrite has not been run against the bare model.
- `fresh-check` is new and has no cases at all.
- `advise` was measured only as part of the old decision panel.
- None of the four has been run in the desktop app.
- No skill has beaten the bare model on cases written without the skill in view. The October
  attempt to write such cases mostly produced cases the bare model already passed.

Measuring needs the `claude` command-line program signed in with a token the owner creates
(`claude setup-token`), then `/bench` from skill-measure.

## Open with the owner

- `building-skills` was removed although it measured a gain on its own cases (+0.30 and +0.32
  on the current models). The reason was overlap with Anthropic's skill-creator, not the
  numbers. It is the one cut worth a second look; it restores from `0a1834d`.
- The plugin name `pdca-workflow` no longer describes two second-opinion skills. Renaming breaks
  existing installs unless the marketplace `renames` map carries the old name across, which has
  only been verified for a removal. Kept as is until the owner decides.
- Whether `dev-skills` and `engineering-skills`, one skill each, should become one plugin. Same
  rename cost.
- The scheduled task "one21tools self-improvement loop" is switched off and its prompt points at
  a command file that no longer exists. Delete it or have it rewritten.
- Open issues and pull request #337 were written against the old shape. Most are now moot and
  need closing or re-reading.
