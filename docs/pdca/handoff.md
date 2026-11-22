# Handoff

Written 21-Nov-2026 on `claude/brave-pasteur-4ho96t` (PR #339), on top of `10c581a`. Rewrite this
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
| `CLAUDE.md` chars against its 6,000 cap | 5,637 | 5,772 | headroom of 300 |

How to read them: verdicts from the README "Measured state" table; cites with
`grep -rnE 'ADRs? [0-9]{4}|#[0-9]{2,3}\b'` over `skills/*/SKILL.md`, `skills/*/references`,
`pdca-workflow/{skills,agents,commands}`; guidance bytes with `wc -c` over the same set; gate
bytes over `scripts/*.mjs`, `pdca-workflow/{scripts,hooks}`, `.claude/hooks`, `validate*.py`,
`gates.yml`; the total with `git ls-files -- . ':!benchmarks'`. Bytes last read at `e14e3ca`.

## Shipped this turn

PR #339: the cut pass, the desktop pass, then this repo's advisory review workflow removed
(owner, 21-Nov: "Remove the broken review"; its token was revoked, so it reviewed nothing). The
template `/pdca-init` offers stays. Sibling PR `one21labs/skill-measure#12`: `/bench` reads this
repo's `evals/evals.json`, refuses by name when `claude` is missing, imports on Python 3.9.

How the two repos were checked together (repeat after either changes): install all four plugins
into a scratch `CLAUDE_CONFIG_DIR` whose path has a space, start `claude -p` with
`--output-format stream-json --verbose`, read the `init` event; spawn a helper with no model and
confirm `docs/pdca/gate-hits.txt` gains a line; load each `skills/*/evals/evals.json` through
skill-measure's `bench_skill.load_evals`; run `validate.py` over skill-measure's `skills/bench`.

## Scheduled (owner, 21-Nov: "schedule the remaining work and merge for after the Sunday reset")

After the weekly limit resets (Sun 22-Nov 18:00 UTC): merge skill-measure#12 and #339 if still
green, then take the candidates below in a new PR.

## Next candidates, ranked

1. **`optimizing-context` ships 54 KB with no verdict**; `building-skills` is unsettled. Measure
   (needs the owner's token) or cut.
2. **The review template is no longer run anywhere we can see.** `templates/claude-review.yml`
   ships to adopters; nothing here exercises it now. Keep only if someone runs it.
3. **Five decision records describe the harness that left** (0019, 0023, 0041, 0096, 0097).

Also true, unranked: the guards are bash, so Windows needs Git for Windows (a node rewrite
removes that); `validate.py` runs on Python 3.9 but no check holds it there; #337 needs a
rebase after the merge, and `control-narratives` returns only if its re-measure beats bare.

## Waiting on the owner

- Turn `pdca-workflow` on for the account, then try `/pdca-workflow:decide` and `/bench` once in
  the desktop Code tab and once in Cowork. Nobody has run either plugin in the app itself.
- `claude setup-token`, for the #328 re-measure and candidate 1.
- The scheduled task "one21tools self-improvement loop" is OFF: attach this repository to it
  with push access, then turn it on.
- Decide: ADR 0024 against the sunk-cost ruling; where frozen benchmark evidence lives (22 MB);
  #338 item 3; whether the 90% pause rule also covers the weekly limit.
