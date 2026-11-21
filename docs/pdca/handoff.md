# Handoff

Written 21-Nov-2026 on `claude/brave-pasteur-4ho96t` (PR #339), on top of `6027267`. Rewrite this
file whole each turn (`pdca-workflow/commands/improve.md`). Where it disagrees with git or the
tracker, they win.

Goal (`README.md`): quality output, autonomously, judged as the person receiving it.

## Measures

| Measure | Baseline `d4bcbc2` | Now | Target |
|---|---|---|---|
| Shipped skills with a promoted "helps" verdict | 1 of 5 | 1 of 4 | all, none below bare |
| Known user-facing defects on `main` once #339 merges | 4 | 0 | 0 |
| Internal record or issue numbers in shipped, model-loaded text | 37 | 0 | 0 |
| Shipped guidance, bytes | 218,629 | 210,936 | below baseline |
| Gate and hook code with tests, bytes | 344,073 | 312,652 | below baseline |
| Everything outside `benchmarks/`, bytes | 926,255 | 817,789 | falling |
| `CLAUDE.md` chars against its 6,000 cap | 5,637 | 5,782 | headroom of 300 |

How to read them: verdicts from the README "Measured state" table; cites with
`grep -rnE 'ADRs? [0-9]{4}|#[0-9]{2,3}\b'` over `skills/*/SKILL.md`, `skills/*/references`,
`pdca-workflow/{skills,agents,commands}`; guidance bytes with `wc -c` over the same set; gate
bytes over `scripts/*.mjs`, `pdca-workflow/{scripts,hooks}`, `.claude/hooks`, `validate*.py`,
`gates.yml`; the total with `git ls-files -- . ':!benchmarks'`.

## Shipped this turn

PR #339: the cut pass (owner, 21-Nov: "Be ruthless. All code is sunk cost."), then the desktop
pass. Desktop facts and what was run are in the README "What loads where" table. The sibling
repo has its own PR on the same branch name in `one21labs/skill-measure`: `/bench` reads this
repo's `evals/evals.json`, refuses by name when the `claude` program is missing, and imports on
the Python a Mac ships.

How the two repos were checked together (repeat after either changes): install all four plugins
into a scratch `CLAUDE_CONFIG_DIR` whose path has a space, start `claude -p` with
`--output-format stream-json --verbose`, read the `init` event for the loaded skills, commands
and agents; spawn a helper with no model and confirm `docs/pdca/gate-hits.txt` gains a line;
load each `skills/*/evals/evals.json` through skill-measure's `bench_skill.load_evals`; run
`validate.py` over skill-measure's `skills/bench`.

## Next candidates, ranked

1. **The advisory review has not posted on #339.** Each run ends in 2 seconds at zero cost:
   a bad token or a limit. Its warning step now prints the reason in the job log; read it.
2. **Nobody has run either plugin in the desktop app itself.** The Code tab shares the engine
   that was run here; Cowork's sandbox is undocumented (is `python3`, `node`, `claude` there?).
   One manual pass by the owner closes it.
3. **`optimizing-context` ships 54 KB with no verdict**; `building-skills` is unsettled. Measure
   or cut. Needs the owner's token.

Also true, unranked: five decision records describe the harness that left (0019, 0023, 0041,
0096, 0097); the guards are bash, so Windows needs Git for Windows — a node rewrite would
remove that; `validate.py` runs on Python 3.9 today but no check holds it there.

## Waiting on the owner

- Merge #339 and the skill-measure PR. #337 then needs a rebase: it carries the
  `control-narratives` revision, which should return only if its re-measure beats bare (#328).
- Turn `pdca-workflow` on for the account (desktop app: Customize, Plugins), then try
  `/pdca-workflow:decide` and `/bench` once in the Code tab and once in Cowork.
- `claude setup-token`, for the #328 re-measure and candidate 3.
- The scheduled task "one21tools self-improvement loop" is OFF: attach this repository to it
  with push access, then turn it on.
- Decide: ADR 0024 (cut only after a plateau) against the sunk-cost ruling in `CLAUDE.md`;
  where frozen benchmark evidence lives (22 MB, cloned by every install); #338 item 3; whether
  the 90% pause rule also covers the weekly limit.
