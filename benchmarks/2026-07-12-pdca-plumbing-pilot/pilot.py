#!/usr/bin/env python3
"""ADR 0052 decision 2: the shared plumbing pilot. Proves the hermetic driver can run a
skill+agent arm at all before either Instrument's grid spends (issue #172).

Three cells, written to outputs/ (committed — the pilot record IS the artifact, ADR 0052):
  1. retro-conflict:  retrospect cell under the FULL deny list — expected to show the
     deny-list conflict HIT (agent cannot ground a single finding).
  2. retro-carveout:  same cell with allow=(Read,Grep,Glob,Bash) + the retrospect agent
     system prompt — expected to ground the seeded defects (conflict RESOLVED).
  3. decide-spawn:    mini /decide flow with allow Task/Agent (+R/G/G/B) and project agents
     in the scenario dir — proves subagent spawning under the pinned config while every
     task-list tool (TaskCreate..TaskUpdate) STAYS denied (the issue-#108 leak surface).

Isolation evidence for cell 3 is gathered outside this script (parent-session task dir
snapshot before/after) and recorded in the README. Models: sonnet everywhere — faithful for
the retrospect tier (ADR 0006); the decide panel's opus tiers are priced later by the I2
cost-pilot on scenario B1, not here.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
from hermetic_driver import build_env, do_call, summarize_call  # noqa: E402

REPO_ROOT = HERE.parents[1]
SUB = HERE / "substrate"
OUT = HERE / "outputs"

RETRO_AGENT_SP = (REPO_ROOT / "pdca-workflow" / "agents" / "retrospect.md").read_text(
    encoding="utf-8").split("---", 2)[2].strip()

RETRO_PROMPT = """Git range: origin/main...HEAD in this repository (the current working directory).

Session friction from the orchestrator (my perception; cross-check the git-visible ones) —
also written at friction.md:
1. CI showed green while docs validation had actually failed once; had to rerun the gate by
   hand to see the failure. (git-visible: yes)
2. A reviewer asked what the README History section was for. (git-visible: yes)

Analyze per your method and output your findings."""

BARE_RETRO_PROMPT = RETRO_PROMPT + """

You are reviewing this session for process problems. Report each problem with its evidence
(commit or file:line)."""

DECIDE_PROMPT = """Run a decision panel on the judgment call in question.md (read it first):
1. Spawn the project agent named `advisor` (point it at question.md) and collect its
   recommendation.
2. Spawn the project agent named `pm`, hand it the advisor's recommendation verbatim, and
   collect its decision record.
3. Output: the advisor's recommendation, then the pm's decision record, then one line naming
   which subagents you spawned."""


def run_cell(name, prompt, cwd, allow=(), extra_args=(), timeout=600):
    env = build_env()
    call = do_call(prompt, "sonnet", env, str(cwd), timeout=timeout,
                   allow=allow, extra_args=extra_args)
    record = {"cell": name, "allow": list(allow),
              "summary": summarize_call(call), "response": call["response"]}
    (OUT / f"{name}.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
    cost = (record["summary"] or {}).get("cost_usd")
    print(f"[{name}] cost={cost} error={record['summary']['error']}")
    return record


def main():
    if not SUB.exists():
        subprocess.run([sys.executable, str(HERE / "build_substrate.py")], check=True)
    OUT.mkdir(exist_ok=True)
    repo = SUB / "repo"
    scenario = SUB / "decide-scenario"

    run_cell("retro-conflict", BARE_RETRO_PROMPT, repo)
    run_cell("retro-carveout", RETRO_PROMPT, repo,
             allow=("Read", "Grep", "Glob", "Bash"),
             extra_args=("--append-system-prompt", RETRO_AGENT_SP))
    run_cell("decide-spawn", DECIDE_PROMPT, scenario,
             allow=("Task", "Agent", "Read", "Grep", "Glob", "Bash"), timeout=900)


if __name__ == "__main__":
    main()
