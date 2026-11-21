# Handoff

Written 21-Nov-2026 on `claude/brave-pasteur-4ho96t` (PR #339), on top of `b540286`. Rewrite this
file whole each turn (`pdca-workflow/commands/improve.md`). Where it disagrees with git or the
tracker, they win.

Goal (`README.md`): quality output, autonomously, judged as the person receiving it.

## Measures

| Measure | Baseline `d4bcbc2` | Last | Now | Target |
|---|---|---|---|---|
| Shipped skills with a promoted "helps" verdict | 1 of 5 | 1 of 5 | 1 of 4 | all, none below bare |
| Known user-facing defects on `main` once #339 merges | 4 | 1 | 0 | 0 |
| Internal record or issue numbers in shipped, model-loaded text | 37 | 0 | 0 | 0 |
| Shipped guidance, bytes | 218,629 | 222,384 | 210,936 | below baseline |
| Gate and hook code with tests, bytes | 344,073 | 345,621 | 312,667 | below baseline |
| Everything outside `benchmarks/`, bytes | 926,255 | 922,421 | 817,020 | falling |
| `CLAUDE.md` chars against its 6,000 cap | 5,637 | 5,998 | 5,782 | headroom of 300 |

How to read them: verdicts from the README "Measured state" table; cites with
`grep -rnE 'ADRs? [0-9]{4}|#[0-9]{2,3}\b'` over `skills/*/SKILL.md`, `skills/*/references`,
`pdca-workflow/{skills,agents,commands}`; guidance bytes with `wc -c` over the same set; gate
bytes over `scripts/*.mjs`, `pdca-workflow/{scripts,hooks}`, `.claude/hooks`, `validate*.py`,
`gates.yml`; the total with `git ls-files -- . ':!benchmarks'`.

## Shipped this turn

PR #339, second pass (owner, 21-Nov: "Be ruthless. All code is sunk cost."): the
`control-narratives` skill removed (it scored below the bare model); two gates deleted with the
records and the research corpus they guarded; the analytics spec nothing implemented; old sweep
logs; the loop command cut to a wrapper around `/pdca-workflow:MSH`; `CLAUDE.md` trimmed.

## Next candidates, ranked

1. **The advisory review has not posted on #339.** Run 44874369631 ended after one turn at no
   cost; run 44874897554 finished green and the PR still has no review comment. A guard that
   does not fire: read that run's `claude-review-execution-log` artifact for the denied or
   missing `gh pr comment`.
2. **`optimizing-context` ships 54 KB with no verdict** (two inconclusive diagnostic pairs,
   `benchmarks/2026-10-12-g8-shortfall/`), and `building-skills` is unsettled. Measure them, or
   cut `optimizing-context` to the references a measurement supports. Needs the owner's token.
3. **Five decision records describe a harness that now lives in `one21labs/skill-measure`**
   (0019, 0023, 0041, 0096, 0097). Confirm that repo holds each rule, then retire them to
   forward entries.

Also true, unranked: `dev-skills` and `engineering-skills` each copy every skill folder and its
`evals/` to disk (`source: ./skills`) — disk only, nothing a model loads; about 100 comments in
hooks and scripts still cite internal records; `.claude/hooks/pr-create-guard.sh` guards
`gh pr create`, which a cloud session never runs.

## Waiting on the owner

- Merge #339. #337 then needs a rebase: it carries the `control-narratives` revision, which
  should return to the marketplace only if its re-measure beats the bare model (#328).
- Turn `pdca-workflow` on for the account (desktop app: Customize, Plugins). Until then no
  cloud session loads it, and nobody has confirmed its agents and guards load there.
- `claude setup-token`, for the #328 re-measure and candidate 2.
- The scheduled task "one21tools self-improvement loop" (daily 10:41 UTC) is turned OFF: a test
  firing got 403 on this repo. Attach `one21labs/one21tools` with push access to it in the
  scheduled-tasks settings, then turn it on.
- Decide: ADR 0024 says cut only after benefit-per-token plateaus; the sunk-cost ruling now in
  `CLAUDE.md` cuts sooner — amend or retire 0024. Where frozen benchmark evidence lives (22 MB,
  cloned by every install). Whether guards are copied into adopting repos (#338 item 3).
  Whether the 90% pause rule also covers the weekly limit.
