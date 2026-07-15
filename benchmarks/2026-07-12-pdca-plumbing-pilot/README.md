# ADR 0052 plumbing pilot — 2026-07-12 (issue #172, gates both instruments)

Proves the ADR 0052 weakest assumption before either grid spends: the hermetic driver
(`../lib/hermetic_driver.py`) can run a **skill+agent arm** at all — the deny-list conflict
must be shown HIT and RESOLVED with isolation preserved, and a cell priced. Not a
measurement: seeds here are a signal sanity check, drawn from the Instrument 1 taxonomy but
NOT from its pre-registered per-substrate assignments; the decide scenario is a throwaway,
not one of Instrument 2's 8. Substrate is regenerable (`build_substrate.py`, gitignored);
`outputs/` is the committed record.

## Design (3 cells, sonnet, run via `pilot.py`)

1. **retro-conflict** — the retrospect task under the FULL deny list. Expected: the agent
   cannot ground a finding (conflict HIT — this is the baseline that shows the carve-out is
   load-bearing, not decorative).
2. **retro-carveout** — same task, `allow=(Read,Grep,Glob,Bash)` (exactly the retrospect
   agent's declared tools) + the agent's system prompt via `--append-system-prompt`, cwd =
   the seeded substrate repo. Expected: grounds the two planted defects
   (gate-piped-filter in `scripts/ci.sh`, backstory-drift in `README.md`) with cites.
3. **decide-spawn** — a mini decision panel in a scenario dir carrying two project agents
   (`.claude/agents/`), `allow=(Task,Agent,Read,Grep,Glob,Bash)`. The task-list tools
   (`TaskCreate`..`TaskUpdate`, `TaskList`...) **stay denied** — that is the issue-#108 leak
   surface the driver's deny list exists for; the carve-out never opens it. Expected: both
   subagents spawn and return; parent-session task state unchanged (before/after snapshot
   taken outside the harness).

Carve-out mechanics: `hermetic_driver.do_call(..., allow=, extra_args=)` — added for this
pilot (allow names are validated against the deny list; unknown names raise). Models: sonnet
everywhere — faithful for the retrospect tier (ADR 0006); Instrument 2's opus panel tiers are
priced by its own cost-pilot on scenario B1, not here.

## Results (run 2026-07-12, records in `outputs/`)

**ADR 0052's weakest assumption: VERIFIED.** All three cells completed, no errors, no retries.

1. **retro-conflict** ($0.729): conflict HIT, witnessed in the output — "I couldn't pull
   exact commit SHAs or line numbers this turn since Bash/Read/Grep/git were all disabled".
   Nuance for arm design: `claude -p` auto-loads the cwd's CLAUDE.md into context (no tool
   needed), so even the fully-denied cell named both defect CLASSES from CLAUDE.md rules +
   friction text — ungrounded (zero cites). Both I1 arms get identical tool access, so this
   context symmetry holds in the grid; grounding is what the found-iff predicates score.
2. **retro-carveout** ($0.375): conflict RESOLVED — both seeds found and grounded (2/2
   recall, commit SHAs + file:line + friction cross-check), zero false positives (explicitly
   cleared the innocuous `docs/guide.md` edit), and the no-session-log case handled honestly
   ("N/A here — nothing to inspect").
3. **decide-spawn** ($0.430): both project subagents spawned and returned ("Subagents
   spawned: `advisor`, `pm`"), full decision record with weakest assumption + revisit
   trigger. Isolation preserved: the parent session's task dir gained only the
   orchestrator's own harness files; ALL nested state (session jsonl + the two subagent
   transcripts) landed inside the pinned `CLAUDE_CONFIG_DIR` — the `TaskCreate`..`TaskUpdate`
   deny held (issue-#108 leak surface never opened).

**Cost gate (first live firing — it works):** projected I1 grid
`48 x $0.375 = $18.02 > $15` ceiling (and $26.50 on the conservative both-cells mean) —
`cost_gate.py` exits 1, grid HALTED per the pre-registered rule. The ceiling (a pre-reg
guess: "3-5x the analog arm cost") was too tight, and the real substrates (10-20 commits vs
this 6-commit smoke repo) will only cost more. Routed to the pre-registered fresh `/decide`:
raise the ceiling vs trim the design.
