#!/usr/bin/env python3
"""I2 cost-pilot (ADR 0052 decision 3; pre-registration: README.md — frozen).

Runs arm-C cells on scenario B1 only, one at a time, hard-capped at $6 total (the ADR's
pilot cap): each cell is the full /decide arm — pdca-workflow loaded via --plugin-dir,
subagent spawning allowed, task-list tools still denied (the pilot-proven carve-out).
After each cell, prints running total and stops before exceeding the cap. Outputs to
pilot-outputs/<n>.json (committed — the pilot record). The measured per-cell costs then
feed: python3 ../lib/cost_gate.py --cells 72 --pilot-cost-usd <these> --ceiling-usd 40.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
from hermetic_driver import build_env, do_call, summarize_call  # noqa: E402

REPO = HERE.parents[1]
SNAP = HERE / "scenario-b1" / "snapshot"
OUT = HERE / "pilot-outputs"
CAP_USD = 6.0
MAX_CELLS = 3
ALLOW = ("Skill", "Task", "Agent", "Read", "Grep", "Glob", "Bash", "Write", "Edit")

PROMPT = """Read ISSUE-41.md at the repository root — it poses a judgment call for this project (adopt tiered-agent execution for the plugin's Do phase?) with an owner-drafted test plan.

Run /decide on this call: decide whether and how to proceed, following the skill's full process, and record the decision with rationale. When the process completes, output the final decision record text in your reply."""


def main():
    if not SNAP.exists():
        sys.exit("run build_b1.py first")
    OUT.mkdir(exist_ok=True)
    env = build_env()
    spent = 0.0
    for n in range(1, MAX_CELLS + 1):
        path = OUT / f"b1-C-r{n}.json"
        if path.exists():
            prior = json.loads(path.read_text())["summary"].get("cost_usd") or 0.0
            spent += prior
            print(f"[b1-C-r{n}] exists (${prior}), skipped; spent={spent:.2f}")
            continue
        # bypassPermissions: nested -p sessions deny writes by default (pilot r3 could not
        # write its ADR); the deny-list is a hard block regardless of permission mode, so
        # hermeticity is unchanged.
        call = do_call(PROMPT, "sonnet", env, str(SNAP), timeout=2400, allow=ALLOW,
                       extra_args=("--plugin-dir", str(REPO / "pdca-workflow"),
                                   "--permission-mode", "acceptEdits"))
        record = {"cell": f"b1-C-r{n}", "arm": "C", "allow": list(ALLOW),
                  "summary": summarize_call(call), "response": call["response"]}
        path.write_text(json.dumps(record, indent=1), encoding="utf-8")
        cost = record["summary"].get("cost_usd") or 0.0
        spent += cost
        print(f"[b1-C-r{n}] cost={cost} spent={spent:.2f} err={record['summary']['error']}")
        if spent + cost > CAP_USD:  # next cell at this rate would break the cap
            print(f"stopping: next cell at ~${cost:.2f} would exceed the ${CAP_USD} pilot cap")
            break
    print(f"pilot done: ${spent:.2f} across {n} cell(s)")


if __name__ == "__main__":
    main()
